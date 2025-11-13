import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import invalidate_cache_pattern
from datetime import datetime, timedelta


def issue_new_policy(policy_data):
    """
    Issue a new policy with validation of client and agent
    
    Args:
        policy_data: Dictionary with policy information
        Required fields: id_cliente, nro_poliza, tipo, fecha_inicio, fecha_fin, 
                        prima_mensual, cobertura_total, id_agente, estado
        Optional fields: deducible
    
    Returns:
        Success message or error
    """
    collection = get_mongo_collection()
    
    # Validate required fields
    required_fields = ['id_cliente', 'nro_poliza', 'tipo', 'fecha_inicio', 
                      'fecha_fin', 'prima_mensual', 'cobertura_total', 'id_agente', 'estado']
    for field in required_fields:
        if field not in policy_data:
            return {"error": f"Missing required field: {field}"}
    
    id_cliente = policy_data['id_cliente']
    nro_poliza = policy_data['nro_poliza']
    id_agente = policy_data['id_agente']
    
    # 1. Validate client exists and is active
    client = collection.find_one({
        "id_cliente": id_cliente,
        "nombre": {"$exists": True}
    })
    
    if not client:
        return {"error": f"Client with id_cliente {id_cliente} not found"}
    
    if not client.get('activo', False):
        return {"error": f"Client {id_cliente} is not active. Cannot issue policy."}
    
    # 2. Validate agent exists and is active
    agent_exists = collection.find_one({
        "polizas.agente.id_agente": id_agente,
        "polizas.agente.activo": True
    })
    
    if not agent_exists:
        # Try to find agent in any policy (even if not active)
        any_agent = collection.find_one({
            "polizas.id_agente": id_agente
        })
        
        if not any_agent:
            return {"error": f"Agent with id_agente {id_agente} not found"}
        else:
            # Agent exists but is not active
            return {"error": f"Agent {id_agente} is not active. Cannot issue policy."}
    
    # 3. Check if policy number already exists
    existing_policy = collection.find_one({
        "polizas.nro_poliza": nro_poliza
    })
    
    if existing_policy:
        return {"error": f"Policy number {nro_poliza} already exists"}
    
    # 4. Validate policy type
    valid_types = ['Auto', 'Hogar', 'Vida', 'Salud', 'Comercio']
    if policy_data['tipo'] not in valid_types:
        return {"error": f"Invalid policy type. Must be one of: {', '.join(valid_types)}"}
    
    # 5. Validate estado
    valid_estados = ['Activa', 'Suspendida', 'Vencida', 'Cancelada']
    if policy_data['estado'] not in valid_estados:
        return {"error": f"Invalid estado. Must be one of: {', '.join(valid_estados)}"}
    
    # 6. Validate dates
    try:
        fecha_inicio = datetime.strptime(policy_data['fecha_inicio'], "%d/%m/%Y")
        fecha_fin = datetime.strptime(policy_data['fecha_fin'], "%d/%m/%Y")
    except ValueError:
        return {"error": "Invalid date format. Use DD/MM/YYYY"}
    
    if fecha_fin <= fecha_inicio:
        return {"error": "End date must be after start date"}
    
    # 7. Validate numeric fields
    try:
        prima_mensual = float(policy_data['prima_mensual'])
        cobertura_total = float(policy_data['cobertura_total'])
        
        if prima_mensual <= 0:
            return {"error": "Prima mensual must be greater than 0"}
        if cobertura_total <= 0:
            return {"error": "Cobertura total must be greater than 0"}
    except (TypeError, ValueError):
        return {"error": "Prima mensual and cobertura total must be valid numbers"}
    
    # 8. Get agent information from existing policies
    agent_info = collection.find_one(
        {"polizas.id_agente": id_agente},
        {"polizas.$": 1}
    )
    
    agente_data = {}
    if agent_info and 'polizas' in agent_info and len(agent_info['polizas']) > 0:
        agente_data = agent_info['polizas'][0].get('agente', {})
    
    # 9. Prepare policy record
    policy_record = {
        "nro_poliza": nro_poliza,
        "tipo": policy_data['tipo'],
        "fecha_inicio": policy_data['fecha_inicio'],
        "fecha_fin": policy_data['fecha_fin'],
        "prima_mensual": prima_mensual,
        "cobertura_total": cobertura_total,
        "id_agente": id_agente,
        "agente": agente_data,
        "estado": policy_data['estado'],
        "siniestros": []
    }
    
    if 'deducible' in policy_data:
        policy_record['deducible'] = policy_data['deducible']
    
    # 10. Insert policy into client's polizas array
    try:
        result = collection.update_one(
            {"id_cliente": id_cliente},
            {"$push": {"polizas": policy_record}}
        )
        
        if result.modified_count > 0:
            print(f"✓ Póliza {nro_poliza} emitida exitosamente para cliente {id_cliente}")
            print(f"  Tipo: {policy_data['tipo']}")
            print(f"  Período: {policy_data['fecha_inicio']} - {policy_data['fecha_fin']}")
            print(f"  Prima mensual: ${prima_mensual}")
            print(f"  Cobertura total: ${cobertura_total}")
            print(f"  Agente: {id_agente}")
            
            # Invalidate policy-related caches
            invalidate_cache_pattern("query4:*")  # Clients without active policies
            invalidate_cache_pattern("query5:*")  # Agents with policy count
            invalidate_cache_pattern("query7:*")  # Top clients by coverage
            invalidate_cache_pattern("query9:*")  # Active policies view
            print("✓ Caché invalidado")
            
            return {
                "success": True,
                "nro_poliza": nro_poliza,
                "id_cliente": id_cliente,
                "id_agente": id_agente,
                "message": "Policy issued successfully"
            }
        else:
            return {"error": "Failed to issue policy"}
    except Exception as e:
        return {"error": f"Error issuing policy: {str(e)}"}


