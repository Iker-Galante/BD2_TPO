import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import invalidate_cache_pattern
from datetime import datetime


def get_next_siniestro_id():
    """
    Get the next available id_siniestro by finding the maximum existing ID
    and incrementing it. Starts at 9095 if no siniestros exist.
    
    Returns:
        int: Next available siniestro ID
    """
    collection = get_mongo_collection()
    
    # Find all siniestros across all policies and get the maximum id_siniestro
    pipeline = [
        {"$match": {"polizas": {"$exists": True}}},
        {"$unwind": "$polizas"},
        {"$unwind": {"path": "$polizas.siniestros", "preserveNullAndEmptyArrays": False}},
        {"$group": {
            "_id": None,
            "max_id": {"$max": "$polizas.siniestros.id_siniestro"}
        }}
    ]
    
    result = list(collection.aggregate(pipeline))
    
    if result and result[0]['max_id'] is not None:
        next_id = result[0]['max_id'] + 1
    else:
        # No siniestros exist yet, start at 9095
        next_id = 9095
    
    return next_id


def create_claim(claim_data):
    """
    Create a new claim (siniestro) and add it to the corresponding policy
    
    Args:
        claim_data: Dictionary with claim information
        Required fields: nro_poliza, tipo, fecha, monto_estimado, estado
        Optional fields: descripcion, monto_final, fecha_resolucion
        Note: id_siniestro is auto-generated if not provided
    
    Returns:
        Success message or error
    """
    collection = get_mongo_collection()
    
    # Auto-generate id_siniestro if not provided
    if 'id_siniestro' not in claim_data:
        claim_data['id_siniestro'] = get_next_siniestro_id()
    
    # Validate required fields
    required_fields = ['nro_poliza', 'id_siniestro', 'tipo', 'fecha', 'monto_estimado', 'estado']
    for field in required_fields:
        if field not in claim_data:
            return {"error": f"Missing required field: {field}"}
    
    nro_poliza = claim_data['nro_poliza']
    
    # Find the client with this policy
    client = collection.find_one({
        "polizas.nro_poliza": nro_poliza
    })
    
    if not client:
        return {"error": f"Policy {nro_poliza} not found"}
    
    # Check if claim already exists
    existing_claim = collection.find_one({
        "polizas.nro_poliza": nro_poliza,
        "polizas.siniestros.id_siniestro": claim_data['id_siniestro']
    })
    
    if existing_claim:
        return {"error": f"Claim with id_siniestro {claim_data['id_siniestro']} already exists for policy {nro_poliza}"}
    
    # Validate claim type
    valid_types = ['Accidente', 'Robo', 'Incendio', 'Danio', 'Granizo', 'Otro']
    if claim_data['tipo'] not in valid_types:
        return {"error": f"Invalid claim type. Must be one of: {', '.join(valid_types)}"}
    
    # Validate estado
    valid_estados = ['Abierto', 'En Proceso', 'Cerrado', 'Rechazado']
    if claim_data['estado'] not in valid_estados:
        return {"error": f"Invalid estado. Must be one of: {', '.join(valid_estados)}"}
    
    # Validate date format
    try:
        datetime.strptime(claim_data['fecha'], "%d/%m/%Y")
    except ValueError:
        return {"error": "Invalid date format. Use DD/MM/YYYY"}
    
    # Prepare claim data (remove nro_poliza as it's only for query)
    claim_record = {k: v for k, v in claim_data.items() if k != 'nro_poliza'}
    
    # Add default values
    if 'descripcion' not in claim_record:
        claim_record['descripcion'] = ''
    
    try:
        # Add claim to the policy's siniestros array
        result = collection.update_one(
            {"polizas.nro_poliza": nro_poliza},
            {"$push": {"polizas.$.siniestros": claim_record}}
        )
        
        if result.modified_count > 0:
            print(f"✓ Siniestro {claim_data['id_siniestro']} creado exitosamente para póliza {nro_poliza}")
            
            # Invalidate claims-related caches
            invalidate_cache_pattern("query2:*")  # Open claims
            invalidate_cache_pattern("query8:*")  # Accident claims
            invalidate_cache_pattern("query12:*")  # Agents with claims
            print("✓ Caché invalidado")
            
            return {
                "success": True,
                "id_siniestro": claim_data['id_siniestro'],
                "nro_poliza": nro_poliza,
                "message": "Claim created successfully"
            }
        else:
            return {"error": "Failed to create claim"}
    except Exception as e:
        return {"error": f"Error creating claim: {str(e)}"}


