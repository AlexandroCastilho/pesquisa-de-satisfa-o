from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Configurações de segurança
SECRET_KEY = "sua_chave_secreta_super_segura" # Troque isso depois!
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def gerar_senha_hash(senha):
    return pwd_context.hash(senha)

def verificar_senha(senha_pura, senha_hash):
    return pwd_context.verify(senha_pura, senha_hash)

def criar_token_acesso(dados: dict):
    expira = datetime.utcnow() + timedelta(hours=24)
    dados.update({"exp": expira})
    return jwt.encode(dados, SECRET_KEY, algorithm=ALGORITHM)