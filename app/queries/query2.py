import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_mongo_collection, get_redis_client
import json
from datetime import datetime

def get_open_claims():

    collection = get_mongo_collection()
    result = []

    open_claims = collection.find({
        "id_siniestro": {"$exists": True},
        "estado": "Abierto"
    })

    for claim in open_claims:
        nro_poliza = claim["nro_poliza"]

        poliza = collection.find_one({
            "nro_poliza": nro_poliza,
            "id_cliente": {"$exists": True}
        })
        if not poliza:
            continue

        id_cliente = poliza["id_cliente"]

        cliente = collection.find_one({
            "id_cliente": id_cliente,
            "nombre": {"$exists": True}
        })
        if not cliente:
            continue

        result.append({
            "id_siniestro": claim["id_siniestro"],
            "tipo": claim["tipo"],
            "monto_estimado": claim["monto_estimado"],
            "cliente": f"{cliente['nombre']} {cliente['apellido']}"
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
