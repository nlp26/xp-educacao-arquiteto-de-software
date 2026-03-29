from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.model.cliente import Cliente
from app.repository.cliente_repository import ClienteRepository
from app.schema.cliente_schema import ClienteCreate, ClienteUpdate


class ClienteService:
    """
    Camada de regras de negocio.
    Recebe a session, instancia o repository, e orquestra as operacoes
    aplicando validacoes antes de delegar pro banco.
    """

    def __init__(self, db: Session):
        self.repo = ClienteRepository(db)

    # -- Consultas --

    def listar_todos(self) -> list[Cliente]:
        """Lista completa de clientes"""
        return self.repo.find_all()

    def buscar_por_id(self, cliente_id: int) -> Cliente:
        """Busca por ID. Levanta 404 se nao encontrar."""
        cliente = self.repo.find_by_id(cliente_id)
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente {cliente_id} nao encontrado",
            )
        return cliente

    def buscar_por_nome(self, nome: str) -> list[Cliente]:
        """Busca parcial por nome"""
        return self.repo.find_by_nome(nome)

    def contar(self) -> int:
        """Total de registros"""
        return self.repo.count()

    # -- Escrita --

    def criar(self, dados: ClienteCreate) -> Cliente:
        """Cria um novo cliente a partir do DTO"""
        cliente = Cliente(
            nome=dados.nome,
            email=dados.email,
            telefone=dados.telefone,
        )
        return self.repo.save(cliente)

    def atualizar(self, cliente_id: int, dados: ClienteUpdate) -> Cliente:
        """Atualiza os dados de um cliente existente"""
        cliente = self.buscar_por_id(cliente_id)  # 404 se nao existir
        cliente.nome = dados.nome
        cliente.email = dados.email
        cliente.telefone = dados.telefone
        return self.repo.update(cliente)

    def deletar(self, cliente_id: int) -> None:
        """Remove um cliente pelo ID"""
        cliente = self.buscar_por_id(cliente_id)  # 404 se nao existir
        self.repo.delete(cliente)
