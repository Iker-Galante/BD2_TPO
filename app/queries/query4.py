import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import RedisCache
import json
from datetime import datetime


def get_clients_without_active_policies(use_cache=True):
    """
    Get clients without active policies using Redis cache
    """
    cache_key = "query4:clients_no_active_policies"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Se recuperaron {len(cached_result)} clientes desde Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} segundos restantes)\n")
            
            for c in cached_result:
                print(f"Cliente {c['id_cliente']}: {c['nombre']} {c['apellido']}")
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Consultando MongoDB...")
    collection = get_mongo_collection()

    clients = collection.aggregate([{
        "$match": {
            "polizas": {
                "$elemMatch": {
                    "estado": {"$ne": "Activa"}
                }
            }
        }
    }, {"$project": {
            "id_cliente": "$id_cliente",
            "nombre": "$nombre",
            "apellido": "$apellido"
        }
    }])
    result = [client for client in clients]
    
    # Store in cache (5 minutes)
    if use_cache:
        cache.set(cache_key, clients, ttl=300)
        print(f"✓ Almacenados {len(result)} clientes en caché (TTL: 300 segundos)\n")

    print(f"Se encontraron {len(result)} clientes sin pólizas activas:")
    for c in result:
        print(f"Cliente {c['id_cliente']}: {c['nombre']} {c['apellido']}")

    return result


if __name__ == "__main__":
    get_clients_without_active_policies()
