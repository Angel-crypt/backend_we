from dataclasses import dataclass
from app.models.base_model import ModelBase

@dataclass
class AsignacionCurso(ModelBase):
    id_asignacion: int
    id_curso: str
    id_grupo: str
    id_maestro: str