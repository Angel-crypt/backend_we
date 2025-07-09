import os
from supabase import create_client, Client

class supabaseConnection:
    """
    Clase para manejar la conexión a Supabase.
    """
    _instance: 'supabaseConnection' = None
    
    def __init__(self):
        self.url: str = os.environ.get("SUPABASE_URL")
        self.key: str = os.environ.get("SUPABASE_KEY")
        self.supabase: Client = create_client(self.url, self.key)
    
    @classmethod
    def get_instance(cls) -> 'supabaseConnection':
        """
        Método para obtener la instancia única de supabaseConnection.
        Si no existe, la crea.
        """
        if cls._instance is None:
            cls._instance = supabaseConnection()
        return cls._instance
    
    def get_client(self) -> Client:
        """
        Método para obtener el cliente de Supabase.
        """
        return self.supabase