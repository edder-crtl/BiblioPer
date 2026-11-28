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
    if libro.reservas:
        raise ReglaNegocio("No se puede eliminar un libro con reservas")
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

# ---------- Préstamos, devoluciones y multas ----------
def notificar(correo: str, mensaje: str) -> None:
    # Pendiente: reemplazar por el servicio de correo (RF-10)
    print(f"[NOTIFICACIÓN] {correo}: {mensaje}")


def registrar_prestamo(db: Session, datos: schemas.PrestamoCrear, bibliotecario_id: int):
    lector = obtener_usuario_por_documento(db, datos.documento)
    if not lector or lector.rol != "lector" or not lector.activo:
        raise ReglaNegocio("Lector no encontrado o inactivo")

    multas_pendientes = (
        db.query(models.Multa)
        .join(models.Prestamo)
        .filter(models.Prestamo.usuario_id == lector.id, models.Multa.pagada.is_(False))
        .count()
    )
    if multas_pendientes:
        raise ReglaNegocio("El lector tiene multas pendientes")

    activos = db.query(models.Prestamo).filter_by(usuario_id=lector.id, estado="activo").count()
    if activos >= MAX_PRESTAMOS:
        raise ReglaNegocio(f"El lector alcanzó el límite de {MAX_PRESTAMOS} préstamos")

    ejemplar = db.query(models.Ejemplar).filter_by(codigo=datos.codigo_ejemplar).first()
    if not ejemplar:
        raise ReglaNegocio("Ejemplar no encontrado")
    if ejemplar.estado != "disponible":
        raise ReglaNegocio("El ejemplar no está disponible")

    ahora = datetime.now()
    prestamo = models.Prestamo(
        fecha_prestamo=ahora,
        fecha_vencimiento=ahora + timedelta(days=DIAS_PRESTAMO),
        usuario_id=lector.id,
        bibliotecario_id=bibliotecario_id,
        ejemplar_id=ejemplar.id,
    )
    ejemplar.estado = "prestado"
    db.add(prestamo)
    db.commit()
    db.refresh(prestamo)
    return prestamo


def registrar_devolucion(db: Session, prestamo_id: int):
    prestamo = db.get(models.Prestamo, prestamo_id)
    if not prestamo or prestamo.estado != "activo":
        raise ReglaNegocio("Préstamo activo no encontrado")

    ahora = datetime.now()
    prestamo.fecha_devolucion = ahora
    prestamo.estado = "devuelto"
    prestamo.ejemplar.estado = "disponible"

    dias_retraso = (ahora.date() - prestamo.fecha_vencimiento.date()).days
    if dias_retraso > 0:
        db.add(models.Multa(valor=dias_retraso * VALOR_MULTA_DIA, prestamo_id=prestamo.id))

    # Avisar al primero de la cola de reservas (CU-05)
    siguiente = (
        db.query(models.Reserva)
        .filter_by(libro_id=prestamo.ejemplar.libro_id, estado="pendiente")
        .order_by(models.Reserva.fecha_reserva)
        .first()
    )
    if siguiente:
        siguiente.estado = "notificada"
        notificar(siguiente.usuario.correo, f"El libro '{prestamo.ejemplar.libro.titulo}' ya está disponible")

    db.commit()
    db.refresh(prestamo)
    return prestamo


def historial_prestamos(db: Session, usuario_id: int):
    return (
        db.query(models.Prestamo)
        .filter_by(usuario_id=usuario_id)
        .order_by(models.Prestamo.fecha_prestamo.desc())
        .all()
    )


def pagar_multa(db: Session, multa_id: int):
    multa = db.get(models.Multa, multa_id)
    if not multa:
        raise ReglaNegocio("Multa no encontrada")
    multa.pagada = True
    db.commit()
    db.refresh(multa)
    return multa

# ---------- Reservas ----------
def crear_reserva(db: Session, usuario_id: int, libro_id: int):
    libro = db.get(models.Libro, libro_id)
    if not libro:
        raise ReglaNegocio("Libro no encontrado")
    if any(e.estado == "disponible" for e in libro.ejemplares):
        raise ReglaNegocio("Hay ejemplares disponibles, solicita el préstamo directamente")
    if db.query(models.Reserva).filter_by(usuario_id=usuario_id, libro_id=libro_id, estado="pendiente").first():
        raise ReglaNegocio("Ya tienes una reserva pendiente de este libro")
    reserva = models.Reserva(usuario_id=usuario_id, libro_id=libro_id)
    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    return reserva


# ---------- Reportes ----------
def reporte_prestamos_activos(db: Session):
    return db.query(models.Prestamo).filter_by(estado="activo").all()


def reporte_mas_prestados(db: Session, limite: int = 10):
    filas = (
        db.query(models.Libro.id, models.Libro.titulo, func.count(models.Prestamo.id))
        .join(models.Ejemplar, models.Ejemplar.libro_id == models.Libro.id)
        .join(models.Prestamo, models.Prestamo.ejemplar_id == models.Ejemplar.id)
        .group_by(models.Libro.id)
        .order_by(func.count(models.Prestamo.id).desc())
        .limit(limite)
        .all()
    )
    return [{"libro_id": f[0], "titulo": f[1], "total_prestamos": f[2]} for f in filas]


def reporte_morosos(db: Session):
    return (
        db.query(models.Usuario)
        .join(models.Prestamo, models.Prestamo.usuario_id == models.Usuario.id)
        .filter(models.Prestamo.estado == "activo", models.Prestamo.fecha_vencimiento < datetime.now())
        .distinct()
        .all()
    )

