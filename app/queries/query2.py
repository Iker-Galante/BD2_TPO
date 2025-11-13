import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import RedisCache


def get_open_claims(use_cache=True):
    """
    Get open claims with Redis caching
    """
    cache_key = "query2:open_claims"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Se recuperaron {len(cached_result)} siniestros abiertos desde Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} segundos restantes)\n")
            
            for r in cached_result:
                print(
                    f"Siniestro {r['id_siniestro']}: "
                    f"{r['tipo']} - ${r['monto_estimado']} - Cliente: {r['cliente']}"
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
            for siniestro in poliza.get("siniestros", []):
                if siniestro.get("estado") == "Abierto":
                    result.append({
                        "id_siniestro": siniestro.get("id_siniestro"),
                        "tipo": siniestro.get("tipo"),
                        "monto_estimado": siniestro.get("monto_estimado"),
                        "cliente": f"{nombre} {apellido}"
                    })

    # Store in cache (2 minutes TTL - shorter because claims change frequently)
    if use_cache:
        cache.set(cache_key, result, ttl=120)
        print(f"✓ Almacenados {len(result)} siniestros en caché (TTL: 120 segundos)\n")

    print(f"Se encontraron {len(result)} siniestros abiertos:")
    for r in result:
        print(
            f"Siniestro {r['id_siniestro']}: "
            f"{r['tipo']} - ${r['monto_estimado']} - Cliente: {r['cliente']}"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 2 ===\n")
    get_open_claims()
