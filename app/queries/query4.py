import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
            print(f"✓ Cache HIT - Retrieved {len(cached_result)} clients from Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} seconds remaining)\n")
            
            for c in cached_result:
                print(f"Cliente {c['id_cliente']}: {c['nombre']} {c['apellido']}")
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Querying MongoDB...")
    collection = get_mongo_collection()
    result = []

    active_policy_clients = collection.distinct(
        "id_cliente",
        {
            "nro_poliza": {"$exists": True},
            "estado": "Activa"
        }
    )
    active_policy_clients = set(active_policy_clients)

    clients = collection.find({
        "id_cliente": {"$exists": True},
        "nombre": {"$exists": True}
    })

    for client in clients:
        if client["id_cliente"] not in active_policy_clients:
            result.append({
                "id_cliente": client["id_cliente"],
                "nombre": client["nombre"],
                "apellido": client["apellido"]
            })
    
    # Store in cache (5 minutes)
    if use_cache:
        cache.set(cache_key, result, ttl=300)
        print(f"✓ Stored {len(result)} clients in cache (TTL: 300 seconds)\n")

    print(f"Found {len(result)} clients without active policies:")
    for c in result:
        print(f"Cliente {c['id_cliente']}: {c['nombre']} {c['apellido']}")

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 4 ===\n")
    get_clients_without_active_policies()
