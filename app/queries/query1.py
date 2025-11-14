import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection, get_redis_client
from app.cache import RedisCache
import json
from datetime import datetime


def get_active_clients(use_cache=True):
    """
    Retrieve clients whose state is active (activo = True)
    Uses Redis cache to improve performance
    """
    cache_key = "query1:active_clients"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Se recuperaron {len(cached_result)} clientes activos desde Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} segundos restantes)")
            
            # Print summary
            for client in cached_result:  # Show first 5
                print(f"  - {client['nombre']} {client['apellido']} (ID: {client['id_cliente']}) - {client['email']}")
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Consultando MongoDB...")
    collection = get_mongo_collection()
    
    # Query for clients where activo is True AND id_cliente exists (to filter only client documents)
    active_clients = collection.find({"activo": True, "id_cliente": {"$exists": True}})
    
    result = [client for client in active_clients]
    
    # Store in cache (5 minutes TTL)
    if use_cache:
        cache.set(cache_key, result, ttl=300)
        print(f"✓ Almacenados {len(result)} clientes en caché (TTL: 300 segundos)")
    
    print(f"\nSe encontraron {len(result)} clientes activos:")
    for client in result:
        print(f"  - {client['nombre']} {client['apellido']} (ID: {client['id_cliente']}) - {client['email']}")
    
    return result

# Example usage functions
if __name__ == "__main__":
    # Show available estado
    get_active_clients()
