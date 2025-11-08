import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_mongo_collection


def get_clients_with_multiple_insured_vehicles():

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

    print(f"Found {len(result)} clients with more than one insured vehicle:")

    for r in result:
        print(
            f"Cliente {r['id_cliente']} - {r['cliente']}: "
            f"{r['cantidad_vehiculos_asegurados']} vehículos asegurados"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 11 ===\n")
    get_clients_with_multiple_insured_vehicles()
