import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import invalidate_cache_pattern
from datetime import datetime


def create_claim(claim_data):
    """
    Create a new claim (siniestro) and add it to the corresponding policy
    
    Args:
        claim_data: Dictionary with claim information
        Required fields: nro_poliza, id_siniestro, tipo, fecha, monto_estimado, estado
        Optional fields: descripcion, monto_final, fecha_resolucion
    
    Returns:
        Success message or error
    """
    collection = get_mongo_collection()
    
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
    valid_types = ['Accidente', 'Robo', 'Incendio', 'Granizo', 'Otro']
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


# Example usage and testing
if __name__ == "__main__":
    print("=== Gestión de Siniestros (Alta de Siniestros) ===\n")
    
    # Test 1: Create a new claim
    print("1. Creando un nuevo siniestro...")
    new_claim = {
        "nro_poliza": 1,  # Make sure this policy exists in your data
        "id_siniestro": 99999,
        "tipo": "Accidente",
        "fecha": "12/11/2025",
        "monto_estimado": 50000.00,
        "estado": "Abierto",
        "descripcion": "Accidente de prueba - colisión frontal"
    }
    result = create_claim(new_claim)
    print(result)
    print()
    
    # Test 2: Get all claims for a policy
    print("2. Obteniendo todos los siniestros para póliza 1...")
    claims = get_claims_by_policy(1)
    if 'error' not in claims:
        print(f"Póliza {claims['nro_poliza']} - Cliente: {claims['cliente']}")
        print(f"Total siniestros: {len(claims['siniestros'])}")
    print()
    
    # Test 3: Update claim status
    print("3. Actualizando estado del siniestro...")
    update_result = update_claim_status(
        nro_poliza=1,
        id_siniestro=99999,
        nuevo_estado="En Proceso",
        monto_final=48000.00
    )
    print(update_result)
    print()
    
    # Note: To clean up, you would need to manually remove the test claim from the database
    print("Nota: Siniestro de prueba creado. Eliminar manualmente si es necesario.")
