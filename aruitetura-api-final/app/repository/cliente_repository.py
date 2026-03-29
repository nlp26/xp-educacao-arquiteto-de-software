from sqlalchemy.orm import Session

from app.model.cliente import Cliente


class ClienteRepository:
    """
    Camada de acesso a dados.
    Encapsula todas as queries ao banco, isolando o restante
    da aplicacao de detalhes do SQLAlchemy.
    """

    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> list[Cliente]:
        """Retorna todos os clientes cadastrados"""
        return self.db.query(Cliente).order_by(Cliente.id).all()

    def find_by_id(self, cliente_id: int) -> Cliente | None:
        """Busca um cliente pela chave primaria"""
        return self.db.query(Cliente).filter(Cliente.id == cliente_id).first()

    def find_by_nome(self, nome: str) -> list[Cliente]:
        """Busca clientes cujo nome contenha o termo informado (case-insensitive)"""
        return (
            self.db.query(Cliente)
            .filter(Cliente.nome.ilike(f"%{nome}%"))
            .order_by(Cliente.nome)
            .all()
        )

    def count(self) -> int:
        """Retorna o total de clientes no banco"""
        return self.db.query(Cliente).count()

    def save(self, cliente: Cliente) -> Cliente:
        """Persiste um novo cliente e retorna com id gerado"""
        self.db.add(cliente)
        self.db.commit()
        self.db.refresh(cliente)
        return cliente

    def update(self, cliente: Cliente) -> Cliente:
        """Commita alteracoes feitas na entidade e atualiza"""
        self.db.commit()
        self.db.refresh(cliente)
        return cliente

    def delete(self, cliente: Cliente) -> None:
        """Remove o cliente do banco"""
        self.db.delete(cliente)
        self.db.commit()
