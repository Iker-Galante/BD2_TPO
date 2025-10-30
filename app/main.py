import pandas as pd
from db import get_mongo_collection

def load_csv_to_mongo():
    mongo_collection = get_mongo_collection()
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
        if file == "resources/polizas.csv":
            for record in records:
                # Extract id_cliente for the query but remove it from the record
                id_cliente = record["id_cliente"]
                poliza_record = {k: v for k, v in record.items() if k != "id_cliente"} #Saco al id del cliente 
                query_filter = {"id_cliente": id_cliente}
                update_operation = {"$push": {"polizas": poliza_record}}
                mongo_collection.update_one(query_filter, update_operation)
        if file=="resources/vehiculos.csv":
            for record in records:
                id_cliente = record["id_cliente"]
                vehiculo_record = {k: v for k, v in record.items() if k != "id_cliente"}
                query_filter = {"id_cliente": id_cliente}
                update_operation = {"$push": {"vehiculos": vehiculo_record}}
                mongo_collection.update_one(query_filter, update_operation)
        else :
            mongo_collection.insert_many(records)

        print(f"Inserted {len(records)} records from {file}")

if __name__ == "__main__":
    load_csv_to_mongo()
