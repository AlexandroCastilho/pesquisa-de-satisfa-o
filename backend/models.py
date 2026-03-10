from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from backend.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    email = Column(String, primary_key=True, index=True)
    nome = Column(String)
    senha_hash = Column(String)

class Empresa(Base):
    __tablename__ = "empresas"
    id = Column(Integer, primary_key=True, index=True)
    usuario_email = Column(String, ForeignKey("usuarios.email"))
    nome_fantasia = Column(String, index=True)
    smtp_host = Column(String)
    smtp_user = Column(String)
    smtp_password = Column(String)
    
class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    nome = Column(String)
    email = Column(String)
    telefone = Column(String)

class Pesquisa(Base):
    __tablename__ = "pesquisas"
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    titulo = Column(String)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())

class Resposta(Base):
    __tablename__ = "respostas"
    id = Column(Integer, primary_key=True, index=True)
    pesquisa_id = Column(Integer, ForeignKey("pesquisas.id"))
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    nota = Column(Integer)