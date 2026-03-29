from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.controller.cliente_controller import router as cliente_router

# Cria tabelas no startup (em prod trocar por Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="API REST para gestao de clientes — Bootcamp Arquitetura de Software",
)

app.include_router(cliente_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
