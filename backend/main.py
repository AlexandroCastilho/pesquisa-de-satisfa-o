from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend import models, schemas, auth
from backend.database import engine, get_db
import pandas as pd
import io

# Garante que as tabelas (Usuario, Empresa, etc.) existam no banco
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SaaS Pesquisa de Satisfação")

# --- RESOLUÇÃO DE ERROS DE CONEXÃO (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROTAS DE USUÁRIO (A MEMÓRIA DO SISTEMA) ---

@app.post("/auth/registrar")
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    
    novo_usuario = models.Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=auth.gerar_senha_hash(usuario.senha)
    )
    db.add(novo_usuario)
    db.commit()
    return {"mensagem": "Usuário criado com sucesso!"}

@app.post("/auth/login")
def login(dados: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.email == dados.email).first()
    if not user or not auth.verificar_senha(dados.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    
    # Retorna os dados para o app.js salvar no LocalStorage
    return {"nome": user.nome, "email": user.email}

# --- ROTAS DE EMPRESA (VINCULADAS AO DONO) ---

@app.post("/empresas/", response_model=schemas.EmpresaResponse)
def criar_empresa(empresa: schemas.EmpresaCreate, db: Session = Depends(get_db)):
    nova_empresa = models.Empresa(
        nome_fantasia=empresa.nome_fantasia,
        smtp_host=empresa.smtp_host,
        smtp_user=empresa.smtp_user,
        smtp_password=empresa.smtp_password,
        usuario_email=empresa.usuario_email
    )
    db.add(nova_empresa)
    db.commit()
    db.refresh(nova_empresa)
    return nova_empresa

# --- IMPORTAÇÃO DE CLIENTES (CSV DA AMAFIL/PIZZARIA) ---

@app.post("/clientes/importar/{empresa_id}")
async def importar_clientes(empresa_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        # Detecta se é vírgula ou ponto e vírgula
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')), sep=None, engine='python')
        
        for _, row in df.iterrows():
            novo_cliente = models.Cliente(
                empresa_id=empresa_id,
                nome=row['nome'],
                email=row['email'],
                telefone=str(row['telefone'])
            )
            db.add(novo_cliente)
        
        db.commit()
        return {"mensagem": f"{len(df)} clientes importados!"}
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Arquivo CSV vazio ou inválido.")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Coluna obrigatória faltando: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro no CSV: {str(e)}")

# --- PESQUISAS E ESTATÍSTICAS ---

@app.post("/pesquisas/", response_model=schemas.PesquisaResponse)
def criar_pesquisa(pesquisa: schemas.PesquisaCreate, db: Session = Depends(get_db)):
    nova_p = models.Pesquisa(empresa_id=pesquisa.empresa_id, titulo=pesquisa.titulo)
    db.add(nova_p)
    db.commit()
    db.refresh(nova_p)
    return nova_p

@app.get("/estatisticas/{pesquisa_id}")
def ver_estatisticas(pesquisa_id: int, db: Session = Depends(get_db)):
    votos = db.query(models.Resposta).filter(models.Resposta.pesquisa_id == pesquisa_id).all()
    if not votos:
        return {"total_votos": 0, "media_estrelas": 0}
    
    media = sum([v.nota for v in votos]) / len(votos)
    return {"total_votos": len(votos), "media_estrelas": round(media, 1)}