from pydantic import BaseModel, EmailStr
from typing import Optional

# Esquemas para Usuário
class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

# Esquemas para Empresa (Agora ligada ao email do usuário)
class EmpresaCreate(BaseModel):
    nome_fantasia: str
    smtp_host: str
    smtp_user: str
    smtp_password: str
    usuario_email: str # O email de quem está logado

class EmpresaResponse(EmpresaCreate):
    id: int
    class Config:
        from_attributes = True

# Esquemas para Pesquisa
class PesquisaCreate(BaseModel):
    empresa_id: int
    titulo: str

class PesquisaResponse(PesquisaCreate):
    id: int
    class Config:
        from_attributes = True

# Outros
class RespostaCreate(BaseModel):
    pesquisa_id: int
    cliente_id: int
    nota: int

class DisparoCreate(BaseModel):
    url_frontend: str