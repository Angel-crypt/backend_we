from datetime import datetime
from app.utils.supabase_connection import supabaseConnection

def puede_subir_calificacion(id_asignacion: int, numero_parcial: int) -> dict:
    """
    Verifica si se puede subir una calificación para una asignación y parcial dados.

    Returns:
        dict: { 'status': bool, 'mensaje': str }
    """
    supabase = supabaseConnection.get_instance().get_client()
    now = datetime.now()

    try:
        res = supabase.table("fechas_parciales") \
            .select("*") \
            .eq("id_asignacion", id_asignacion) \
            .eq("numero_parcial", numero_parcial) \
            .execute()
    except Exception as e:
        return {"status": False, "mensaje": f"Error al consultar Supabase: {e}"}

    if not res.data:
        return {"status": False, "mensaje": "No existe una asignación con ese parcial."}

    fecha = res.data[0]
    try:
        fecha_inicio = datetime.fromisoformat(fecha["fecha_inicio"])
        fecha_fin = datetime.fromisoformat(fecha["fecha_fin"])
    except Exception:
        return {"status": False, "mensaje": "Formato de fecha inválido en la base de datos."}

    if now < fecha_inicio:
        return {
            "status": False,
            "mensaje": f"Aún no inicia el periodo para subir calificaciones. Inicia el {fecha_inicio.strftime('%Y-%m-%d %H:%M')}"
        }
    elif now > fecha_fin:
        return {
            "status": False,
            "mensaje": f"Ya terminó el periodo para subir calificaciones. Finalizó el {fecha_fin.strftime('%Y-%m-%d %H:%M')}"
        }
    else:
        return {
            "status": True,
            "mensaje": "Está dentro del periodo permitido. Puedes subir calificaciones."
        }