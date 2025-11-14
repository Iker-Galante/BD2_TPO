import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import RedisCache

def get_accident_claims_last_year(use_cache=True):
    """
    Get accident claims from the last year using Redis cache
    """
    cache_key = "query8:accident_claims_last_year"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Se recuperaron {len(cached_result)} siniestros de accidente desde Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} segundos restantes)\n")
            
            for r in cached_result:
                print(
                    f"Siniestro {r['_id']} - Fecha: {datetime.fromisoformat(r['fecha']).strftime("%d/%m/%Y")} - "
                    f"Cliente: {r['nombre']} {r['apellido']}"
                )
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Consultando MongoDB...")
    collection = get_mongo_collection()

    siniestros = collection.aggregate([
        { 
            "$unwind": "$polizas"
        }, {
            "$unwind": "$polizas.siniestros"
        }, {
            "$match": {
                "id_cliente": {"$exists": True},
                "polizas": {"$exists": True},
                "polizas.siniestros.tipo": {"$eq": "Accidente"},
                "polizas.siniestros.fecha": {"$lte": datetime.now(), "$gt": datetime.now().replace(year = datetime.now().year - 1)}
            }
        }, {
            "$group": {
                "_id": "$polizas.siniestros.id_siniestro",
                "nombre": {"$first": "$nombre"},
                "apellido": {"$first": "$apellido"},
                "fecha": {"$first": "$polizas.siniestros.fecha"}
            }
        }
    ])
    result = [siniestro for siniestro in siniestros]

    # Store in cache (3 minutes - accident claims change moderately)
    if use_cache:
        cache.set(cache_key, result, ttl=180)
        print(f"✓ Almacenados {len(result)} siniestros de accidente en caché (TTL: 180 segundos)\n")

    print(f"Se encontraron {len(result)} siniestros en 2025:")
    for r in result:
        print(
            f"Siniestro {r['_id']} - Fecha: {r['fecha'].strftime("%d/%m/%Y")} - "
            f"Cliente: {r['nombre']} {r['apellido']}"
        )

    return result


if __name__ == "__main__":
    get_accident_claims_last_year()
