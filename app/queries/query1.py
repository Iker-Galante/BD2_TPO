import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
            print(f"✓ Cache HIT - Retrieved {len(cached_result)} active clients from Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} seconds remaining)")
            
            # Print summary
            for client in cached_result[:5]:  # Show first 5
                print(f"  - {client['nombre']} {client['apellido']} (ID: {client['id_cliente']}) - {client['email']}")
            if len(cached_result) > 5:
                print(f"  ... and {len(cached_result) - 5} more")
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Querying MongoDB...")
    collection = get_mongo_collection()
    
    # Query for clients where activo is True AND id_cliente exists (to filter only client documents)
    active_clients = collection.find({"activo": True, "id_cliente": {"$exists": True}})
    
    result = []
    for client in active_clients:
        client['_id'] = str(client['_id'])
        result.append(client)
    
    # Store in cache (5 minutes TTL)
    if use_cache:
        cache.set(cache_key, result, ttl=300)
        print(f"✓ Stored {len(result)} clients in cache (TTL: 300 seconds)")
    
    print(f"\nFound {len(result)} active clients:")
    for client in result:
        print(f"  - {client['nombre']} {client['apellido']} (ID: {client['id_cliente']}) - {client['email']}")
    
    return result

# Example usage functions
if __name__ == "__main__":
    print("=== MongoDB Query Examples ===\n")
    # Show available estado
    get_active_clients()
