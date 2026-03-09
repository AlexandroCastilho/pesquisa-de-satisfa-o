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
    nova_empresa = models.Empresa(**empresa.dict())
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
        # Monta o visual do e-mail
        corpo_html = f"""
        <div style='font-family: Arial; padding: 20px; text-align: center; background: #f4f4f9;'>
            <h2>Olá! Gostaríamos de ouvir você.</h2>
            <p>Por favor, avalie nosso serviço clicando no botão abaixo:</p>
            <a href='{link}' style='display: inline-block; padding: 10px 20px; background: #4f46e5; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;'>Avaliar Agora</a>
        </div>
        """
        msg = MIMEText(corpo_html, 'html')
        msg['Subject'] = assunto
        msg['From'] = user
        msg['To'] = destinatario

        # Conecta no servidor (Porta 587 é padrão para segurança TLS)
        server = smtplib.SMTP(host, 587)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, destinatario, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Erro ao enviar para {destinatario}: {e}")

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