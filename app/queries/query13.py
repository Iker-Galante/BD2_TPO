import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import invalidate_cache_pattern


def get_next_client_id():
    """
    Get the next available id_cliente by finding the maximum existing ID
    and incrementing it. Starts at 206 if no clients exist.
    
    Returns:
        int: Next available client ID
    """
    collection = get_mongo_collection()
    
    # Find the maximum id_cliente
    result = collection.find_one(
        {"id_cliente": {"$exists": True}},
        sort=[("id_cliente", -1)]
    )
    
    if result and 'id_cliente' in result:
        next_id = result['id_cliente'] + 1
    else:
        # No clients exist yet, start at 206
        next_id = 206
    
    return next_id


def create_client(client_data):
    """
    Create a new client (Alta)
    
    Args:
        client_data: Dictionary with client information
        Required fields: nombre, apellido, dni, email
        Optional fields: telefono, direccion, ciudad, provincia, activo
        Note: id_cliente is auto-generated if not provided
    
    Returns:
        Created client document or error message
    """
    collection = get_mongo_collection()
    
    # Auto-generate id_cliente if not provided
    if 'id_cliente' not in client_data:
        client_data['id_cliente'] = get_next_client_id()
    
    # Validate required fields
    required_fields = ['id_cliente', 'nombre', 'apellido', 'dni', 'email']
    for field in required_fields:
        if field not in client_data or not client_data[field]:
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
        print(f"✓ Cliente creado exitosamente con ID: {client_data['id_cliente']}")
        
        # Invalidate related caches
        invalidate_cache_pattern("query1:*")  # Active clients
        invalidate_cache_pattern("query4:*")  # Clients without policies
        print("✓ Caché invalidado")
        
        return {
            "success": True,
            "id_cliente": client_data['id_cliente'],
            "message": "Client created successfully"
        }
    except Exception as e:
        return {"error": f"Error creating client: {str(e)}"}


