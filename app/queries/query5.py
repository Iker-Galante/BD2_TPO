import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import RedisCache


def get_active_agents_with_assigned_policies_count(use_cache=True):
    """
    Get active agents with policy count using Redis cache
    """
    cache_key = "query5:active_agents_policies"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Retornando {len(cached_result)} agentes desde Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} segundos restantes)\n")
            
            print("Agentes activos con cantidad de pólizas asignadas:")
            for r in cached_result:
                print(
                    f"Agente {r['_id']} - {r['nombre']} {r['apellido']}: "
                    f"{r['polizas_asignadas']} pólizas"
                )
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Consultando MongoDB...")
    collection = get_mongo_collection()

    agents = collection.aggregate([
        {
            "$unwind": "$polizas"
        },
        {
            "$match": {
                "polizas.agente.activo": True
            }
        },
        {
            "$group": {
                "_id": "$polizas.id_agente",
                "nombre": {"$first": "$polizas.agente.nombre"},
                "apellido": {"$first": "$polizas.agente.apellido"},
                "polizas_asignadas": {"$sum": 1}
            }
        }
    ])

    result = [agent for agent in agents]
    
    # Store in cache (10 minutes - agent data changes less frequently)
    if use_cache:
        cache.set(cache_key, result, ttl=600)
        print(f"✓ Guardado {len(result)} agentes en cache (TTL: 600 segundos)\n")

    print("Agentes activos con cantidad de pólizas asignadas:")

    for r in result:
        print(
            f"Agente {r['_id']} - {r['nombre']} {r['apellido']}: "
            f"{r['polizas_asignadas']} pólizas"
        )

    return result


if __name__ == "__main__":
    get_active_agents_with_assigned_policies_count()