def validate_policy_requirements(id_cliente, tipo_poliza):
    """
    Validate specific requirements for policy types
    
    Args:
        id_cliente: Client ID
        tipo_poliza: Policy type (Auto, Hogar, etc.)
    
    Returns:
        Validation result with requirements met/missing
    """
    collection = get_mongo_collection()
    
    client = collection.find_one({"id_cliente": id_cliente})
    
    if not client:
        return {"error": f"Client {id_cliente} not found"}
    
    requirements = {
        "client_active": client.get('activo', False),
        "has_email": bool(client.get('email')),
        "has_dni": bool(client.get('dni'))
    }
    
    if tipo_poliza == "Auto":
        # For Auto policies, client should have vehicles
        vehiculos = client.get('vehiculos', [])
        requirements['has_vehicles'] = len(vehiculos) > 0
        requirements['vehicle_count'] = len(vehiculos)
    
    all_met = all(requirements.values()) if tipo_poliza == "Auto" else \
              requirements['client_active'] and requirements['has_email'] and requirements['has_dni']
    
    return {
        "id_cliente": id_cliente,
        "tipo_poliza": tipo_poliza,
        "requirements": requirements,
        "all_requirements_met": all_met
    }


def get_available_agents():
    """
    Get list of active agents available for policy assignment
    
    Returns:
        List of active agents
    """
    collection = get_mongo_collection()
    
    # Find all active agents
    pipeline = [
        {"$unwind": "$polizas"},
        {"$match": {"polizas.agente.activo": True}},
        {"$group": {
            "_id": "$polizas.id_agente",
            "nombre": {"$first": "$polizas.agente.nombre"},
            "apellido": {"$first": "$polizas.agente.apellido"},
            "email": {"$first": "$polizas.agente.email"},
            "telefono": {"$first": "$polizas.agente.telefono"},
            "policy_count": {"$sum": 1}
        }},
        {"$sort": {"policy_count": 1}}  # Show agents with fewer policies first
    ]
    
    agents = list(collection.aggregate(pipeline))
    
    print(f"Se encontraron {len(agents)} agentes activos:")
    for agent in agents:
        print(f"  - Agente {agent['_id']}: {agent.get('nombre')} {agent.get('apellido')} - {agent['policy_count']} pólizas")
    
    return agents


# Example usage and testing
if __name__ == "__main__":
    print("=== Emisión de Pólizas ===\n")
    
    # Test 1: Get available agents
    print("1. Obteniendo agentes disponibles...")
    agents = get_available_agents()
    print()
    
    # Test 2: Validate requirements for a client
    print("2. Validando requisitos de póliza para cliente 1...")
    validation = validate_policy_requirements(1, "Auto")
    print(validation)
    print()
    
    # Test 3: Issue a new policy
    print("3. Emitiendo una nueva póliza...")
    
    # Calculate dates
    today = datetime.now()
    one_year_later = today + timedelta(days=365)
    
    new_policy = {
        "id_cliente": 1,  # Make sure this client exists
        "nro_poliza": 99999,
        "tipo": "Auto",
        "fecha_inicio": today.strftime("%d/%m/%Y"),
        "fecha_fin": one_year_later.strftime("%d/%m/%Y"),
        "prima_mensual": 5000.00,
        "cobertura_total": 500000.00,
        "deducible": 10000.00,
        "id_agente": 1,  # Make sure this agent exists and is active
        "estado": "Activa"
    }
    
    result = issue_new_policy(new_policy)
    print(result)
    print()
    
    # Note: To clean up, you would need to manually remove the test policy from the database
    print("Nota: Póliza de prueba creada. Eliminar manualmente si es necesario.")
