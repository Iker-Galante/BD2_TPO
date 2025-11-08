import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_mongo_collection

def get_accident_claims_2025():

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
                if siniestro.get("tipo") != "Accidente":
                    continue

                fecha_str = siniestro.get("fecha")
                if not fecha_str:
                    continue

                try:
                    fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
                except ValueError:
                    continue

                if fecha.year == 2025:
                    result.append({
                        "id_siniestro": siniestro.get("id_siniestro"),
                        "fecha": fecha_str,
                        "cliente": f"{nombre} {apellido}"
                    })

    print(f"Found {len(result)} claims in 2025:")
    for r in result:
        print(
            f"Siniestro {r['id_siniestro']} - Fecha: {r['fecha']} - "
            f"Cliente: {r['cliente']}"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB Query 8 ===\n")
    get_accident_claims_2025()