def update_claim_status(nro_poliza, id_siniestro, nuevo_estado, monto_final=None, fecha_resolucion=None):
    """
    Update claim status and resolution details
    
    Args:
        nro_poliza: Policy number
        id_siniestro: Claim ID
        nuevo_estado: New status (En Proceso, Cerrado, Rechazado)
        monto_final: Final amount (optional)
        fecha_resolucion: Resolution date (optional)
    
    Returns:
        Success message or error
    """
    collection = get_mongo_collection()
    
    valid_estados = ['Abierto', 'En Proceso', 'Cerrado', 'Rechazado']
    if nuevo_estado not in valid_estados:
        return {"error": f"Invalid estado. Must be one of: {', '.join(valid_estados)}"}
    
    # Build update operation
    update_op = {
        "polizas.$[poliza].siniestros.$[siniestro].estado": nuevo_estado
    }
    
    if monto_final is not None:
        update_op["polizas.$[poliza].siniestros.$[siniestro].monto_final"] = monto_final
    
    if fecha_resolucion is not None:
        # Validate date format
        try:
            datetime.strptime(fecha_resolucion, "%d/%m/%Y")
            update_op["polizas.$[poliza].siniestros.$[siniestro].fecha_resolucion"] = fecha_resolucion
        except ValueError:
            return {"error": "Invalid date format. Use DD/MM/YYYY"}
    
    try:
        result = collection.update_one(
            {"polizas.nro_poliza": nro_poliza},
            {"$set": update_op},
            array_filters=[
                {"poliza.nro_poliza": nro_poliza},
                {"siniestro.id_siniestro": id_siniestro}
            ]
        )
        
        if result.modified_count > 0:
            print(f"✓ Siniestro {id_siniestro} actualizado exitosamente a estado: {nuevo_estado}")
            
            # Invalidate claims-related caches
            invalidate_cache_pattern("query2:*")
            invalidate_cache_pattern("query8:*")
            print("✓ Caché invalidado")
            
            return {
                "success": True,
                "id_siniestro": id_siniestro,
                "nuevo_estado": nuevo_estado,
                "message": "Claim status updated successfully"
            }
        else:
            return {"error": "Claim not found or no changes were made"}
    except Exception as e:
        return {"error": f"Error updating claim: {str(e)}"}


def get_claims_by_policy(nro_poliza):
    """
    Get all claims for a specific policy
    
    Args:
        nro_poliza: Policy number
    
    Returns:
        List of claims or error
    """
    collection = get_mongo_collection()
    
    client = collection.find_one(
        {"polizas.nro_poliza": nro_poliza},
        {"polizas.$": 1, "nombre": 1, "apellido": 1}
    )
    
    if not client or 'polizas' not in client or len(client['polizas']) == 0:
        return {"error": f"Policy {nro_poliza} not found"}
    
    poliza = client['polizas'][0]
    siniestros = poliza.get('siniestros', [])
    
    print(f"Se encontraron {len(siniestros)} siniestros para póliza {nro_poliza}:")
    for s in siniestros:
        print(f"  - Siniestro {s.get('id_siniestro')}: {s.get('tipo')} - ${s.get('monto_estimado')} - {s.get('estado')}")
    
    return {
        "nro_poliza": nro_poliza,
        "cliente": f"{client.get('nombre')} {client.get('apellido')}",
        "siniestros": siniestros
    }


