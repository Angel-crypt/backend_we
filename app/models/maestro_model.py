from dataclasses import dataclass
from typing import Optional
from datetime import date
from app.models.base_model import ModelBase

@dataclass
class Maestro(ModelBase):
    id_usuario: str
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    especialidad: Optional[str] = None
    
    def to_dict(self) -> dict:        # Primero obtenemos el diccionario base del padre
        base_dict = super().to_dict()
        
        # Calculamos el nombre completo
        nombre_completo = f"{self.nombre} {self.apellido_paterno or ''} {self.apellido_materno or ''}".strip()
        
        # Agregamos el nombre completo al diccionario
        base_dict['nombre_completo'] = nombre_completo
        
        return base_dict