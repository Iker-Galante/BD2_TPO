import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import get_mongo_collection
from app.cache import invalidate_cache_pattern
from datetime import datetime, timedelta


def get_next_policy_number():
    """
    Get the next available policy number in format POLxxxx
    Starting from POL1161 and incrementing
    
    Returns:
        Next policy number as string
    """
    collection = get_mongo_collection()
    
    # Find all policy numbers that match the POLxxxx pattern
    pipeline = [
        {"$unwind": "$polizas"},
        {"$match": {"polizas.nro_poliza": {"$regex": "^POL\\d+$"}}},
        {"$project": {
            "nro_poliza": "$polizas.nro_poliza",
            "policy_number": {
                "$toInt": {"$substr": ["$polizas.nro_poliza", 3, -1]}
            }
        }},
        {"$sort": {"policy_number": -1}},
        {"$limit": 1}
    ]
    
    result = list(collection.aggregate(pipeline))
    
    if result:
        last_number = result[0]['policy_number']
        next_number = last_number + 1
    else:
        # No policies found, start from 1161
        next_number = 1161
    
    return f"POL{next_number}"


def issue_new_policy(policy_data):
    """
    Issue a new policy with validation of client and agent
    
    Args:
        policy_data: Dictionary with policy information
        Required fields: dni_cliente, tipo, fecha_inicio, fecha_fin, 
                        prima_mensual, cobertura_total, matricula_agente, estado
        Optional fields: deducible, nro_poliza (auto-generated if not provided)
    
    Returns:
        Success message or error
    """
    collection = get_mongo_collection()
    
    required_fields = ['dni_cliente', 'tipo', 'fecha_inicio', 
                      'fecha_fin', 'prima_mensual', 'cobertura_total', 'matricula_agente', 'estado']
    for field in required_fields:
        if field not in policy_data:
            return {"error": f"Missing required field: {field}"}
    
    dni_cliente = policy_data['dni_cliente']
    matricula_agente = policy_data['matricula_agente']
    
    # Auto-generate policy number if not provided
    if 'nro_poliza' not in policy_data or not policy_data['nro_poliza']:
        nro_poliza = get_next_policy_number()
        policy_data['nro_poliza'] = nro_poliza
    else:
        nro_poliza = policy_data['nro_poliza']
    
    # 1. Validate client exists and is active
    client = collection.find_one({
        "dni": dni_cliente,
        "nombre": {"$exists": True}
    })
    
    if not client:
        return {"error": f"Client with DNI {dni_cliente} not found"}
    
    if not client.get('activo', False):
        return {"error": f"Client with DNI {dni_cliente} is not active. Cannot issue policy."}
    
    id_cliente = client['id_cliente']
    
    # 2. Validate agent exists and is active
    agent_exists = collection.find_one({
        "polizas.agente.matricula": matricula_agente,
        "polizas.agente.activo": True
    })
    
    if not agent_exists:
        # Try to find agent in any policy (even if not active)
        any_agent = collection.find_one({
            "polizas.agente.matricula": matricula_agente
        })
        
        if not any_agent:
            return {"error": f"Agent with matricula {matricula_agente} not found"}
        else:
            # Agent exists but is not active
            return {"error": f"Agent with matricula {matricula_agente} is not active. Cannot issue policy."}
    
    # Get id_agente from the found agent
    id_agente = agent_exists['polizas'][0]['id_agente']
    
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
    
    # 8. Get agent information from existing policies using matricula
    agent_info = collection.find_one(
        {"polizas.agente.matricula": matricula_agente},
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
            print(f"✓ Póliza {nro_poliza} emitida exitosamente para cliente DNI {dni_cliente} (ID: {id_cliente})")
            print(f"  Tipo: {policy_data['tipo']}")
            print(f"  Período: {policy_data['fecha_inicio']} - {policy_data['fecha_fin']}")
            print(f"  Prima mensual: ${prima_mensual}")
            print(f"  Cobertura total: ${cobertura_total}")
            print(f"  Agente matricula: {matricula_agente} (ID: {id_agente})")
            
            # Invalidate policy-related caches
            invalidate_cache_pattern("query4:*")  # Clients without active policies
            invalidate_cache_pattern("query5:*")  # Agents with policy count
            invalidate_cache_pattern("query7:*")  # Top clients by coverage
            invalidate_cache_pattern("query9:*")  # Active policies view
            print("✓ Caché invalidado")
            
            return {
                "success": True,
                "nro_poliza": nro_poliza,
                "dni_cliente": dni_cliente,
                "id_cliente": id_cliente,
                "matricula_agente": matricula_agente,
                "id_agente": id_agente,
                "message": "Policy issued successfully"
            }
        else:
            return {"error": "Failed to issue policy"}
    except Exception as e:
        return {"error": f"Error issuing policy: {str(e)}"}


def validate_policy_requirements(dni_cliente, tipo_poliza):
    """
    Validate specific requirements for policy types
    
    Args:
        dni_cliente: Client DNI
        tipo_poliza: Policy type (Auto, Hogar, etc.)
    
    Returns:
        Validation result with requirements met/missing
    """
    collection = get_mongo_collection()
    
    client = collection.find_one({"dni": dni_cliente})
    
    if not client:
        return {"error": f"Client with DNI {dni_cliente} not found"}
    
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
        "dni_cliente": dni_cliente,
        "id_cliente": client['id_cliente'],
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
            "matricula": {"$first": "$polizas.agente.matricula"},
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
        print(f"  - Agente {agent.get('matricula')}: {agent.get('nombre')} {agent.get('apellido')} - {agent['policy_count']} pólizas")
    
    return agents


def interactive_issue_policy():
    """
    Interactive function to issue a new policy with user input
    """
    print("=== Emisión de Nueva Póliza ===\n")
    
    try:
        # Step 1: Get client DNI
        print("1. INFORMACIÓN DEL CLIENTE")
        dni_cliente = input("Ingrese DNI del cliente: ").strip()
        if not dni_cliente.isdigit():
            print("❌ Error: El DNI debe ser numérico")
            return
        dni_cliente = int(dni_cliente)
        
        # Validate client exists
        collection = get_mongo_collection()
        client = collection.find_one({"dni": dni_cliente})
        if not client:
            print(f"❌ Error: No se encontró cliente con DNI {dni_cliente}")
            return
        
        print(f"✓ Cliente encontrado: {client.get('nombre')} {client.get('apellido')}")
        
        if not client.get('activo', False):
            print(f"❌ Error: El cliente no está activo")
            return
        print(f"✓ Cliente activo\n")
        
        # Step 2: Select policy type and validate requirements
        print("2. TIPO DE PÓLIZA")
        print("Tipos disponibles: Auto, Hogar, Vida, Salud, Comercio")
        tipo = input("Ingrese tipo de póliza: ").strip()
        
        if tipo not in ['Auto', 'Hogar', 'Vida', 'Salud', 'Comercio']:
            print(f"❌ Error: Tipo de póliza inválido")
            return
        
        # Validate requirements
        validation = validate_policy_requirements(dni_cliente, tipo)
        if not validation.get('all_requirements_met', False):
            print(f"⚠ Advertencia: No se cumplen todos los requisitos:")
            for req, met in validation['requirements'].items():
                status = "✓" if met else "✗"
                print(f"  {status} {req}: {met}")
            
            confirm = input("\n¿Desea continuar de todos modos? (s/n): ").strip().lower()
            if confirm != 's':
                print("Emisión cancelada")
                return
        print(f"✓ Tipo: {tipo}\n")
        
        # Step 3: Get agent matricula
        print("3. AGENTE")
        print("\nAgentes activos disponibles:")
        agents = get_available_agents()
        print()
        
        matricula_agente = input("Ingrese matrícula del agente: ").strip()
        
        # Validate agent exists and is active
        agent_exists = collection.find_one({
            "polizas.agente.matricula": matricula_agente,
            "polizas.agente.activo": True
        })
        
        if not agent_exists:
            print(f"❌ Error: No se encontró agente activo con matrícula {matricula_agente}")
            return
        
        agent_name = agent_exists['polizas'][0]['agente'].get('nombre', '')
        agent_lastname = agent_exists['polizas'][0]['agente'].get('apellido', '')
        print(f"✓ Agente encontrado: {agent_name} {agent_lastname}\n")
        
        # Step 4: Get policy details
        print("4. DETALLES DE LA PÓLIZA")
        
        # Auto-generate policy number
        nro_poliza = get_next_policy_number()
        print(f"✓ Número de póliza auto-generado: {nro_poliza}\n")
        
        # Get dates
        print("\nFechas (formato DD/MM/YYYY):")
        fecha_inicio = input("Fecha de inicio: ").strip()
        fecha_fin = input("Fecha de fin: ").strip()
        
        # Validate date format
        try:
            datetime.strptime(fecha_inicio, "%d/%m/%Y")
            datetime.strptime(fecha_fin, "%d/%m/%Y")
        except ValueError:
            print("❌ Error: Formato de fecha inválido. Use DD/MM/YYYY")
            return
        
        # Get amounts
        print("\nMontos:")
        prima_mensual = input("Prima mensual: $").strip()
        cobertura_total = input("Cobertura total: $").strip()
        
        try:
            prima_mensual = float(prima_mensual)
            cobertura_total = float(cobertura_total)
            
            if prima_mensual <= 0 or cobertura_total <= 0:
                print("❌ Error: Los montos deben ser mayores a 0")
                return
        except ValueError:
            print("❌ Error: Los montos deben ser numéricos")
            return
        
        
        # Estado
        print("\nEstados disponibles: Activa, Suspendida, Vencida, Cancelada")
        estado = input("Estado de la póliza: ").strip()
        
        if estado not in ['Activa', 'Suspendida', 'Vencida', 'Cancelada']:
            print("❌ Error: Estado inválido")
            return
        
        # Step 5: Confirm and create policy
        print("\n" + "="*60)
        print("RESUMEN DE LA PÓLIZA")
        print("="*60)
        print(f"Cliente: {client.get('nombre')} {client.get('apellido')} (DNI: {dni_cliente})")
        print(f"Agente: {agent_name} {agent_lastname} (Matrícula: {matricula_agente})")
        print(f"Póliza Nº: {nro_poliza}")
        print(f"Tipo: {tipo}")
        print(f"Período: {fecha_inicio} - {fecha_fin}")
        print(f"Prima mensual: ${prima_mensual:,.2f}")
        print(f"Cobertura total: ${cobertura_total:,.2f}")
        if deducible:
            print(f"Deducible: ${deducible:,.2f}")
        print(f"Estado: {estado}")
        print("="*60)
        
        confirm = input("\n¿Confirma la emisión de esta póliza? (s/n): ").strip().lower()
        
        if confirm != 's':
            print("\n❌ Emisión cancelada por el usuario")
            return
        
        # Create policy data
        policy_data = {
            "dni_cliente": dni_cliente,
            "nro_poliza": nro_poliza,
            "tipo": tipo,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "prima_mensual": prima_mensual,
            "cobertura_total": cobertura_total,
            "matricula_agente": matricula_agente,
            "estado": estado
        }
        
        if deducible:
            policy_data["deducible"] = deducible
        
        # Issue the policy
        print("\nEmitiendo póliza...")
        result = issue_new_policy(policy_data)
        
        if result.get('success'):
            print("\n" + "="*60)
            print("✓ ¡PÓLIZA EMITIDA EXITOSAMENTE!")
            print("="*60)
        else:
            print(f"\n❌ Error al emitir póliza: {result.get('error', 'Error desconocido')}")
    
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")


# Example usage and testing
if __name__ == "__main__":
    print("=== Sistema de Emisión de Pólizas ===\n")
    print("Opciones:")
    print("1. Emisión interactiva de póliza")
    print("2. Ver agentes disponibles")

    opcion = input("\nSeleccione una opción (1-2): ").strip()
    print()
    
    if opcion == "1":
        interactive_issue_policy()
    
    elif opcion == "2":
        print("=== Agentes Disponibles ===\n")
        agents = get_available_agents()
        for agent in agents:
            print(f"{agent.get('nombre')} {agent.get('apellido')} - Matrícula: {agent.get('matricula')}")
    
    else:
        print("Opción inválida")
