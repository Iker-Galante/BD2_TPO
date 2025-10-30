import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_mongo_collection, get_redis_client
import json
from datetime import datetime


def get_active_clients():
    """
    Retrieve clients whose state is active (activo = True)
    """
    collection = get_mongo_collection()
    
    # Query for clients where activo is True AND id_cliente exists (to filter only client documents)
    active_clients = collection.find({"activo": True, "id_cliente": {"$exists": True}})
    
    result = []
    for client in active_clients:
        client['_id'] = str(client['_id'])
        result.append(client)
    
    print(f"Found {len(result)} active clients:")
    for client in result:
        print(f"  - {client['nombre']} {client['apellido']} (ID: {client['id_cliente']}) - {client['email']}")
    
    return result

# Example usage functions
if __name__ == "__main__":
    print("=== MongoDB Query Examples ===\n")
    # Show available estado
    get_active_clients()
