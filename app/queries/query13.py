import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_mongo_collection
from app.cache import invalidate_cache_pattern


def create_client(client_data):
    """
    Create a new client (Alta)
    
    Args:
        client_data: Dictionary with client information
        Required fields: id_cliente, nombre, apellido, dni, email
        Optional fields: telefono, direccion, ciudad, provincia, activo
    
    Returns:
        Created client document or error message
    """
    collection = get_mongo_collection()
    
    # Validate required fields
    required_fields = ['id_cliente', 'nombre', 'apellido', 'dni', 'email']
    for field in required_fields:
        if field not in client_data:
            return {"error": f"Missing required field: {field}"}
    
    # Check if client already exists
    existing = collection.find_one({"id_cliente": client_data['id_cliente']})
    if existing:
        return {"error": f"Client with id_cliente {client_data['id_cliente']} already exists"}
    
    # Set default values
    if 'activo' not in client_data:
        client_data['activo'] = True
    
    # Initialize empty arrays for relationships
    client_data['polizas'] = []
    client_data['vehiculos'] = []
    
    try:
        result = collection.insert_one(client_data)
        print(f"✓ Client created successfully with ID: {client_data['id_cliente']}")
        
        # Invalidate related caches
        invalidate_cache_pattern("query1:*")  # Active clients
        invalidate_cache_pattern("query4:*")  # Clients without policies
        print("✓ Cache invalidated")
        
        return {
            "success": True,
            "id_cliente": client_data['id_cliente'],
            "message": "Client created successfully"
        }
    except Exception as e:
        return {"error": f"Error creating client: {str(e)}"}


def read_client(id_cliente):
    """
    Read/retrieve a client by ID (Baja - Read)
    
    Args:
        id_cliente: Client ID to search for
    
    Returns:
        Client document or error message
    """
    collection = get_mongo_collection()
    
    client = collection.find_one(
        {"id_cliente": id_cliente},
        {"_id": 0}  # Exclude MongoDB _id from result
    )
    
    if not client:
        return {"error": f"Client with id_cliente {id_cliente} not found"}
    
    print(f"✓ Client found: {client.get('nombre')} {client.get('apellido')}")
    return client


def update_client(id_cliente, update_data):
    """
    Update client information (Modificación)
    
    Args:
        id_cliente: Client ID to update
        update_data: Dictionary with fields to update
    
    Returns:
        Success message or error
    """
    collection = get_mongo_collection()
    
    # Check if client exists
    existing = collection.find_one({"id_cliente": id_cliente})
    if not existing:
        return {"error": f"Client with id_cliente {id_cliente} not found"}
    
    # Don't allow updating id_cliente
    if 'id_cliente' in update_data:
        del update_data['id_cliente']
    
    # Don't allow updating polizas or vehiculos through this method
    if 'polizas' in update_data:
        del update_data['polizas']
    if 'vehiculos' in update_data:
        del update_data['vehiculos']
    
    try:
        result = collection.update_one(
            {"id_cliente": id_cliente},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print(f"✓ Client {id_cliente} updated successfully")
            
            # Invalidate related caches
            invalidate_cache_pattern("query1:*")
            invalidate_cache_pattern("query4:*")
            print("✓ Cache invalidated")
            
            return {
                "success": True,
                "id_cliente": id_cliente,
                "modified_fields": list(update_data.keys()),
                "message": "Client updated successfully"
            }
        else:
            return {"message": "No changes were made"}
    except Exception as e:
        return {"error": f"Error updating client: {str(e)}"}


def delete_client(id_cliente, soft_delete=True):
    """
    Delete a client (Baja)
    
    Args:
        id_cliente: Client ID to delete
        soft_delete: If True, marks client as inactive; if False, permanently deletes
    
    Returns:
        Success message or error
    """
    collection = get_mongo_collection()
    
    # Check if client exists
    existing = collection.find_one({"id_cliente": id_cliente})
    if not existing:
        return {"error": f"Client with id_cliente {id_cliente} not found"}
    
    try:
        if soft_delete:
            # Soft delete: mark as inactive
            result = collection.update_one(
                {"id_cliente": id_cliente},
                {"$set": {"activo": False}}
            )
            print(f"✓ Client {id_cliente} marked as inactive")
            
            # Invalidate caches
            invalidate_cache_pattern("query1:*")
            invalidate_cache_pattern("query4:*")
            print("✓ Cache invalidated")
            
            return {
                "success": True,
                "id_cliente": id_cliente,
                "message": "Client marked as inactive (soft delete)"
            }
        else:
            # Hard delete: permanently remove
            result = collection.delete_one({"id_cliente": id_cliente})
            print(f"✓ Client {id_cliente} permanently deleted")
            
            # Invalidate caches
            invalidate_cache_pattern("query*")  # Invalidate all query caches
            print("✓ Cache invalidated")
            
            return {
                "success": True,
                "id_cliente": id_cliente,
                "message": "Client permanently deleted"
            }
    except Exception as e:
        return {"error": f"Error deleting client: {str(e)}"}


def list_clients(filter_active=None):
    """
    List all clients with optional filtering
    
    Args:
        filter_active: If True, only active clients; if False, only inactive; if None, all
    
    Returns:
        List of clients
    """
    collection = get_mongo_collection()
    
    query = {"id_cliente": {"$exists": True}}
    if filter_active is not None:
        query["activo"] = filter_active
    
    clients = list(collection.find(query, {"_id": 0}))
    
    print(f"Found {len(clients)} clients")
    for client in clients:
        status = "✓" if client.get('activo') else "✗"
        print(f"{status} {client.get('id_cliente')}: {client.get('nombre')} {client.get('apellido')}")
    
    return clients


# Example usage and testing
if __name__ == "__main__":
    print("=== Client CRUD Operations (ABM) ===\n")
    
    # Test 1: Create a new client
    print("1. Creating a new client...")
    new_client = {
        "id_cliente": 9999,
        "nombre": "Test",
        "apellido": "Cliente",
        "dni": "12345678",
        "email": "test@example.com",
        "telefono": "1234567890",
        "direccion": "Test Address 123",
        "ciudad": "Buenos Aires",
        "provincia": "Buenos Aires",
        "activo": True
    }
    result = create_client(new_client)
    print(result)
    print()
    
    # Test 2: Read the client
    print("2. Reading the client...")
    client = read_client(9999)
    if 'error' not in client:
        print(f"Found: {client.get('nombre')} {client.get('apellido')}")
    print()
    
    # Test 3: Update the client
    print("3. Updating the client...")
    update_result = update_client(9999, {
        "telefono": "0987654321",
        "email": "newemail@example.com"
    })
    print(update_result)
    print()
    
    # Test 4: List clients
    print("4. Listing all clients...")
    list_clients()
    print()
    
    # Test 5: Delete (soft delete)
    print("5. Deleting the client (soft delete)...")
    delete_result = delete_client(9999, soft_delete=True)
    print(delete_result)
    print()
    
    # Cleanup: Hard delete the test client
    print("6. Cleanup: Permanently deleting test client...")
    delete_client(9999, soft_delete=False)
