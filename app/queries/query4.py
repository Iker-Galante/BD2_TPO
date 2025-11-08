import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_mongo_collection
import json
from datetime import datetime


def get_clients_without_active_policies():

    collection = get_mongo_collection()
    result = []

    active_policy_clients = collection.distinct(
        "id_cliente",
        {
            "nro_poliza": {"$exists": True},
            "estado": "Activa"
        }
    )
    active_policy_clients = set(active_policy_clients)

    clients = collection.find({
        "id_cliente": {"$exists": True},
        "nombre": {"$exists": True}
    })

    for client in clients:
        if client["id_cliente"] not in active_policy_clients:
            result.append({
                "id_cliente": client["id_cliente"],
                "nombre": client["nombre"],
                "apellido": client["apellido"]
            })

    print(f"Found {len(result)} clients without active policies:")
    for c in result:
        print(f"Cliente {c['id_cliente']}: {c['nombre']} {c['apellido']}")

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 4 ===\n")
    get_clients_without_active_policies()
