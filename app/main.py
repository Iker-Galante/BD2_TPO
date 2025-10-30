import pandas as pd
from db import get_mongo_collection

def load_csv_to_mongo():
    mongo_collection = get_mongo_collection()
    csv_files = [
        "resources/agentes.csv",
        "resources/clientes.csv",
        "resources/polizas.csv",
        "resources/siniestros.csv",
        "resources/vehiculos.csv"
    ]

    for file in csv_files:
        df = pd.read_csv(file)
        records = df.to_dict(orient="records")
        mongo_collection.insert_many(records)
        print(f"Inserted {len(records)} records from {file}")

if __name__ == "__main__":
    load_csv_to_mongo()
