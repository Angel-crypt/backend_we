from datetime import datetime
from app.utils.supabase_connection import supabaseConnection

supabase = supabaseConnection.get_instance().get_client()

def puede_subir_calificacion(id_asignacion: int, numero_parcial: int) -> bool:
    now = datetime.now()

    res = supabase.table("fechas_parciales") \
        .select("*") \
        .eq("id_asignacion", id_asignacion) \
        .eq("numero_parcial", numero_parcial) \
        .eq("activo", True) \
        .execute()

    if not res.data:
        return False

    fecha = res.data[0]
    fecha_inicio = datetime.fromisoformat(fecha["fecha_inicio"])
    fecha_fin = datetime.fromisoformat(fecha["fecha_fin"])

    return fecha_inicio <= now <= fecha_fin