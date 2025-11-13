import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import RedisCache


def get_clients_with_multiple_insured_vehicles(use_cache=True):
    """
    Get clients with multiple insured vehicles using Redis cache
    """
    cache_key = "query11:clients_multiple_vehicles"
    cache = RedisCache()
    
    # Try cache first
    if use_cache:
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            print(f"✓ Cache HIT - Se recuperaron {len(cached_result)} clientes desde Redis")
            print(f"  (TTL: {cache.get_ttl(cache_key)} segundos restantes)\n")
            
            for r in cached_result:
                print(
                    f"Cliente {r['id_cliente']} - {r['cliente']}: "
                    f"{r['cantidad_vehiculos_asegurados']} vehículos asegurados"
                )
            
            return cached_result
    
    # Cache miss - query MongoDB
    print("✗ Cache MISS - Consultando MongoDB...")
    collection = get_mongo_collection()
    result = []

    clients = collection.find({
        "id_cliente": {"$exists": True},
        "vehiculos": {"$exists": True}
    })

    for client in clients:
        nombre = client.get("nombre", "")
        apellido = client.get("apellido", "")
        id_cliente = client.get("id_cliente")

        vehiculos = client.get("vehiculos", [])

        insured = [
            v for v in vehiculos
            if v.get("asegurado") in ("True", True)
        ]

        if len(insured) > 1:
            result.append({
                "id_cliente": id_cliente,
                "cliente": f"{nombre} {apellido}",
                "cantidad_vehiculos_asegurados": len(insured),
                "vehiculos": [
                    {
                        "id_vehiculo": v.get("id_vehiculo"),
                        "patente": v.get("patente"),
                        "marca": v.get("marca"),
                        "modelo": v.get("modelo"),
                        "anio": v.get("anio")
                    }
                    for v in insured
                ]
            })
    
    # Store in cache (10 minutes - vehicle count doesn't change often)
    if use_cache:
        cache.set(cache_key, result, ttl=600)
        print(f"✓ Almacenados {len(result)} clientes en caché (TTL: 600 segundos)\n")

    print(f"Se encontraron {len(result)} clientes con más de un vehículo asegurado:")

    for r in result:
        print(
            f"Cliente {r['id_cliente']} - {r['cliente']}: "
            f"{r['cantidad_vehiculos_asegurados']} vehículos asegurados"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 11 ===\n")
    get_clients_with_multiple_insured_vehicles()
