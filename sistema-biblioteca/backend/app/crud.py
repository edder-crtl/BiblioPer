import os
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas
from .auth import hash_password

# Parámetros del sistema (CU-11 los volverá configurables)
DIAS_PRESTAMO = 7
MAX_PRESTAMOS = 3
VALOR_MULTA_DIA = 1000.0


class ReglaNegocio(Exception):
    """Error de regla de negocio; se responde como 400."""


# ---------- Usuarios ----------
def crear_usuario(db: Session, datos: schemas.UsuarioCrear) -> models.Usuario:
    if db.query(models.Usuario).filter(
        (models.Usuario.documento == datos.documento) | (models.Usuario.correo == datos.correo)
    ).first():
        raise ReglaNegocio("Ya existe un usuario con ese documento o correo")
    usuario = models.Usuario(
        **datos.model_dump(exclude={"contrasena"}),
        contrasena_hash=hash_password(datos.contrasena),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def crear_admin_inicial(db: Session) -> None:
    if db.query(models.Usuario).filter_by(rol="administrador").first():
        return
    crear_usuario(db, schemas.UsuarioCrear(
        nombre="Administrador",
        documento="admin",
        correo="admin@biblioper.local",
        contrasena=os.getenv("ADMIN_PASSWORD", "admin123"),
        rol="administrador",
    ))


def obtener_usuario_por_documento(db: Session, documento: str):
    return db.query(models.Usuario).filter_by(documento=documento).first()


def listar_usuarios(db: Session):
    return db.query(models.Usuario).all()


def actualizar_usuario(db: Session, usuario_id: int, datos: schemas.UsuarioActualizar):
    usuario = db.get(models.Usuario, usuario_id)
    if not usuario:
        raise ReglaNegocio("Usuario no encontrado")
    cambios = datos.model_dump(exclude_unset=True)
    if "contrasena" in cambios:
        usuario.contrasena_hash = hash_password(cambios.pop("contrasena"))
    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario


# ---------- Libros ----------
def crear_libro(db: Session, datos: schemas.LibroCrear) -> models.Libro:
    if db.query(models.Libro).filter_by(isbn=datos.isbn).first():
        raise ReglaNegocio("Ya existe un libro con ese ISBN")
    libro = models.Libro(**datos.model_dump())
    db.add(libro)
    db.commit()
    db.refresh(libro)
    return libro


def buscar_libros(db: Session, q: str | None = None):
    consulta = db.query(models.Libro)
    if q:
        patron = f"%{q}%"
        consulta = consulta.filter(
            models.Libro.titulo.ilike(patron)
            | models.Libro.autor.ilike(patron)
            | models.Libro.categoria.ilike(patron)
            | models.Libro.isbn.ilike(patron)
        )
    return consulta.all()


def actualizar_libro(db: Session, libro_id: int, datos: schemas.LibroActualizar):
    libro = db.get(models.Libro, libro_id)
    if not libro:
        raise ReglaNegocio("Libro no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(libro, campo, valor)
    db.commit()
    db.refresh(libro)
    return libro


def eliminar_libro(db: Session, libro_id: int) -> None:
    libro = db.get(models.Libro, libro_id)
    if not libro:
        raise ReglaNegocio("Libro no encontrado")
    for ejemplar in libro.ejemplares:
        if ejemplar.prestamos:
            raise ReglaNegocio("No se puede eliminar un libro con historial de préstamos")
    db.delete(libro)
    db.commit()


def agregar_ejemplar(db: Session, libro_id: int, datos: schemas.EjemplarCrear):
    if not db.get(models.Libro, libro_id):
        raise ReglaNegocio("Libro no encontrado")
    if db.query(models.Ejemplar).filter_by(codigo=datos.codigo).first():
        raise ReglaNegocio("Ya existe un ejemplar con ese código")
    ejemplar = models.Ejemplar(codigo=datos.codigo, libro_id=libro_id)
    db.add(ejemplar)
    db.commit()
    db.refresh(ejemplar)
    return ejemplar