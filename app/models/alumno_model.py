from dataclasses import dataclass
from typing import Optional
from datetime import date
from enum import Enum
from app.models.base_model import ModelBase

class SexoEnum(str, Enum):
    MASCULINO = "M"
    FEMENINO = "F"
    OTRO = "O"

@dataclass
class Alumno(ModelBase):
    id_alumno: str
    id_grupo: str
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[SexoEnum] = None
    
    def to_dict(self) -> dict:
        # Primero obtenemos el diccionario base del padre
        base_dict = super().to_dict()
        
        # Calculamos el nombre completo
        nombre_completo = f"{self.nombre} {self.apellido_paterno or ''} {self.apellido_materno or ''}".strip()
        
        # Agregamos el nombre completo al diccionario
        base_dict['nombre_completo'] = nombre_completo
        
        return base_dict