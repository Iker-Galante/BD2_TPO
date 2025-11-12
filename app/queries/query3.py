import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_mongo_collection
from app.cache import RedisCache


def get_insured_vehicles_with_client_and_policy(use_cache=True):
    """
    Get insured vehicles with client and policy info using Redis cache
    """
    cache_key = "query3:insured_vehicles"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Retrieved {len(cached_result)} insured vehicles from Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} seconds remaining)\n")
            
            for r in cached_result:
                print(
                    f"Vehículo {r['id_vehiculo']} ({r['patente']}) - "
                    f"Cliente {r['cliente']} - "
                    f"Póliza {r['nro_poliza']} ({r['estado_poliza']})"
                )
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Querying MongoDB...")
    collection = get_mongo_collection()
    result = []

    clients = collection.find({
        "id_cliente": {"$exists": True},
        "vehiculos": {"$exists": True},
        "polizas": {"$exists": True}
    })

    for client in clients:
        nombre = client.get("nombre", "")
        apellido = client.get("apellido", "")

        polizas_auto = [
            p for p in client.get("polizas", [])
            if p.get("tipo") == "Auto"
        ]
        if not polizas_auto:
            continue

        poliza = polizas_auto[0]

        for vehiculo in client.get("vehiculos", []):
            asegurado = vehiculo.get("asegurado")
            if asegurado in (True, "True", "true", 1):
                result.append({
                    "id_vehiculo": vehiculo.get("id_vehiculo"),
                    "patente": vehiculo.get("patente"),
                    "cliente": f"{nombre} {apellido}",
                    "nro_poliza": poliza.get("nro_poliza"),
                    "estado_poliza": poliza.get("estado")
                })
    
    # Store in cache (7 minutes - vehicle insurance status doesn't change often)
    if use_cache:
        cache.set(cache_key, result, ttl=420)
        print(f"✓ Stored {len(result)} vehicles in cache (TTL: 420 seconds)\n")

    print(f"Found {len(result)} insured vehicles with client and Auto policy:")

    for r in result:
        print(
            f"Vehículo {r['id_vehiculo']} ({r['patente']} - "
            f"Cliente {r['cliente']} - "
            f"Póliza {r['nro_poliza']} ({r['estado_poliza']})"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 3 ===\n")
    get_insured_vehicles_with_client_and_policy()
