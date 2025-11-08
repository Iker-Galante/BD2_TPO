import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_mongo_collection


def get_open_claims():

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
                if siniestro.get("estado") == "Abierto":
                    result.append({
                        "id_siniestro": siniestro.get("id_siniestro"),
                        "tipo": siniestro.get("tipo"),
                        "monto_estimado": siniestro.get("monto_estimado"),
                        "cliente": f"{nombre} {apellido}"
                    })

    print(f"Found {len(result)} open claims info:")
    for r in result:
        print(
            f"Siniestro {r['id_siniestro']}: "
            f"{r['tipo']} - ${r['monto_estimado']} - Cliente: {r['cliente']}"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 2 ===\n")
    get_open_claims()
