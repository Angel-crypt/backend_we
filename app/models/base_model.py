from dataclasses import dataclass, fields
from typing import Type, TypeVar, get_type_hints
from enum import Enum
from datetime import date, datetime, time

T = TypeVar("T", bound="ModelBase")

@dataclass
class ModelBase:
    @classmethod
    def from_dict(cls: Type[T], data: dict) -> T:
        type_hints = get_type_hints(cls)
        converted = {}

        for field in fields(cls):
            key = field.name
            value = data.get(key)

            if value is None:
                converted[key] = None
                continue

            field_type = type_hints.get(key)

            # Auto conversión para Enums
            if isinstance(field_type, type) and issubclass(field_type, Enum):
                converted[key] = field_type(value)

            # Fechas y horas en ISO 8601
            elif field_type is datetime:
                converted[key] = datetime.fromisoformat(value)
            elif field_type is date:
                converted[key] = date.fromisoformat(value)
            elif field_type is time:
                converted[key] = time.fromisoformat(value)
            else:
                converted[key] = value

        return cls(**converted)

    def to_dict(self) -> dict:
        result = {}
        for field in fields(self):
            key = field.name
            value = getattr(self, key)

            if isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, (datetime, date, time)):
                result[key] = value.isoformat()
            else:
                result[key] = value

        return result

# --- Enums ---
class DiaSemanaEnum(str, Enum):
    LUNES = "lunes"
    MARTES = "martes"
    MIERCOLES = "miércoles"
    JUEVES = "jueves"
    VIERNES = "viernes"
    SABADO = "sábado"
    DOMINGO = "domingo"
