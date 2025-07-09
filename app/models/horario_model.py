from dataclasses import dataclass
from datetime import time
from app.models.base_model import ModelBase, DiaSemanaEnum

@dataclass
class HorarioAsignacion(ModelBase):
    id_horario: int
    id_asignacion: int
    dia_semana: DiaSemanaEnum
    hora_inicio: time
    hora_fin: time