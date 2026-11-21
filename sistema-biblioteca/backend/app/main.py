from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .auth import crear_token, requiere_roles, usuario_actual, verificar_password
from .database import Base, SessionLocal, engine, get_db

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    crud.crear_admin_inicial(db)

app = FastAPI(title="BiblioPer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # el frontend se sirve aparte; restringir en producción
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(crud.ReglaNegocio)
def manejar_regla_negocio(request, exc: crud.ReglaNegocio):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# ---------- Autenticación ----------
@app.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = crud.obtener_usuario_por_documento(db, form.username)  # username = documento
    if not usuario or not usuario.activo or not verificar_password(form.password, usuario.contrasena_hash):
        raise HTTPException(status_code=401, detail="Documento o contraseña incorrectos")
    return schemas.Token(access_token=crear_token(usuario.id))


@app.post("/registro", response_model=schemas.UsuarioOut, status_code=201)
def registro(datos: schemas.UsuarioCrear, db: Session = Depends(get_db)):
    datos.rol = "lector"  # el autorregistro solo crea lectores
    return crud.crear_usuario(db, datos)


# ---------- Usuarios ----------
@app.get("/usuarios/me", response_model=schemas.UsuarioOut)
def mi_perfil(actual: models.Usuario = Depends(usuario_actual)):
    return actual


@app.post("/usuarios", response_model=schemas.UsuarioOut, status_code=201)
def crear_usuario(
    datos: schemas.UsuarioCrear,
    db: Session = Depends(get_db),
    actual: models.Usuario = Depends(requiere_roles("administrador", "bibliotecario")),
):
    if datos.rol != "lector" and actual.rol != "administrador":
        raise HTTPException(status_code=403, detail="Solo el administrador crea personal")
    return crud.crear_usuario(db, datos)


@app.get("/usuarios", response_model=list[schemas.UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(requiere_roles("administrador", "bibliotecario")),
):
    return crud.listar_usuarios(db)


@app.put("/usuarios/{usuario_id}", response_model=schemas.UsuarioOut)
def actualizar_usuario(
    usuario_id: int,
    datos: schemas.UsuarioActualizar,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(requiere_roles("administrador", "bibliotecario")),
):
    return crud.actualizar_usuario(db, usuario_id, datos)


@app.delete("/usuarios/{usuario_id}", response_model=schemas.UsuarioOut)
def desactivar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(requiere_roles("administrador", "bibliotecario")),
):
    return crud.actualizar_usuario(db, usuario_id, schemas.UsuarioActualizar(activo=False))


# ---------- Libros ----------
@app.get("/libros", response_model=list[schemas.LibroOut])
def buscar_libros(q: str | None = None, db: Session = Depends(get_db)):
    return crud.buscar_libros(db, q)


@app.post("/libros", response_model=schemas.LibroOut, status_code=201)
def crear_libro(
    datos: schemas.LibroCrear,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(requiere_roles("administrador", "bibliotecario")),
):
    return crud.crear_libro(db, datos)


@app.put("/libros/{libro_id}", response_model=schemas.LibroOut)
def actualizar_libro(
    libro_id: int,
    datos: schemas.LibroActualizar,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(requiere_roles("administrador", "bibliotecario")),
):
    return crud.actualizar_libro(db, libro_id, datos)


@app.delete("/libros/{libro_id}", status_code=204)
def eliminar_libro(
    libro_id: int,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(requiere_roles("administrador", "bibliotecario")),
):
    crud.eliminar_libro(db, libro_id)


@app.post("/libros/{libro_id}/ejemplares", response_model=schemas.EjemplarOut, status_code=201)
def agregar_ejemplar(
    libro_id: int,
    datos: schemas.EjemplarCrear,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(requiere_roles("administrador", "bibliotecario")),
):
    return crud.agregar_ejemplar(db, libro_id, datos)

# ---------- Préstamos y multas ----------
@app.post("/prestamos", response_model=schemas.PrestamoOut, status_code=201)
def registrar_prestamo(
    datos: schemas.PrestamoCrear,
    db: Session = Depends(get_db),
    actual: models.Usuario = Depends(requiere_roles("bibliotecario", "administrador")),
):
    return crud.registrar_prestamo(db, datos, actual.id)


@app.put("/prestamos/{prestamo_id}/devolucion", response_model=schemas.PrestamoOut)
def registrar_devolucion(
    prestamo_id: int,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(requiere_roles("bibliotecario", "administrador")),
):
    return crud.registrar_devolucion(db, prestamo_id)


@app.get("/prestamos/mis", response_model=list[schemas.PrestamoOut])
def mi_historial(db: Session = Depends(get_db), actual: models.Usuario = Depends(usuario_actual)):
    return crud.historial_prestamos(db, actual.id)


@app.put("/multas/{multa_id}/pagar", response_model=schemas.MultaOut)
def pagar_multa(
    multa_id: int,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(requiere_roles("bibliotecario", "administrador")),
):
    return crud.pagar_multa(db, multa_id)

# ---------- Reservas ----------
@app.post("/reservas", response_model=schemas.ReservaOut, status_code=201)
def reservar_libro(
    datos: schemas.ReservaCrear,
    db: Session = Depends(get_db),
    actual: models.Usuario = Depends(requiere_roles("lector")),
):
    return crud.crear_reserva(db, actual.id, datos.libro_id)


# ---------- Reportes (solo administrador) ----------
@app.get("/reportes/prestamos-activos", response_model=list[schemas.PrestamoOut])
def reporte_activos(db: Session = Depends(get_db), _=Depends(requiere_roles("administrador"))):
    return crud.reporte_prestamos_activos(db)


@app.get("/reportes/mas-prestados")
def reporte_mas_prestados(db: Session = Depends(get_db), _=Depends(requiere_roles("administrador"))):
    return crud.reporte_mas_prestados(db)


@app.get("/reportes/morosos", response_model=list[schemas.UsuarioOut])
def reporte_morosos(db: Session = Depends(get_db), _=Depends(requiere_roles("administrador"))):
    return crud.reporte_morosos(db)