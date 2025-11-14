import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import RedisCache

def get_agents_with_claims_count(use_cache=True):
    """
    Get agents with claims count using Redis cache
    """
    cache_key = "query12:agents_claims_count"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Se recuperaron {len(cached_result)} agentes desde Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} segundos restantes)\n")
            
            print("Agentes y cantidad de siniestros asociados:")
            for a in cached_result:
                print(
                    f"Agente {a['_id']} - {a['nombre']} {a['apellido']}: "
                    f"{a['siniestros_asociados']} siniestros"
                )
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Consultando MongoDB...")
    collection = get_mongo_collection()

    clients = collection.find({
        "id_cliente": {"$exists": True},
        "polizas": {"$exists": True}
    })

    agents = collection.aggregate([
        { "$unwind": "$polizas" },
        { "$match": {
            "polizas.id_agente": {"$exists": True, "$gt": 0}
        }}, 
        { "$group": {
            "_id": "$polizas.id_agente",
            "nombre": {"$first": "$polizas.agente.nombre"},
            "apellido": {"$first": "$polizas.agente.apellido"},
            "siniestros_asociados": {"$sum": {"$size": {"$ifNull": ["$polizas.siniestros", []]}}}
        }}
    ])

    result = [agent for agent in agents]
    
    # Store in cache (5 minutes)
    if use_cache:
        cache.set(cache_key, result, ttl=300)
        print(f"✓ Almacenados {len(result)} agentes en caché (TTL: 300 segundos)\n")

    print("Agentes y cantidad de siniestros asociados:")
    for a in result:
        print(
            f"Agente {int(a['_id'])} - {a['nombre']} {a['apellido']}: "
            f"{a['siniestros_asociados']} siniestros"
        )

    return result


if __name__ == "__main__":
    get_agents_with_claims_count()
