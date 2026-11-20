from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    documento = Column(String(20), unique=True, index=True, nullable=False)
    correo = Column(String(120), unique=True, nullable=False)
    contrasena_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default="lector")  # administrador | bibliotecario | lector
    activo = Column(Boolean, default=True)

    prestamos = relationship("Prestamo", back_populates="lector", foreign_keys="Prestamo.usuario_id")
    reservas = relationship("Reserva", back_populates="usuario")


class Libro(Base):
    __tablename__ = "libros"

    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(20), unique=True, index=True, nullable=False)
    titulo = Column(String(200), nullable=False, index=True)
    autor = Column(String(120), nullable=False, index=True)
    categoria = Column(String(60), index=True)
    anio_publicacion = Column(Integer)

    ejemplares = relationship("Ejemplar", back_populates="libro", cascade="all, delete-orphan")
    reservas = relationship("Reserva", back_populates="libro")


class Ejemplar(Base):
    __tablename__ = "ejemplares"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(30), unique=True, index=True, nullable=False)
    estado = Column(String(20), default="disponible")  # disponible | prestado
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)

    libro = relationship("Libro", back_populates="ejemplares")
    prestamos = relationship("Prestamo", back_populates="ejemplar")


class Prestamo(Base):
    __tablename__ = "prestamos"

    id = Column(Integer, primary_key=True, index=True)
    fecha_prestamo = Column(DateTime, default=datetime.now)
    fecha_vencimiento = Column(DateTime, nullable=False)
    fecha_devolucion = Column(DateTime, nullable=True)
    estado = Column(String(20), default="activo")  # activo | devuelto
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    bibliotecario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    ejemplar_id = Column(Integer, ForeignKey("ejemplares.id"), nullable=False)

    lector = relationship("Usuario", back_populates="prestamos", foreign_keys=[usuario_id])
    ejemplar = relationship("Ejemplar", back_populates="prestamos")
    multa = relationship("Multa", back_populates="prestamo", uselist=False)


class Multa(Base):
    __tablename__ = "multas"

    id = Column(Integer, primary_key=True, index=True)
    valor = Column(Float, nullable=False)
    pagada = Column(Boolean, default=False)
    prestamo_id = Column(Integer, ForeignKey("prestamos.id"), nullable=False)

    prestamo = relationship("Prestamo", back_populates="multa")


class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    fecha_reserva = Column(DateTime, default=datetime.now)
    estado = Column(String(20), default="pendiente")  # pendiente | notificada
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="reservas")
    libro = relationship("Libro", back_populates="reservas")