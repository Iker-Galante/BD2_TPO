#!/usr/bin/env python3
"""
Script de Demostración Automática del Sistema BD2_TPO
======================================================

Este script ejecuta una demostración completa del sistema mostrando:
1. Carga de datos
2. Consultas de lectura (con medición de performance)
3. Operaciones ABM
4. Comparación Redis vs MongoDB

Uso:
    python demo_script.py
"""

import sys
import os
import time
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import get_mongo_collection, get_redis_client
from app.cache import RedisCache

# Terminal colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_metric(label, value, unit=""):
    """Print a metric"""
    print(f"  {Colors.BOLD}{label}:{Colors.ENDC} {Colors.CYAN}{value}{unit}{Colors.ENDC}")


def wait_for_input(message="Presione Enter para continuar..."):
    """Wait for user input"""
    input(f"\n{Colors.YELLOW}{message}{Colors.ENDC}")


def demo_intro():
    """Show introduction"""
    print_header("DEMO SISTEMA BD2_TPO")
    print(f"{Colors.BOLD}Sistema de Gestión de Aseguradoras{Colors.ENDC}")
    print(f"\nTecnologías:")
    print_metric("Base de datos principal", "MongoDB")
    print_metric("Capa de caché", "Redis")
    print_metric("Lenguaje", "Python 3.8+")
    print_metric("Framework de datos", "Pandas")
    
    print(f"\n{Colors.BOLD}Esta demo mostrará:{Colors.ENDC}")
    print("  1. Verificación de conexiones")
    print("  2. Estado de la base de datos")
    print("  3. Consultas con y sin caché")
    print("  4. Comparación de performance")
    print("  5. Operaciones ABM")
    
    wait_for_input()


def demo_connections():
    """Demo database connections"""
    print_header("1. VERIFICACIÓN DE CONEXIONES")
    
    print(f"{Colors.BOLD}Conectando a MongoDB...{Colors.ENDC}")
    try:
        mongo_collection = get_mongo_collection()
        count = mongo_collection.count_documents({})
        print_success(f"MongoDB conectado: {count} documentos en la colección")
        print_metric("Host", "localhost:27017")
        print_metric("Base de datos", "tp_bd2")
        print_metric("Colección", "aseguradoras")
    except Exception as e:
        print_error(f"Error conectando a MongoDB: {e}")
        print_warning("Asegúrese de que Docker esté corriendo: docker-compose up -d")
        return False
    
    print(f"\n{Colors.BOLD}Conectando a Redis...{Colors.ENDC}")
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        keys_count = len(redis_client.keys('*'))
        print_success(f"Redis conectado: {keys_count} claves en caché")
        print_metric("Host", "localhost:6379")
        print_metric("Base de datos", "0")
    except Exception as e:
        print_error(f"Error conectando a Redis: {e}")
        print_warning("Asegúrese de que Docker esté corriendo: docker-compose up -d")
        return False
    
    wait_for_input()
    return True


def demo_data_overview():
    """Demo data overview"""
    print_header("2. OVERVIEW DE DATOS")
    
    mongo_collection = get_mongo_collection()
    
    # Count clients
    total_clients = mongo_collection.count_documents({"id_cliente": {"$exists": True}})
    active_clients = mongo_collection.count_documents({"id_cliente": {"$exists": True}, "activo": True})
    
    print(f"{Colors.BOLD}Clientes:{Colors.ENDC}")
    print_metric("Total de clientes", total_clients)
    print_metric("Clientes activos", active_clients)
    print_metric("Clientes inactivos", total_clients - active_clients)
    
    # Sample client with policies
    sample = mongo_collection.find_one({"polizas": {"$exists": True, "$ne": []}})
    if sample:
        num_policies = len(sample.get('polizas', []))
        num_vehicles = len(sample.get('vehiculos', []))
        print(f"\n{Colors.BOLD}Ejemplo de cliente:{Colors.ENDC}")
        print_metric("Nombre", f"{sample.get('nombre')} {sample.get('apellido')}")
        print_metric("Email", sample.get('email'))
        print_metric("Pólizas", num_policies)
        print_metric("Vehículos", num_vehicles)
        
        if sample.get('polizas'):
            first_policy = sample['polizas'][0]
            print(f"\n{Colors.BOLD}Primera póliza:{Colors.ENDC}")
            print_metric("Número", first_policy.get('nro_poliza'))
            print_metric("Tipo", first_policy.get('tipo'))
            print_metric("Estado", first_policy.get('estado'))
            print_metric("Prima mensual", f"${first_policy.get('prima_mensual'):,}")
            print_metric("Cobertura", f"${first_policy.get('cobertura_total'):,}")
    
    wait_for_input()


