from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum
from app.models.base_model import ModelBase

class RolEnum(str, Enum):
    ADMIN = "admin"
    MAESTRO = "maestro"

@dataclass
class Usuario(ModelBase):
    id_usuario: str
    contrasena: str
    rol: RolEnum
    fecha_creacion: Optional[datetime] = None