def read_client(id_cliente):
    """
    Read/retrieve a client by ID
    
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
        return {"error": f"Cliente con id_cliente {id_cliente} no encontrado"}
    
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
    
    # Remove empty strings from update_data (keep existing values)
    update_data = {k: v for k, v in update_data.items() if v != ''}
    
    if not update_data:
        return {"message": "No changes were made"}
    
    try:
        result = collection.update_one(
            {"id_cliente": id_cliente},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print(f"✓ Cliente {id_cliente} actualizado exitosamente")
            
            # Invalidate related caches
            invalidate_cache_pattern("query1:*")
            invalidate_cache_pattern("query4:*")
            print("✓ Caché invalidado")
            
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
            print(f"✓ Cliente {id_cliente} marcado como inactivo")
            
            # Invalidate caches
            invalidate_cache_pattern("query1:*")
            invalidate_cache_pattern("query4:*")
            print("✓ Caché invalidado")
            
            return {
                "success": True,
                "id_cliente": id_cliente,
                "message": "Client marked as inactive (soft delete)"
            }
        else:
            # Hard delete: permanently remove
            result = collection.delete_one({"id_cliente": id_cliente})
            print(f"✓ Cliente {id_cliente} eliminado permanentemente")
            
            # Invalidate caches
            invalidate_cache_pattern("query*")  # Invalidate all query caches
            print("✓ Caché invalidado")
            
            return {
                "success": True,
                "id_cliente": id_cliente,
                "message": "Client permanently deleted"
            }
    except Exception as e:
        return {"error": f"Error deleting client: {str(e)}"}


def list_clients(filter_active=None, limit=10):
    """
    List all clients with optional filtering
    
    Args:
        filter_active: If True, only active clients; if False, only inactive; if None, all
        limit: Maximum number of clients to display
    
    Returns:
        List of clients
    """
    collection = get_mongo_collection()
    
    query = {"id_cliente": {"$exists": True}}
    if filter_active is not None:
        query["activo"] = filter_active
    
    clients = list(collection.find(query, {"_id": 0}).limit(limit))
    
    return clients


def interactive_abm():
    """
    Interactive terminal-based ABM system for clients
    """
    print("\n" + "="*60)
    print("     SISTEMA ABM DE CLIENTES (Alta/Baja/Modificación)")
    print("="*60 + "\n")
    
    while True:
        print("\n¿Qué operación desea realizar?")
        print("1. Crear cliente (Alta)")
        print("2. Modificar cliente")
        print("3. Eliminar cliente (Baja)")
        print("4. Consultar cliente")
        print("5. Listar clientes")
        print("6. Salir")
        
        operation = input("\nIngrese el número de la operación (1-6): ").strip()
        
        if operation == "1":
            # CREATE
            print("\n--- CREAR NUEVO CLIENTE ---")
            client_data = {}
            
            # Auto-generate client ID
            next_id = get_next_client_id()
            client_data['id_cliente'] = next_id
            print(f"✓ ID Cliente asignado automáticamente: {next_id}\n")
            
            client_data['nombre'] = input("Nombre (*): ").strip()
            client_data['apellido'] = input("Apellido (*): ").strip()
            client_data['dni'] = input("DNI (*): ").strip()
            client_data['email'] = input("Email (*): ").strip()
            
            # Optional fields
            telefono = input("Teléfono (opcional): ").strip()
            if telefono:
                client_data['telefono'] = telefono
            
            direccion = input("Dirección (opcional): ").strip()
            if direccion:
                client_data['direccion'] = direccion
            
            ciudad = input("Ciudad (opcional): ").strip()
            if ciudad:
                client_data['ciudad'] = ciudad
            
            provincia = input("Provincia (opcional): ").strip()
            if provincia:
                client_data['provincia'] = provincia
            
            activo = input("Activo (S/n, por defecto S): ").strip().lower()
            client_data['activo'] = activo != 'n'
            
            # Confirm
            print("\n--- DATOS A CREAR ---")
            for key, value in client_data.items():
                print(f"{key}: {value}")
            
            confirm = input("\n¿Confirmar creación? (S/n): ").strip().lower()
            if confirm != 'n':
                result = create_client(client_data)
                if 'error' in result:
                    print(f"\n❌ Error: {result['error']}")
                else:
                    print(f"\n✓ Cliente creado exitosamente!")
        
        elif operation == "2":
            # UPDATE
            print("\n--- MODIFICAR CLIENTE ---")
            try:
                id_cliente = int(input("ID del cliente a modificar: "))
            except ValueError:
                print("❌ Error: ID debe ser un número")
                continue
            
            # First, retrieve current client
            client = read_client(id_cliente)
            if 'error' in client:
                print(f"\n❌ {client['error']}")
                continue
            
            print("\n--- DATOS ACTUALES ---")
            print(f"Nombre: {client.get('nombre', 'N/A')}")
            print(f"Apellido: {client.get('apellido', 'N/A')}")
            print(f"DNI: {client.get('dni', 'N/A')}")
            print(f"Email: {client.get('email', 'N/A')}")
            print(f"Teléfono: {client.get('telefono', 'N/A')}")
            print(f"Dirección: {client.get('direccion', 'N/A')}")
            print(f"Ciudad: {client.get('ciudad', 'N/A')}")
            print(f"Provincia: {client.get('provincia', 'N/A')}")
            print(f"Activo: {client.get('activo', 'N/A')}")
            
            print("\n--- NUEVOS VALORES ---")
            print("(Deje en blanco para mantener el valor actual)\n")
            
            update_data = {}
            
            nombre = input(f"Nombre [{client.get('nombre', '')}]: ").strip()
            if nombre:
                update_data['nombre'] = nombre
            
            apellido = input(f"Apellido [{client.get('apellido', '')}]: ").strip()
            if apellido:
                update_data['apellido'] = apellido
            
            dni = input(f"DNI [{client.get('dni', '')}]: ").strip()
            if dni:
                update_data['dni'] = dni
            
            email = input(f"Email [{client.get('email', '')}]: ").strip()
            if email:
                update_data['email'] = email
            
            telefono = input(f"Teléfono [{client.get('telefono', '')}]: ").strip()
            if telefono:
                update_data['telefono'] = telefono
            
            direccion = input(f"Dirección [{client.get('direccion', '')}]: ").strip()
            if direccion:
                update_data['direccion'] = direccion
            
            ciudad = input(f"Ciudad [{client.get('ciudad', '')}]: ").strip()
            if ciudad:
                update_data['ciudad'] = ciudad
            
            provincia = input(f"Provincia [{client.get('provincia', '')}]: ").strip()
            if provincia:
                update_data['provincia'] = provincia
            
            activo = input(f"Activo (S/n) [{client.get('activo', True)}]: ").strip().lower()
            if activo:
                update_data['activo'] = activo != 'n'
            
            if update_data:
                print("\n--- CAMPOS A MODIFICAR ---")
                for key, value in update_data.items():
                    print(f"{key}: {value}")
                
                confirm = input("\n¿Confirmar modificación? (S/n): ").strip().lower()
                if confirm != 'n':
                    result = update_client(id_cliente, update_data)
                    if 'error' in result:
                        print(f"\n❌ Error: {result['error']}")
                    else:
                        print(f"\n✓ Cliente modificado exitosamente!")
            else:
                print("\n⚠ No se ingresaron cambios")
        
        elif operation == "3":
            # DELETE
            print("\n--- ELIMINAR CLIENTE ---")
            try:
                id_cliente = int(input("ID del cliente a eliminar: "))
            except ValueError:
                print("❌ Error: ID debe ser un número")
                continue
            
            # Show client info
            client = read_client(id_cliente)
            if 'error' in client:
                print(f"\n❌ {client['error']}")
                continue
            
            print(f"\nCliente: {client.get('nombre')} {client.get('apellido')}")
            print(f"DNI: {client.get('dni')}")
            print(f"Email: {client.get('email')}")
            
            print("\nTipo de eliminación:")
            print("1. Lógica (marcar como inactivo)")
            print("2. Física (eliminar permanentemente)")
            
            delete_type = input("Seleccione (1/2): ").strip()
            
            confirm = input(f"\n¿CONFIRMAR ELIMINACIÓN del cliente {id_cliente}? (S/n): ").strip().lower()
            if confirm != 'n':
                soft_delete = delete_type != "2"
                result = delete_client(id_cliente, soft_delete=soft_delete)
                if 'error' in result:
                    print(f"\n❌ Error: {result['error']}")
                else:
                    print(f"\n✓ Cliente eliminado exitosamente!")
        
        elif operation == "4":
            # READ
            print("\n--- CONSULTAR CLIENTE ---")
            try:
                id_cliente = int(input("ID del cliente a consultar: "))
            except ValueError:
                print("❌ Error: ID debe ser un número")
                continue
            
            client = read_client(id_cliente)
            if 'error' in client:
                print(f"\n❌ {client['error']}")
            else:
                print("\n--- DATOS DEL CLIENTE ---")
                print(f"ID: {client.get('id_cliente')}")
                print(f"Nombre: {client.get('nombre', 'N/A')}")
                print(f"Apellido: {client.get('apellido', 'N/A')}")
                print(f"DNI: {client.get('dni', 'N/A')}")
                print(f"Email: {client.get('email', 'N/A')}")
                print(f"Teléfono: {client.get('telefono', 'N/A')}")
                print(f"Dirección: {client.get('direccion', 'N/A')}")
                print(f"Ciudad: {client.get('ciudad', 'N/A')}")
                print(f"Provincia: {client.get('provincia', 'N/A')}")
                print(f"Activo: {'Sí' if client.get('activo') else 'No'}")
                print(f"Nº Pólizas: {len(client.get('polizas', []))}")
                print(f"Nº Vehículos: {len(client.get('vehiculos', []))}")
        
        elif operation == "5":
            # LIST
            print("\n--- LISTAR CLIENTES ---")
            print("1. Todos")
            print("2. Solo activos")
            print("3. Solo inactivos")
            
            filter_option = input("Seleccione (1-3): ").strip()
            
            filter_active = None
            if filter_option == "2":
                filter_active = True
            elif filter_option == "3":
                filter_active = False
            
            try:
                limit = int(input("Cantidad máxima a mostrar (por defecto 10): ").strip() or "10")
            except ValueError:
                limit = 10
            
            clients = list_clients(filter_active=filter_active, limit=limit)
            
            print(f"\n--- CLIENTES ENCONTRADOS: {len(clients)} ---")
            for client in clients:
                status = "✓" if client.get('activo') else "✗"
                print(f"{status} ID {client.get('id_cliente')}: {client.get('nombre')} {client.get('apellido')} - {client.get('email')}")
        
        elif operation == "6":
            print("\n¡Hasta luego!")
            break
        
        else:
            print("\n❌ Opción inválida. Por favor seleccione 1-6.")


if __name__ == "__main__":
    interactive_abm()
