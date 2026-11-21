import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .database import get_db

SECRET_KEY = os.getenv("SECRET_KEY", "cambiar-en-produccion")
ALGORITHM = "HS256"
EXPIRA_MINUTOS = 120

oauth2 = OAuth2PasswordBearer(tokenUrl="login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verificar_password(password: str, hash_guardado: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash_guardado.encode())


def crear_token(usuario_id: int) -> str:
    payload = {
        "sub": str(usuario_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=EXPIRA_MINUTOS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def usuario_actual(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> models.Usuario:
    try:
        datos = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = int(datos["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    usuario = db.get(models.Usuario, usuario_id)
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=401, detail="Usuario no válido")
    return usuario


def requiere_roles(*roles: str):
    def dependencia(usuario: models.Usuario = Depends(usuario_actual)) -> models.Usuario:
        if usuario.rol not in roles:
            raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
        return usuario

    return dependencia