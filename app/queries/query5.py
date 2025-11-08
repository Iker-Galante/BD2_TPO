import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_mongo_collection


def get_active_agents_with_assigned_policies_count():

    collection = get_mongo_collection()
    agents = {}

    clients = collection.find({
        "polizas": {"$exists": True}
    })

    for client in clients:
        for poliza in client.get("polizas", []):
            agente_info = poliza.get("agente")
            id_agente = poliza.get("id_agente")

            if not agente_info or id_agente is None:
                continue

            if not agente_info.get("activo"):
                continue

            if id_agente not in agents:
                agents[id_agente] = {
                    "id_agente": id_agente,
                    "nombre": agente_info.get("nombre"),
                    "apellido": agente_info.get("apellido"),
                    "polizas_asignadas": 0
                }

            agents[id_agente]["polizas_asignadas"] += 1

    result = list(agents.values())

    print("Active agents with assigned policies count:")

    for r in result:
        print(
            f"Agente {r['id_agente']} - {r['nombre']} {r['apellido']}: "
            f"{r['polizas_asignadas']} pólizas"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 5 ===\n")
    get_active_agents_with_assigned_policies_count()
