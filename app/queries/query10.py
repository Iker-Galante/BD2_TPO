import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import RedisCache


def get_suspended_policies(use_cache=True):
    """
    Get suspended policies with client status using Redis cache
    """
    cache_key = "query10:suspended_policies"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Se recuperaron {len(cached_result)} pólizas suspendidas desde Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} segundos restantes)\n")
            
            for r in cached_result:
                print(
                    f"Poliza {r['_id']} - "
                    f"Estado poliza: {r['estado_poliza']} - "
                    f"Cliente {r['id_cliente']}: {r['nombre']} {r['apellido']} - "
                    f"Estado cliente: { "Activo" if r['cliente_activo'] else "Inactivo"}"
                )
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Consultando MongoDB...")
    collection = get_mongo_collection()
    result = []

    polizas = collection.aggregate([
        {
            "$unwind": "$polizas"
        },  {
            "$match": {
                "id_cliente": {"$exists": True},
                "polizas": {"$exists": True},
                "polizas.estado": "Suspendida"
            }
        },  {
            "$project": {
                "_id": "$polizas.nro_poliza",
                "cliente_activo": "$activo",
                "estado_poliza": "$polizas.estado",
                "nombre": "$nombre",
                "apellido": "$apellido",
                "id_cliente": "$id_cliente"
            }
        }
    ])

    result = [poliza for poliza in polizas]
    
    # Store in cache (8 minutes)
    if use_cache:
        cache.set(cache_key, result, ttl=480)
        print(f"✓ Almacenadas {len(result)} pólizas suspendidas en caché (TTL: 480 segundos)\n")

    print(f"Se encontraron {len(result)} pólizas suspendidas:")
    for r in result:
        print(
            f"Poliza {r['_id']} - "
            f"Estado poliza: {r['estado_poliza']} - "
            f"Cliente {r['id_cliente']}: {r['nombre']} {r['apellido']} - "
            f"Estado cliente: { "Activo" if r['cliente_activo'] else "Inactivo"}"
        )

    return result


if __name__ == "__main__":
    get_suspended_policies()