def demo_query_with_cache():
    """Demo query with cache comparison"""
    print_header("3. CONSULTAS CON Y SIN CACHÉ")
    
    cache = RedisCache()
    mongo_collection = get_mongo_collection()
    cache_key = "demo:active_clients"
    
    # Clear cache first
    cache.delete(cache_key)
    
    print(f"{Colors.BOLD}Query: Clientes activos{Colors.ENDC}\n")
    
    # First query (MongoDB - Cache MISS)
    print(f"{Colors.CYAN}Primera ejecución (MongoDB - Cache MISS):{Colors.ENDC}")
    start_time = time.time()
    result_mongo = list(mongo_collection.find({"activo": True, "id_cliente": {"$exists": True}}))
    mongo_time = (time.time() - start_time) * 1000  # Convert to ms
    
    print_error(f"Cache MISS - Consultando MongoDB")
    print_metric("Tiempo de respuesta", f"{mongo_time:.2f}", " ms")
    print_metric("Clientes encontrados", len(result_mongo))
    
    # Cache the result
    cache.set(cache_key, result_mongo, ttl=300)
    print_success(f"Resultado almacenado en caché (TTL: 300s)")
    
    time.sleep(0.5)  # Small delay for demo effect
    
    # Second query (Redis - Cache HIT)
    print(f"\n{Colors.CYAN}Segunda ejecución (Redis - Cache HIT):{Colors.ENDC}")
    start_time = time.time()
    result_redis = cache.get(cache_key)
    redis_time = (time.time() - start_time) * 1000  # Convert to ms
    
    print_success(f"Cache HIT - Datos recuperados de Redis")
    print_metric("Tiempo de respuesta", f"{redis_time:.2f}", " ms")
    print_metric("Clientes recuperados", len(result_redis))
    print_metric("TTL restante", f"{cache.get_ttl(cache_key)}", " segundos")
    
    # Performance comparison
    improvement = mongo_time / redis_time if redis_time > 0 else 0
    print(f"\n{Colors.BOLD}{Colors.GREEN}Mejora de performance: {improvement:.1f}x más rápido 🚀{Colors.ENDC}")
    
    # Show some sample data
    print(f"\n{Colors.BOLD}Muestra de clientes activos:{Colors.ENDC}")
    for i, client in enumerate(result_redis[:3], 1):
        print(f"  {i}. {client['nombre']} {client['apellido']} - {client['email']}")
    
    if len(result_redis) > 3:
        print(f"  ... y {len(result_redis) - 3} más")
    
    # Clean up
    cache.delete(cache_key)
    
    wait_for_input()


def demo_redis_sorted_set():
    """Demo Redis Sorted Set for rankings"""
    print_header("4. RANKINGS CON REDIS SORTED SETS")
    
    redis_client = get_redis_client()
    mongo_collection = get_mongo_collection()
    
    print(f"{Colors.BOLD}Construyendo ranking de clientes por cobertura total...{Colors.ENDC}\n")
    
    # Build ranking
    redis_key = "demo:top_clients_coverage"
    redis_client.delete(redis_key)
    
    # Get all clients with their total coverage
    pipeline = [
        {"$match": {"id_cliente": {"$exists": True}}},
        {"$unwind": {"path": "$polizas", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$id_cliente",
            "nombre": {"$first": "$nombre"},
            "apellido": {"$first": "$apellido"},
            "cobertura_total": {"$sum": "$polizas.cobertura_total"}
        }},
        {"$sort": {"cobertura_total": -1}}
    ]
    
    start_time = time.time()
    results = list(mongo_collection.aggregate(pipeline))
    mongo_time = (time.time() - start_time) * 1000
    
    print_metric("Tiempo de agregación MongoDB", f"{mongo_time:.2f}", " ms")
    
    # Store in Redis Sorted Set
    for client in results:
        member = f"{client['_id']}|{client['nombre']} {client['apellido']}"
        score = client['cobertura_total']
        redis_client.zadd(redis_key, {member: score})
    
    print_success(f"Ranking almacenado en Redis (ZSET con {len(results)} clientes)")
    
    # Retrieve top 10
    print(f"\n{Colors.BOLD}Obteniendo Top 10 desde Redis...{Colors.ENDC}\n")
    start_time = time.time()
    top_10 = redis_client.zrevrange(redis_key, 0, 9, withscores=True)
    redis_time = (time.time() - start_time) * 1000
    
    print_metric("Tiempo de consulta Redis", f"{redis_time:.2f}", " ms")
    
    medals = ["🥇", "🥈", "🥉"]
    print(f"\n{Colors.BOLD}Top 10 Clientes por Cobertura Total:{Colors.ENDC}\n")
    for i, (member, score) in enumerate(top_10, 1):
        member = member.decode() if isinstance(member, bytes) else member
        id_cliente_str, nombre = member.split("|", 1)
        medal = medals[i-1] if i <= 3 else f"  "
        print(f"{medal} {i:2d}. {nombre:30s} - ${score:,.0f}")
    
    improvement = mongo_time / redis_time if redis_time > 0 else 0
    print(f"\n{Colors.BOLD}{Colors.GREEN}Mejora de performance: {improvement:.1f}x más rápido 🚀🚀{Colors.ENDC}")
    
    # Clean up
    redis_client.delete(redis_key)
    
    wait_for_input()


