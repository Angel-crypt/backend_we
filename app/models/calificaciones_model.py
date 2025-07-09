from dataclasses import dataclass
from typing import Optional
from app.models.base_model import ModelBase

@dataclass
class Calificaciones(ModelBase):
    id_calif_alum_curso: int
    id_alumno: str
    id_asignacion: int
    calificacion_parcial_1: Optional[float] = None
    fecha_parcial_1: Optional[str] = None
    calificacion_parcial_2: Optional[float] = None
    fecha_parcial_2: Optional[str] = None
    calificacion_parcial_3: Optional[float] = None
    fecha_parcial_3: Optional[str] = None
    calificacion_final: Optional[float] = None
    
    def calculate_final(self) -> Optional[float]:
        """
        Calcula la calificación final del alumno en el curso.
        La calificación final se calcula como el promedio de las tres calificaciones parciales.
        Si alguna de las calificaciones parciales es None, se retorna None.
        """
        if (self.calificacion_parcial_1 is None or
            self.calificacion_parcial_2 is None or
            self.calificacion_parcial_3 is None):
            return None
        
        return (self.calificacion_parcial_1 +
                self.calificacion_parcial_2 +
                self.calificacion_parcial_3) / 3.0