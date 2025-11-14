import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import RedisCache

def view_active_policies(use_cache=True):
    """
    View active policies sorted by start date using Redis cache
    """
    cache_key = "query9:active_policies_sorted"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Se recuperaron {len(cached_result)} pólizas activas desde Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} segundos restantes)\n")
            
            print("Pólizas activas\n")
            for p in cached_result:
                print(
                    f"{p['nro_poliza']} | Cliente {p['id_cliente']} | "
                    f"Tipo: {p['tipo']} | Inicio: {datetime.fromisoformat(p['fecha_inicio']).strftime("%d/%m/%Y")} | "
                    f"Fin: {datetime.fromisoformat(p['fecha_fin']).strftime("%d/%m/%Y")} | Estado: {p['estado']}"
                )
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Consultando MongoDB...")
    col = get_mongo_collection()

    pipeline = [
        {"$unwind": "$polizas"},

        {"$match": {
            "polizas.estado": "Activa"
        }},

        {"$sort": {
            "fecha_inicio_date": 1
        }},

        {"$project": {
            "_id": 0,
            "id_cliente": 1,
            "nro_poliza": "$polizas.nro_poliza",
            "tipo": "$polizas.tipo",
            "fecha_inicio": "$polizas.fecha_inicio",
            "fecha_fin": "$polizas.fecha_fin",
            "prima_mensual": "$polizas.prima_mensual",
            "cobertura_total": "$polizas.cobertura_total",
            "id_agente": "$polizas.id_agente",
            "estado": "$polizas.estado"
        }}
    ]
    
    # Convert to list for caching
    result = list(col.aggregate(pipeline))
    
    # Store in cache (5 minutes)
    if use_cache:
        cache.set(cache_key, result, ttl=300)
        print(f"✓ Almacenadas {len(result)} pólizas activas en caché (TTL: 300 segundos)\n")

    print("Pólizas activas\n")
    for p in result:
        print(
            f"{p['nro_poliza']} | Cliente {p['id_cliente']} | "
            f"Tipo: {p['tipo']} | Inicio: {p['fecha_inicio'].strftime("%d/%m/%Y")} | "
            f"Fin: {p['fecha_fin'].strftime("%d/%m/%Y")} | Estado: {p['estado']}"
        )

if __name__ == "__main__":
    view_active_policies()
