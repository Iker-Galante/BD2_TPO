from app.db import get_mongo_collection

def view_active_policies():
    col = get_mongo_collection()

    pipeline = [
        {"$unwind": "$polizas"},

        {"$match": {
            "polizas.estado": "Activa"
        }},

        {"$set": {
            "fecha_inicio_date": {
                "$dateFromString": {
                    "dateString": "$polizas.fecha_inicio",
                    "format": "%d/%m/%Y"
                }
            }
        }},

        {"$sort": {
            "fecha_inicio_date": 1
        }},

        {"$project": {
            "_id": 0,
            "id_cliente": 1,
            "nro_poliza": "$polizas.nro_poliza",
            "tipo": "$polizas.tipo",
            "fecha_inicio": "$polizas.fecha_inicio",
            "fecha_fin": "$polizas.fecha_fin",
            "prima_mensual": "$polizas.prima_mensual",
            "cobertura_total": "$polizas.cobertura_total",
            "id_agente": "$polizas.id_agente",
            "estado": "$polizas.estado"
        }}
    ]

    print("Polizas activas\n")
    for p in col.aggregate(pipeline):
        print(
            f"{p['nro_poliza']} | Cliente {p['id_cliente']} | "
            f"Tipo: {p['tipo']} | Inicio: {p['fecha_inicio']} | "
            f"Fin: {p['fecha_fin']} | Estado: {p['estado']}"
        )

if __name__ == "__main__":
    view_active_policies()
