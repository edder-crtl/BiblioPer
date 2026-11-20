"""Punto de entrada FastAPI - BiblioPer."""
from fastapi import FastAPI
from app.database import engine, Base
from app import models  # noqa: F401 - importa modelos para que Base los registre

app = FastAPI(
    title="BiblioPer API",
    description="API REST para sistema de gestión de biblioteca",
    version="0.1.0",
)


# Crear tablas al arrancar (solo desarrollo; en producción usar migraciones)
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"mensaje": "BiblioPer API funcionando", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}

# Las rutas se importarán y registrarán aquí cuando se implementen
# from app.routers import usuarios, libros, ejemplares, prestamos, reservas, multas
# app.include_router(usuarios.router)
# app.include_router(libros.router)
# app.include_router(ejemplares.router)
# app.include_router(prestamos.router)
# app.include_router(reservas.router)
# app.include_router(multas.router) No newline at end of file