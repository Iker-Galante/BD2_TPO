import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_mongo_collection

def get_agents_with_claims_count():

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

            if id_agente is None or not siniestros:
                continue

            agente_info = poliza.get("agente", {})

            if id_agente not in agents:
                agents[id_agente] = {
                    "id_agente": id_agente,
                    "nombre": agente_info.get("nombre"),
                    "apellido": agente_info.get("apellido"),
                    "siniestros_asociados": 0
                }

            agents[id_agente]["siniestros_asociados"] += len(siniestros)

    result = list(agents.values())

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
