import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_mongo_collection

def get_expired_policies():

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
            if poliza.get("estado") == "Vencida":
                result.append({
                    "nro_poliza": poliza.get("nro_poliza"),
                    "tipo": poliza.get("tipo"),
                    "estado": poliza.get("estado"),
                    "cliente": f"{nombre} {apellido}"
                })

    print(f"Found {len(result)} expired policies with client name:")
    for r in result:
        print(
            f"Poliza {r['nro_poliza']} ({r['tipo']}) - "
            f"Estado: {r['estado']} - Cliente: {r['cliente']}"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 6 ===\n")
    get_expired_policies()
