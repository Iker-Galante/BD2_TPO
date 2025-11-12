import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_mongo_collection
from app.cache import RedisCache

def get_accident_claims_2025(use_cache=True):
    """
    Get accident claims from 2025 using Redis cache
    """
    cache_key = "query8:accident_claims_2025"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Retrieved {len(cached_result)} accident claims from Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} seconds remaining)\n")
            
            for r in cached_result:
                print(
                    f"Siniestro {r['id_siniestro']} - Fecha: {r['fecha']} - "
                    f"Cliente: {r['cliente']}"
                )
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Querying MongoDB...")
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
                if siniestro.get("tipo") != "Accidente":
                    continue

                fecha_str = siniestro.get("fecha")
                if not fecha_str:
                    continue

                try:
                    fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
                except ValueError:
                    continue

                if fecha.year == 2025:
                    result.append({
                        "id_siniestro": siniestro.get("id_siniestro"),
                        "fecha": fecha_str,
                        "cliente": f"{nombre} {apellido}"
                    })
    
    # Store in cache (3 minutes - accident claims change moderately)
    if use_cache:
        cache.set(cache_key, result, ttl=180)
        print(f"✓ Stored {len(result)} accident claims in cache (TTL: 180 seconds)\n")

    print(f"Found {len(result)} claims in 2025:")
    for r in result:
        print(
            f"Siniestro {r['id_siniestro']} - Fecha: {r['fecha']} - "
            f"Cliente: {r['cliente']}"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 8 ===\n")
    get_accident_claims_2025()
