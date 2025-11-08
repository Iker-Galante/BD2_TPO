import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_mongo_collection, get_redis_client
import json
from datetime import datetime

def get_insured_vehicles_with_client_and_policy():

    collection = get_mongo_collection()
    result = []

    vehicles = collection.find({
        "id_vehiculo": {"$exists": True},
        "asegurado": True
    })

    for vehicle in vehicles:
        id_cliente = vehicle["id_cliente"]

        cliente = collection.find_one({
            "id_cliente": id_cliente,
            "nombre": {"$exists": True}
        })
        if not cliente:
            continue

        policy = collection.find_one({
            "id_cliente": id_cliente,
            "nro_poliza": {"$exists": True},
            "tipo": "Auto"
        })
        if not policy:
            continue

        result.append({
            "id_vehiculo": vehicle["id_vehiculo"],
            "patente": vehicle["patente"],
            "cliente": f"{cliente['nombre']} {cliente['apellido']}",
            "nro_poliza": policy["nro_poliza"],
            "estado_poliza": policy.get("estado")
        })

    print(f"Found {len(result)} insured vehicles with client and policy:")

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