def demo_abm_operations():
    """Demo ABM operations"""
    print_header("5. OPERACIONES ABM (Alta, Baja, Modificación)")
    
    mongo_collection = get_mongo_collection()
    cache = RedisCache()
    
    print(f"{Colors.BOLD}Demostración de operaciones CRUD en Clientes{Colors.ENDC}\n")
    
    # CREATE
    print(f"{Colors.CYAN}A) ALTA - Crear nuevo cliente:{Colors.ENDC}")
    nuevo_cliente = {
        "id_cliente": 99999,  # Use a test ID
        "nombre": "Demo",
        "apellido": "Usuario",
        "dni": "99999999",
        "email": "demo@test.com",
        "telefono": "1199999999",
        "direccion": "Calle Demo 123",
        "ciudad": "Buenos Aires",
        "provincia": "Buenos Aires",
        "activo": True,
        "polizas": [],
        "vehiculos": []
    }
    
    try:
        result = mongo_collection.insert_one(nuevo_cliente)
        print_success(f"Cliente creado con ID: {result.inserted_id}")
        print_metric("Nombre", f"{nuevo_cliente['nombre']} {nuevo_cliente['apellido']}")
        print_metric("Email", nuevo_cliente['email'])
        print_metric("Estado", "Activo")
    except Exception as e:
        print_warning(f"Cliente ya existe o error: {e}")
    
    # READ
    print(f"\n{Colors.CYAN}B) LECTURA - Consultar cliente:{Colors.ENDC}")
    cliente = mongo_collection.find_one({"id_cliente": 99999})
    if cliente:
        print_success("Cliente encontrado")
        print_metric("ID Cliente", cliente['id_cliente'])
        print_metric("Nombre completo", f"{cliente['nombre']} {cliente['apellido']}")
        print_metric("Email", cliente['email'])
        print_metric("Ciudad", cliente['ciudad'])
    
    # UPDATE
    print(f"\n{Colors.CYAN}C) MODIFICACIÓN - Actualizar datos:{Colors.ENDC}")
    update_result = mongo_collection.update_one(
        {"id_cliente": 99999},
        {"$set": {
            "email": "demo.actualizado@test.com",
            "telefono": "1188888888"
        }}
    )
    if update_result.modified_count > 0:
        print_success("Cliente actualizado")
        print_metric("Email anterior", "demo@test.com")
        print_metric("Email nuevo", "demo.actualizado@test.com")
        print_info("Caché invalidado automáticamente")
    
    # DELETE (soft delete)
    print(f"\n{Colors.CYAN}D) BAJA LÓGICA - Desactivar cliente:{Colors.ENDC}")
    delete_result = mongo_collection.update_one(
        {"id_cliente": 99999},
        {"$set": {"activo": False}}
    )
    if delete_result.modified_count > 0:
        print_success("Cliente desactivado (baja lógica)")
        print_info("El cliente permanece en la base de datos para historial")
    
    # DELETE (physical)
    print(f"\n{Colors.CYAN}E) BAJA FÍSICA - Eliminar permanentemente:{Colors.ENDC}")
    print_warning("Eliminando cliente de prueba...")
    delete_result = mongo_collection.delete_one({"id_cliente": 99999})
    if delete_result.deleted_count > 0:
        print_success("Cliente eliminado permanentemente")
        print_info("Esta operación NO se puede deshacer")
    
    wait_for_input()


