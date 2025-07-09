from dataclasses import dataclass
from datetime import time
from app.models.base_model import ModelBase, DiaSemanaEnum

@dataclass
class DisponibilidadMaestro(ModelBase):
    id_disponibilidad: int
    id_maestro: str
    dia_semana: DiaSemanaEnum
    hora_inicio: time
    hora_fin: time