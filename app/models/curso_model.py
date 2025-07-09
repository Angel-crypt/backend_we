from dataclasses import dataclass
from typing import Optional
from app.models.base_model import ModelBase

@dataclass
class Curso(ModelBase):
    id_curso: str
    nombre: str
    codigo: Optional[str] = None
    descripcion: Optional[str] = None