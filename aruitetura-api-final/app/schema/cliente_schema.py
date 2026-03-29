from pydantic import BaseModel, Field


class ClienteBase(BaseModel):
    """Campos comuns entre criacao e resposta"""

    nome: str = Field(..., min_length=1, max_length=150, examples=["Maria Silva"])
    email: str = Field(..., max_length=200, examples=["maria@email.com"])
    telefone: str | None = Field(default=None, max_length=20, examples=["11999990000"])


class ClienteCreate(ClienteBase):
    """Payload de entrada para criacao e atualizacao. Sem id."""
    pass


class ClienteUpdate(ClienteBase):
    """Payload de atualizacao. Todos os campos obrigatorios."""
    pass


class ClienteResponse(ClienteBase):
    """Resposta da API. Inclui o id gerado pelo banco."""

    id: int

    class Config:
        from_attributes = True
