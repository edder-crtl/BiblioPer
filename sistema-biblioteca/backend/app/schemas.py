from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

Rol = Literal["administrador", "bibliotecario", "lector"]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Usuarios ----------
class UsuarioCrear(BaseModel):
    nombre: str
    documento: str
    correo: str
    contrasena: str
    rol: Rol = "lector"


class UsuarioActualizar(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    contrasena: Optional[str] = None
    activo: Optional[bool] = None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    documento: str
    correo: str
    rol: str
    activo: bool


# ---------- Libros y ejemplares ----------
class LibroCrear(BaseModel):
    isbn: str
    titulo: str
    autor: str
    categoria: Optional[str] = None
    anio_publicacion: Optional[int] = None


class LibroActualizar(BaseModel):
    titulo: Optional[str] = None
    autor: Optional[str] = None
    categoria: Optional[str] = None
    anio_publicacion: Optional[int] = None


class EjemplarCrear(BaseModel):
    codigo: str


class EjemplarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    estado: str
    libro_id: int


class LibroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    isbn: str
    titulo: str
    autor: str
    categoria: Optional[str]
    anio_publicacion: Optional[int]
    ejemplares: list[EjemplarOut] = []


# ---------- Préstamos, multas y reservas ----------
class PrestamoCrear(BaseModel):
    documento: str
    codigo_ejemplar: str


class MultaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    valor: float
    pagada: bool


class PrestamoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fecha_prestamo: datetime
    fecha_vencimiento: datetime
    fecha_devolucion: Optional[datetime]
    estado: str
    usuario_id: int
    ejemplar_id: int
    multa: Optional[MultaOut] = None


class ReservaCrear(BaseModel):
    libro_id: int


class ReservaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fecha_reserva: datetime
    estado: str
    usuario_id: int
    libro_id: int