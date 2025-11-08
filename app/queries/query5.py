import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_mongo_collection, get_redis_client
import json
from datetime import datetime


def get_active_agents_with_assigned_policies_count():

    collection = get_mongo_collection()
    result = []

    agents = collection.find({
        "id_agente": {"$exists": True},
        "activo": True
    })

    for agent in agents:
        agent_id = agent["id_agente"]

        policies_count = collection.count_documents({
            "nro_poliza": {"$exists": True},
            "id_agente": agent_id
        })

        result.append({
            "id_agente": agent_id,
            "nombre": agent["nombre"],
            "apellido": agent["apellido"],
            "polizas_asignadas": policies_count
        })

    print("Active agents with assigned policies count:")

    for r in result:
        print(
            f"Agente activo {r['id_agente']} - {r['nombre']} {r['apellido']}: "
            f"{r['polizas_asignadas']} pólizas"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 5 ===\n")
    get_active_agents_with_assigned_policies_count()