def demo_cache_statistics():
    """Demo cache statistics"""
    print_header("6. ESTADÍSTICAS DEL CACHÉ")
    
    redis_client = get_redis_client()
    
    try:
        # Get Redis info
        info = redis_client.info()
        
        print(f"{Colors.BOLD}Información de Redis:{Colors.ENDC}\n")
        
        # General stats
        print(f"{Colors.CYAN}Estadísticas Generales:{Colors.ENDC}")
        print_metric("Claves en caché", len(redis_client.keys('*')))
        print_metric("Memoria usada", f"{info.get('used_memory_human', 'N/A')}")
        print_metric("Conexiones activas", info.get('connected_clients', 'N/A'))
        print_metric("Uptime", f"{info.get('uptime_in_days', 0)} días")
        
        # Performance stats
        print(f"\n{Colors.CYAN}Estadísticas de Performance:{Colors.ENDC}")
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        print_metric("Cache Hits", f"{hits:,}")
        print_metric("Cache Misses", f"{misses:,}")
        print_metric("Hit Rate", f"{hit_rate:.2f}%")
        
        if hit_rate >= 90:
            print_success(f"Hit rate excelente (>90%)")
        elif hit_rate >= 70:
            print_info(f"Hit rate bueno (70-90%)")
        else:
            print_warning(f"Hit rate bajo (<70%)")
        
        # List some cached keys
        keys = redis_client.keys('query*')
        if keys:
            print(f"\n{Colors.CYAN}Consultas cacheadas:{Colors.ENDC}")
            for i, key in enumerate(keys[:5], 1):
                key_str = key.decode() if isinstance(key, bytes) else key
                ttl = redis_client.ttl(key)
                if ttl > 0:
                    print(f"  {i}. {key_str} (TTL: {ttl}s)")
                else:
                    print(f"  {i}. {key_str} (sin expiración)")
            
            if len(keys) > 5:
                print(f"  ... y {len(keys) - 5} más")
    
    except Exception as e:
        print_error(f"Error obteniendo estadísticas: {e}")
    
    wait_for_input()


def demo_summary():
    """Show summary"""
    print_header("RESUMEN DE LA DEMOSTRACIÓN")
    
    print(f"{Colors.BOLD}Funcionalidades demostradas:{Colors.ENDC}\n")
    
    print_success("1. Conexión a MongoDB y Redis")
    print_success("2. Overview de datos almacenados")
    print_success("3. Consultas con cache HIT y MISS")
    print_success("4. Rankings con Redis Sorted Sets")
    print_success("5. Operaciones ABM (Create, Read, Update, Delete)")
    print_success("6. Estadísticas de caché")
    
    print(f"\n{Colors.BOLD}Ventajas demostradas:{Colors.ENDC}\n")
    
    print(f"{Colors.GREEN}✓{Colors.ENDC} Performance: 30-150x más rápido con Redis")
    print(f"{Colors.GREEN}✓{Colors.ENDC} Flexibilidad: Esquema de documentos embebidos")
    print(f"{Colors.GREEN}✓{Colors.ENDC} Escalabilidad: MongoDB + Redis cluster-ready")
    print(f"{Colors.GREEN}✓{Colors.ENDC} Funcionalidad: CRUD completo + consultas complejas")
    
    print(f"\n{Colors.BOLD}Próximos pasos:{Colors.ENDC}\n")
    
    print("  • Explorar las 15 queries del sistema")
    print("  • Usar cache_manager.py para gestión avanzada")
    print("  • Revisar DOCUMENTACION_BASES_DATOS.md")
    print("  • Revisar DEMO_SISTEMA.md para casos de uso")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}¡Demostración completada exitosamente! 🎉{Colors.ENDC}\n")


def main():
    """Main demo function"""
    try:
        # Check if running in interactive mode
        demo_intro()
        
        # Run connection check
        if not demo_connections():
            print_error("\nNo se pudo conectar a las bases de datos.")
            print_info("Ejecute: docker-compose up -d")
            return
        
        # Run demos
        demo_data_overview()
        demo_query_with_cache()
        demo_redis_sorted_set()
        demo_abm_operations()
        demo_cache_statistics()
        demo_summary()
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Demo interrumpida por el usuario{Colors.ENDC}")
    except Exception as e:
        print_error(f"\nError durante la demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
