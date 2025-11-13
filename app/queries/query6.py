import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import RedisCache

def get_expired_policies(use_cache=True):
    """
    Get expired policies with client name using Redis cache
    """
    cache_key = "query6:expired_policies"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Se recuperaron {len(cached_result)} pólizas vencidas desde Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} segundos restantes)\n")
            
            for r in cached_result:
                print(
                    f"Poliza {r['nro_poliza']} ({r['tipo']}) - "
                    f"Estado: {r['estado']} - Cliente: {r['cliente']}"
                )
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Consultando MongoDB...")
    collection = get_mongo_collection()
    result = []

    clients = collection.find({
        "id_cliente": {"$exists": True},
        "polizas": {"$exists": True}
    })

    for client in clients:
        nombre = client.get("nombre", "")
        apellido = client.get("apellido", "")

        for poliza in client.get("polizas", []):
            if poliza.get("estado") == "Vencida":
                result.append({
                    "nro_poliza": poliza.get("nro_poliza"),
                    "tipo": poliza.get("tipo"),
                    "estado": poliza.get("estado"),
                    "cliente": f"{nombre} {apellido}"
                })
    
    # Store in cache (10 minutes - expired policies don't change)
    if use_cache:
        cache.set(cache_key, result, ttl=600)
        print(f"✓ Almacenadas {len(result)} pólizas vencidas en caché (TTL: 600 segundos)\n")

    print(f"Se encontraron {len(result)} pólizas vencidas con nombre de cliente:")
    for r in result:
        print(
            f"Poliza {r['nro_poliza']} ({r['tipo']}) - "
            f"Estado: {r['estado']} - Cliente: {r['cliente']}"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 6 ===\n")
    get_expired_policies()
