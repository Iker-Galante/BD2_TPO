import pandas as pd
from app.db import get_mongo_collection, get_redis_client

def load_csv_to_mongo():
    mongo_collection = get_mongo_collection()
    redis_client = get_redis_client()
    
    # Clear the collection first to avoid duplicates
    mongo_collection.delete_many({})
    
    csv_files = [
        "resources/clientes.csv",
        "resources/polizas.csv", 
        "resources/siniestros.csv",
        "resources/agentes.csv",
        "resources/vehiculos.csv"
    ]

    for file in csv_files:
        df = pd.read_csv(file)
        records = df.to_dict(orient="records")
        
        if file == "resources/clientes.csv":
            # Insert clients first as base documents
            mongo_collection.insert_many(records)
            
        elif file == "resources/polizas.csv":
            for record in records:
                # Extract id_cliente for the query but remove it from the record
                id_cliente = record["id_cliente"]
                poliza_record = {k: v for k, v in record.items() if k != "id_cliente"}
                
                # Check if poliza already exists for this client
                query_filter = {
                    "id_cliente": id_cliente, 
                    "polizas.nro_poliza": {"$ne": poliza_record["nro_poliza"]}
                }
                update_operation = {"$push": {"polizas": poliza_record}}
                mongo_collection.update_one(query_filter, update_operation)
                
        elif file == "resources/siniestros.csv":
            for record in records:
                # Extract nro_poliza for the query but remove it from the record
                nro_poliza = record["nro_poliza"]
                siniestro_record = {k: v for k, v in record.items() if k != "nro_poliza"}
                
                # Check if siniestro already exists for this poliza
                query_filter = {
                    "polizas.nro_poliza": nro_poliza,
                    "polizas.siniestros.id_siniestro": {"$ne": siniestro_record["id_siniestro"]}
                }
                update_operation = {"$push": {"polizas.$.siniestros": siniestro_record}}
                mongo_collection.update_one(query_filter, update_operation)
                
        elif file == "resources/vehiculos.csv":
            for record in records:
                id_cliente = record["id_cliente"]
                vehiculo_record = {k: v for k, v in record.items() if k != "id_cliente"}
                
                # Check if vehiculo already exists for this client
                query_filter = {
                    "id_cliente": id_cliente,
                    "vehiculos.id_vehiculo": {"$ne": vehiculo_record["id_vehiculo"]}
                }
                update_operation = {"$push": {"vehiculos": vehiculo_record}}
                mongo_collection.update_one(query_filter, update_operation)
                
        elif file == "resources/agentes.csv":
            for record in records:
                id_agente = record["id_agente"]
                agente_record = {k: v for k, v in record.items() if k != "id_agente"}
                
                # Add agent info to ALL polizas that have this agent using arrayFilters
                query_filter = {"polizas.id_agente": id_agente}
                update_operation = {"$set": {"polizas.$[elem].agente": agente_record}}
                array_filters = [{"elem.id_agente": id_agente}]
                
                mongo_collection.update_many(
                    query_filter, 
                    update_operation, 
                    array_filters=array_filters
                )

        print(f"Processed {len(records)} records from {file}")

        build_top_coverage_in_redis(mongo_collection, redis_client)


def build_top_coverage_in_redis(mongo_collection, redis_client):

        redis_key = "top_clients_coverage"
        redis_client.delete(redis_key)

        clients = mongo_collection.find({
            "id_cliente": {"$exists": True},
            "polizas": {"$exists": True}
        })

        for client in clients:
            total_coverage = 0.0

            for poliza in client.get("polizas", []):
                cov = poliza.get("cobertura_total")
                if cov is None:
                    continue
                try:
                    total_coverage += float(cov)
                except (TypeError, ValueError):
                    continue

            if total_coverage > 0:
                member = f"{client['id_cliente']}|{client.get('nombre', '')} {client.get('apellido', '')}"
                # score = cobertura_total
                redis_client.zadd(redis_key, {member: total_coverage}) # lo guardo en un sorted set


if __name__ == "__main__":
    load_csv_to_mongo()
