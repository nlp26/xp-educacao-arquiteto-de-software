from sqlalchemy import Column, Integer, String

from app.database import Base


class Cliente(Base):
    """
    Entidade de dominio mapeada para a tabela 'clientes'.
    Campos:
        - id: chave primaria, autoincrement
        - nome: nome do cliente (indexado para buscas)
        - email: email unico do cliente
        - telefone: campo opcional
    """

    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(150), nullable=False, index=True)
    email = Column(String(200), nullable=False, unique=True)
    telefone = Column(String(20), nullable=True)

    def __repr__(self):
        return f"<Cliente(id={self.id}, nome='{self.nome}')>"
