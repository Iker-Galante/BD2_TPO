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
                    f"Poliza {r['nro_poliza']} - "
                    f"Estado poliza: {r['estado_poliza']} - "
                    f"Cliente {r['id_cliente']}: {r['cliente']} - "
                    f"Estado cliente: {r['estado_cliente']}"
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
        estado_cliente = (
            "Activo" if client.get("activo") is True
            else "Inactivo"
        )

        for poliza in client.get("polizas", []):
            if poliza.get("estado") == "Suspendida":
                result.append({
                    "nro_poliza": poliza.get("nro_poliza"),
                    "estado_poliza": poliza.get("estado"),
                    "id_cliente": client.get("id_cliente"),
                    "cliente": f"{nombre} {apellido}",
                    "estado_cliente": estado_cliente
                })
    
    # Store in cache (8 minutes)
    if use_cache:
        cache.set(cache_key, result, ttl=480)
        print(f"✓ Almacenadas {len(result)} pólizas suspendidas en caché (TTL: 480 segundos)\n")

    print(f"Se encontraron {len(result)} pólizas suspendidas:")
    for r in result:
        print(
            f"Poliza {r['nro_poliza']} - "
            f"Estado poliza: {r['estado_poliza']} - "
            f"Cliente {r['id_cliente']}: {r['cliente']} - "
            f"Estado cliente: {r['estado_cliente']}"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 10 ===\n")
    get_suspended_policies()
