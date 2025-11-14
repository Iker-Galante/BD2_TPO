import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import RedisCache


def get_clients_with_multiple_insured_vehicles(use_cache=True):
    """
    Get clients with multiple insured vehicles using Redis cache
    """
    cache_key = "query11:clients_multiple_vehicles"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Se recuperaron {len(cached_result)} clientes desde Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} segundos restantes)\n")
            
            for r in cached_result:
                print(
                    f"Cliente {r['_id']} - {r['cliente']}: "
                    f"{r['cantidad_vehiculos_asegurados']} vehículos asegurados"
                )
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Consultando MongoDB...")
    collection = get_mongo_collection()

    clients = collection.aggregate([
        {
            "$match": {
                "id_cliente": {"$exists": True},
            }
        }, {
            "$unwind": "$vehiculos"
        }, {
            "$project": {
                "_id": "$id_cliente",
                "cliente": {"$concat": ["$nombre", " ", "$apellido"]},
                "cantidad_vehiculos_asegurados": {"$sum": 1}
            }
        }, {
            "$match": {
                "cantidad_vehiculos_asegurados": {"$gte": 2}
            }
        }
    ])

    result = [client for client in clients]
    
    # Store in cache (10 minutes - vehicle count doesn't change often)
    if use_cache:
        cache.set(cache_key, result, ttl=600)
        print(f"✓ Almacenados {len(result)} clientes en caché (TTL: 600 segundos)\n")

    print(f"Se encontraron {len(result)} clientes con más de un vehículo asegurado:")

    for r in result:
        print(
            f"Cliente {r['_id']} - {r['cliente']}: "
            f"{r['cantidad_vehiculos_asegurados']} vehículos asegurados"
        )

    return result


if __name__ == "__main__":
    get_clients_with_multiple_insured_vehicles()
