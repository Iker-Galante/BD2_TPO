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

    siniestros = collection.aggregate([
        { "$unwind": "$polizas"},
        { "$unwind": "$polizas.siniestros"},
        {
            "$match": {
                "polizas.siniestros.estado": "Abierto"
            }
        }, {
            "$project": {
                "id_siniestro": "$polizas.siniestros.id_siniestro",
                "tipo": "$polizas.siniestros.tipo",
                "monto_estimado": "$polizas.siniestros.monto_estimado",
                "cliente": {"$concat": ["$nombre", " ", "$apellido"]}
            }
        }
    ])

    result = [siniestro for siniestro in siniestros]

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
    get_open_claims()
