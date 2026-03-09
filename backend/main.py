import smtplib
from email.mime.text import MIMEText
from fastapi import BackgroundTasks
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
import pandas as pd
import io


import models, schemas
from database import engine, get_db

# Cria as tabelas no banco de dados automaticamente
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SaaS Pesquisa de Satisfação API")

# Permite que o Frontend converse com o Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"mensagem": "API do SaaS rodando com sucesso!"}

@app.post("/empresas/", response_model=schemas.EmpresaResponse)
def criar_empresa(empresa: schemas.EmpresaCreate, db: Session = Depends(get_db)):
    nova_empresa = models.Empresa(empresa.model_dump())
    db.add(nova_empresa)
    db.commit()
    db.refresh(nova_empresa)
    return nova_empresa

@app.post("/clientes/importar/{empresa_id}")
async def importar_clientes_csv(empresa_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="O arquivo deve ser um .csv")
    
    # Lendo o CSV com Pandas na memória
    conteudo = await file.read()
    df = pd.read_csv(io.BytesIO(conteudo))
    
    clientes_salvos = 0
    # Iterando pelas linhas do CSV (espera-se colunas: nome, email, telefone)
    for index, row in df.iterrows():
        novo_cliente = models.Cliente(
            empresa_id=empresa_id,
            nome=row.get('nome'),
            email=row.get('email'),
            telefone=row.get('telefone')
        )
        db.add(novo_cliente)
        clientes_salvos += 1
        
    db.commit()
    return {"mensagem": f"{clientes_salvos} clientes importados com sucesso para a empresa {empresa_id}!"}  

@app.post("/pesquisas/", response_model=schemas.PesquisaResponse)
def criar_pesquisa(pesquisa: schemas.PesquisaCreate, db: Session = Depends(get_db)):
    nova_pesquisa = models.Pesquisa(**pesquisa.model_dump())
    db.add(nova_pesquisa)
    db.commit()
    db.refresh(nova_pesquisa)
    return nova_pesquisa

@app.post("/respostas/")
def salvar_resposta(resposta: schemas.RespostaCreate, db: Session = Depends(get_db)):
    nova_resposta = models.Resposta(
        pesquisa_id=resposta.pesquisa_id,
        cliente_id=resposta.cliente_id,
        nota=resposta.nota
    )
    db.add(nova_resposta)
    db.commit()
    return {"mensagem": "Voto computado com sucesso!"}

@app.get("/estatisticas/{pesquisa_id}")
def obter_estatisticas(pesquisa_id: int, db: Session = Depends(get_db)):
    # Pede para o banco de dados calcular a média e contar os votos
    resultado = db.query(
        func.avg(models.Resposta.nota).label("media"),
        func.count(models.Resposta.id).label("total")
    ).filter(models.Resposta.pesquisa_id == pesquisa_id).first()

    # Arredonda a média para 1 casa decimal (ex: 4.5) ou retorna 0 se não tiver votos
    media = round(resultado.media, 1) if resultado.media else 0.0
    total = resultado.total if resultado.total else 0

    return {
        "pesquisa_id": pesquisa_id, 
        "media_estrelas": media, 
        "total_votos": total
    }   

def enviar_email_background(host, user, password, destinatario, assunto, link):
    try:
        # Aqui você pode trocar o link da imagem para o logo da Amafil ou Castilho's
        logo_url = "https://cdn-icons-png.flaticon.com/512/3144/3144456.png" 
        
        corpo_html = f"""
        <html>
            <body style="margin: 0; padding: 0; background-color: #f6f9fc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                    <tr>
                        <td align="center" style="padding: 40px 0;">
                            <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                                <tr>
                                    <td align="center" style="padding: 40px 0 20px 0; background-color: #4f46e5;">
                                        <img src="{logo_url}" alt="Logo" width="80" style="display: block;">
                                        <h1 style="color: #ffffff; margin-top: 10px; font-size: 24px;">Sua opinião vale muito!</h1>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 40px; text-align: center;">
                                        <p style="font-size: 18px; color: #475569; line-height: 1.6;">
                                            Olá! Ficamos felizes em ter você conosco. <br>
                                            Poderia dedicar 10 segundos para nos dizer o que achou do nosso atendimento?
                                        </p>
                                        <div style="margin-top: 30px;">
                                            <a href="{link}" style="background-color: #4f46e5; color: #ffffff; padding: 15px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">
                                                DAR MINHA NOTA ★★★★★
                                            </a>
                                        </div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px; background-color: #f8fafc; text-align: center; font-size: 12px; color: #94a3b8;">
                                        Este e-mail foi enviado automaticamente por Alexandro Castilho Pesquisas. <br>
                                        © 2026 Todos os direitos reservados.
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        msg = MIMEText(corpo_html, 'html')
        # ... (resto do código de envio continua igual)

@app.post("/pesquisas/{pesquisa_id}/disparar")
def disparar_emails(pesquisa_id: int, dados: schemas.DisparoCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    pesquisa = db.query(models.Pesquisa).filter(models.Pesquisa.id == pesquisa_id).first()
    empresa = db.query(models.Empresa).filter(models.Empresa.id == pesquisa.empresa_id).first()
    clientes = db.query(models.Cliente).filter(models.Cliente.empresa_id == empresa.id).all()

    count = 0
    for cliente in clientes:
        # Cria o link mágico único para aquele cliente
        link_unico = f"{dados.url_frontend}/votar.html?pesquisa={pesquisa.id}&cliente={cliente.id}"
        
        # Joga o envio para a fila de segundo plano
        background_tasks.add_task(
            enviar_email_background, 
            empresa.smtp_host, 
            empresa.smtp_user, 
            empresa.smtp_password, 
            cliente.email, 
            f"Pesquisa: {pesquisa.titulo}", 
            link_unico
        )
        count += 1
        
    return {"mensagem": f"Disparo iniciado para {count} clientes em segundo plano!"}

from auth import gerar_senha_hash, verificar_senha, criar_token_acesso

@app.post("/auth/registrar")
def registrar(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    # Verifica se o email já existe
    db_user = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    novo_user = models.Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=gerar_senha_hash(usuario.senha)
    )
    db.add(novo_user)
    db.commit()
    return {"mensagem": "Utilizador criado com sucesso!"}

@app.post("/auth/login")
def login(dados: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.email == dados.email).first()
    if not user or not verificar_senha(dados.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    token = criar_token_acesso({"sub": user.email, "id": user.id})
    return {"access_token": token, "token_type": "bearer", "user_nome": user.nome}