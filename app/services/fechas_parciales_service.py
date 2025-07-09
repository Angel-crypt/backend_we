from datetime import datetime
from app.utils.supabase_connection import supabaseConnection

supabase = supabaseConnection.get_instance().get_client()

def crear_fecha_parcial(id_asignacion: int, numero_parcial: int, fecha_inicio: datetime, fecha_fin: datetime, activo: bool = True) -> dict:
    # Verificar que no exista ya una fecha para este parcial
    existente = supabase.table("fechas_parciales") \
        .select("*") \
        .eq("id_asignacion", id_asignacion) \
        .eq("numero_parcial", numero_parcial) \
        .execute()

    if existente.data:
        return {"error": "Ya existe una fecha configurada para este parcial"}

    # Insertar nuevo registro
    res = supabase.table("fechas_parciales").insert({
        "id_asignacion": id_asignacion,
        "numero_parcial": numero_parcial,
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "activo": activo
    }).execute()

    return res.data[0] if res.data else {"error": "No se pudo registrar la fecha"}
