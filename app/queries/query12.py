import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
            print(f"✓ Cache HIT - Retrieved {len(cached_result)} agents from Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} seconds remaining)\n")
            
            print("Agents and associated claims count:")
            for a in cached_result:
                print(
                    f"Agente {a['id_agente']} - {a.get('nombre', '')} {a.get('apellido', '')}: "
                    f"{a['siniestros_asociados']} siniestros"
                )
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Querying MongoDB...")
    collection = get_mongo_collection()
    agents = {}

    clients = collection.find({
        "id_cliente": {"$exists": True},
        "polizas": {"$exists": True}
    })

    for client in clients:
        for poliza in client.get("polizas", []):
            id_agente = poliza.get("id_agente")
            siniestros = poliza.get("siniestros", [])

            if not siniestros:
                continue

            if id_agente is None:
                continue

            try:
                id_agente_int = int(id_agente)
            except (TypeError, ValueError):
                continue

            agente_info = poliza.get("agente", {})

            if id_agente_int not in agents:
                agents[id_agente_int] = {
                    "id_agente": id_agente_int,
                    "nombre": agente_info.get("nombre"),
                    "apellido": agente_info.get("apellido"),
                    "siniestros_asociados": 0
                }

            agents[id_agente_int]["siniestros_asociados"] += len(siniestros)

    result = list(agents.values())
    
    # Store in cache (5 minutes)
    if use_cache:
        cache.set(cache_key, result, ttl=300)
        print(f"✓ Stored {len(result)} agents in cache (TTL: 300 seconds)\n")

    print("Agents and associated claims count:")
    for a in result:
        print(
            f"Agente {a['id_agente']} - {a.get('nombre', '')} {a.get('apellido', '')}: "
            f"{a['siniestros_asociados']} siniestros"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 12 ===\n")
    get_agents_with_claims_count()
