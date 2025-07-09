from dataclasses import dataclass
from app.models.base_model import ModelBase

@dataclass
class Grupo(ModelBase):
    id_grupo: str
    nombre_grupo: str
    generacion: str
    facultad: str