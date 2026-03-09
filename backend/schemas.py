from pydantic import BaseModel

class EmpresaCreate(BaseModel):
    nome_fantasia: str
    smtp_host: str
    smtp_user: str
    smtp_password: str

class EmpresaResponse(EmpresaCreate):
    id: int
    class Config:
        orm_mode = True

class PesquisaCreate(BaseModel):
    empresa_id: int
    titulo: str

class PesquisaResponse(PesquisaCreate):
    id: int
    class Config:
        from_attributes = True

class RespostaCreate(BaseModel):
    pesquisa_id: int
    cliente_id: int
    nota: int

class DisparoCreate(BaseModel):
    url_frontend: str