def interactive_abm():
    """
    Interactive terminal-based system for sinister management (Alta de Siniestros)
    """
    print("\n" + "="*60)
    print("     SISTEMA DE GESTIÓN DE SINIESTROS (Alta de Siniestros)")
    print("="*60 + "\n")
    
    while True:
        print("\n¿Qué operación desea realizar?")
        print("1. Crear nuevo siniestro (Alta)")
        print("2. Consultar siniestros de una póliza")
        print("3. Actualizar estado de siniestro")
        print("4. Salir")
        
        operation = input("\nIngrese el número de la operación (1-4): ").strip()
        
        if operation == "1":
            # CREATE CLAIM
            print("\n--- CREAR NUEVO SINIESTRO ---")
            claim_data = {}
            
            # Get policy number first and validate it exists
            nro_poliza = input("Número de Póliza (*): ").strip()
            
            # Validate that the policy exists
            collection = get_mongo_collection()
            policy_exists = collection.find_one({"polizas.nro_poliza": nro_poliza})
            
            if not policy_exists:
                print(f"\n❌ Error: La póliza '{nro_poliza}' no existe en el sistema")
                print("   No es posible crear el siniestro sin una póliza válida.")
                continue
            
            print(f"✓ Póliza '{nro_poliza}' encontrada")
            claim_data['nro_poliza'] = nro_poliza
            
            # Auto-generate claim ID
            next_id = get_next_siniestro_id()
            claim_data['id_siniestro'] = next_id
            print(f"✓ ID Siniestro asignado automáticamente: {next_id}")
            
            # Get claim type
            print("\nTipo de siniestro:")
            print("1. Accidente")
            print("2. Robo")
            print("3. Incendio")
            print("4. Danio")
            print("5. Otro")
            tipo_option = input("Seleccione el tipo (1-5): ").strip()
            tipo_map = {
                "1": "Accidente",
                "2": "Robo",
                "3": "Incendio",
                "4": "Danio",
                "5": "Otro"
            }
            if tipo_option not in tipo_map:
                print("❌ Error: Opción inválida")
                continue
            claim_data['tipo'] = tipo_map[tipo_option]
            
            # Get date
            fecha = input("Fecha del siniestro (DD/MM/YYYY) (*): ").strip()
            claim_data['fecha'] = fecha
            
            # Get estimated amount
            try:
                claim_data['monto_estimado'] = float(input("Monto estimado (*): "))
            except ValueError:
                print("❌ Error: Monto debe ser un número")
                continue
            
            # Get status
            print("\nEstado del siniestro:")
            print("1. Abierto")
            print("2. En Proceso")
            print("3. Cerrado")
            print("4. Rechazado")
            estado_option = input("Seleccione el estado (1-4, por defecto 1-Abierto): ").strip() or "1"
            estado_map = {
                "1": "Abierto",
                "2": "En Proceso",
                "3": "Cerrado",
                "4": "Rechazado"
            }
            if estado_option not in estado_map:
                print("❌ Error: Opción inválida")
                continue
            claim_data['estado'] = estado_map[estado_option]
            
            # Get description (optional)
            descripcion = input("Descripción (opcional): ").strip()
            if descripcion:
                claim_data['descripcion'] = descripcion
            
            # Confirm
            print("\n--- DATOS DEL SINIESTRO A CREAR ---")
            print(f"Póliza: {claim_data['nro_poliza']}")
            print(f"ID Siniestro: {claim_data['id_siniestro']}")
            print(f"Tipo: {claim_data['tipo']}")
            print(f"Fecha: {claim_data['fecha']}")
            print(f"Monto estimado: ${claim_data['monto_estimado']}")
            print(f"Estado: {claim_data['estado']}")
            if 'descripcion' in claim_data:
                print(f"Descripción: {claim_data['descripcion']}")
            
            confirm = input("\n¿Confirmar creación? (S/n): ").strip().lower()
            if confirm != 'n':
                result = create_claim(claim_data)
                if 'error' in result:
                    print(f"\n❌ Error: {result['error']}")
                else:
                    print(f"\n✓ Siniestro creado exitosamente!")
        
        elif operation == "2":
            # GET CLAIMS BY POLICY
            print("\n--- CONSULTAR SINIESTROS DE UNA PÓLIZA ---")
            nro_poliza = input("Número de Póliza: ").strip()
            
            result = get_claims_by_policy(nro_poliza)
            if 'error' in result:
                print(f"\n❌ {result['error']}")
            else:
                print(f"\n--- SINIESTROS DE PÓLIZA {result['nro_poliza']} ---")
                print(f"Cliente: {result['cliente']}")
                print(f"Total de siniestros: {len(result['siniestros'])}")
                
                if result['siniestros']:
                    print("\nDetalle:")
                    for s in result['siniestros']:
                        print(f"\n  ID: {s.get('id_siniestro')}")
                        print(f"  Tipo: {s.get('tipo')}")
                        print(f"  Fecha: {s.get('fecha')}")
                        print(f"  Monto estimado: ${s.get('monto_estimado')}")
                        print(f"  Estado: {s.get('estado')}")
                        if s.get('descripcion'):
                            print(f"  Descripción: {s.get('descripcion')}")
                        if s.get('monto_final'):
                            print(f"  Monto final: ${s.get('monto_final')}")
                        if s.get('fecha_resolucion'):
                            print(f"  Fecha resolución: {s.get('fecha_resolucion')}")
                else:
                    print("\n  No hay siniestros registrados para esta póliza.")
        
        elif operation == "3":
            # UPDATE CLAIM STATUS
            print("\n--- ACTUALIZAR ESTADO DE SINIESTRO ---")
            nro_poliza = input("Número de Póliza: ").strip()
            
            try:
                id_siniestro = int(input("ID del Siniestro: "))
            except ValueError:
                print("❌ Error: ID debe ser un número")
                continue
            
            print("\nNuevo estado:")
            print("1. Abierto")
            print("2. En Proceso")
            print("3. Cerrado")
            print("4. Rechazado")
            estado_option = input("Seleccione el nuevo estado (1-4): ").strip()
            estado_map = {
                "1": "Abierto",
                "2": "En Proceso",
                "3": "Cerrado",
                "4": "Rechazado"
            }
            if estado_option not in estado_map:
                print("❌ Error: Opción inválida")
                continue
            nuevo_estado = estado_map[estado_option]
            
            # Optional: monto final
            monto_final = None
            monto_input = input("Monto final (opcional, Enter para omitir): ").strip()
            if monto_input:
                try:
                    monto_final = float(monto_input)
                except ValueError:
                    print("❌ Error: Monto debe ser un número")
                    continue
            
            # Optional: fecha resolución
            fecha_resolucion = None
            fecha_input = input("Fecha resolución (DD/MM/YYYY, opcional, Enter para omitir): ").strip()
            if fecha_input:
                fecha_resolucion = fecha_input
            
            # Confirm
            print("\n--- ACTUALIZACIÓN A REALIZAR ---")
            print(f"Póliza: {nro_poliza}")
            print(f"ID Siniestro: {id_siniestro}")
            print(f"Nuevo estado: {nuevo_estado}")
            if monto_final:
                print(f"Monto final: ${monto_final}")
            if fecha_resolucion:
                print(f"Fecha resolución: {fecha_resolucion}")
            
            confirm = input("\n¿Confirmar actualización? (S/n): ").strip().lower()
            if confirm != 'n':
                result = update_claim_status(
                    nro_poliza=nro_poliza,
                    id_siniestro=id_siniestro,
                    nuevo_estado=nuevo_estado,
                    monto_final=monto_final,
                    fecha_resolucion=fecha_resolucion
                )
                if 'error' in result:
                    print(f"\n❌ Error: {result['error']}")
                else:
                    print(f"\n✓ Siniestro actualizado exitosamente!")
        
        elif operation == "4":
            print("\n¡Hasta luego!")
            break
        
        else:
            print("\n❌ Opción inválida. Por favor seleccione 1-4.")


if __name__ == "__main__":
    interactive_abm()
