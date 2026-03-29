from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schema.cliente_schema import ClienteCreate, ClienteUpdate, ClienteResponse
from app.service.cliente_service import ClienteService

router = APIRouter(prefix="/clientes", tags=["Clientes"])


def _service(db: Session = Depends(get_db)) -> ClienteService:
    """Factory: injeta a session do request no service"""
    return ClienteService(db)


# ──────────────── READ ────────────────


@router.get(
    "/",
    response_model=list[ClienteResponse],
    summary="Listar todos os clientes",
)
def find_all(svc: ClienteService = Depends(_service)):
    return svc.listar_todos()


@router.get(
    "/contar",
    summary="Contar total de clientes",
)
def count(svc: ClienteService = Depends(_service)):
    return {"total": svc.contar()}


@router.get(
    "/buscar",
    response_model=list[ClienteResponse],
    summary="Buscar clientes por nome",
)
def find_by_name(
    nome: str = Query(..., min_length=1, description="Termo de busca"),
    svc: ClienteService = Depends(_service),
):
    return svc.buscar_por_nome(nome)


@router.get(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Buscar cliente por ID",
)
def find_by_id(cliente_id: int, svc: ClienteService = Depends(_service)):
    return svc.buscar_por_id(cliente_id)


# ──────────────── CREATE ────────────────


@router.post(
    "/",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo cliente",
)
def create(dados: ClienteCreate, svc: ClienteService = Depends(_service)):
    return svc.criar(dados)


# ──────────────── UPDATE ────────────────


@router.put(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Atualizar cliente",
)
def update(
    cliente_id: int,
    dados: ClienteUpdate,
    svc: ClienteService = Depends(_service),
):
    return svc.atualizar(cliente_id, dados)


# ──────────────── DELETE ────────────────


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover cliente",
)
def delete(cliente_id: int, svc: ClienteService = Depends(_service)):
    svc.deletar(cliente_id)
