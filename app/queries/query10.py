import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_mongo_collection


def get_suspended_policies():

    collection = get_mongo_collection()
    result = []

    clients = collection.find({
        "id_cliente": {"$exists": True},
        "polizas": {"$exists": True}
    })

    for client in clients:
        nombre = client.get("nombre", "")
        apellido = client.get("apellido", "")
        estado_cliente = (
            "Activo" if client.get("activo") is True
            else "Inactivo"
        )

        for poliza in client.get("polizas", []):
            if poliza.get("estado") == "Suspendida":
                result.append({
                    "nro_poliza": poliza.get("nro_poliza"),
                    "estado_poliza": poliza.get("estado"),
                    "id_cliente": client.get("id_cliente"),
                    "cliente": f"{nombre} {apellido}",
                    "estado_cliente": estado_cliente
                })

    print(f"Found {len(result)} suspended policies:")
    for r in result:
        print(
            f"Poliza {r['nro_poliza']} - "
            f"Estado poliza: {r['estado_poliza']} - "
            f"Cliente {r['id_cliente']}: {r['cliente']} - "
            f"Estado cliente: {r['estado_cliente']}"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 10 ===\n")
    get_suspended_policies()
