# BD2 TPO - Sistema de Gestión de Aseguradoras

Sistema de gestión de una aseguradora implementado con MongoDB y Redis, que permite consultar información sobre clientes, pólizas, vehículos, agentes y siniestros.

## Características Principales

- **MongoDB**: Base de datos principal con documentos embebidos
- **Redis**: Capa de caché para optimización de consultas (30-100x más rápido)
- **Caching inteligente**: Invalidación automática al modificar datos
- **15 Consultas y servicios**: Desde lecturas simples hasta operaciones ABM completas
- **Cache Manager**: Herramienta para monitorear y gestionar el caché

## 🔧 Requisitos Previos

- Python 3.8 o superior
- Docker y Docker Compose
- Git (opcional)

## Instalación

### 1. Clonar el repositorio (si corresponde)

```bash
git clone <repository-url>
cd BD2_TPO
```

### 2. Crear entorno virtual

```powershell
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1
```

**Importante**: El entorno virtual debe estar activado (verás `(.venv)` en tu prompt) antes de instalar dependencias o ejecutar scripts.

### 3. Instalar dependencias de Python

```powershell
pip install -r requirements.txt
```

Las dependencias incluyen:
- `pymongo`: Cliente de MongoDB para Python
- `redis`: Cliente de Redis para Python
- `pandas`: Procesamiento de datos CSV

## Configuración del Proyecto

### 1. Iniciar contenedores de Docker

El proyecto utiliza MongoDB y Redis en contenedores Docker. Para iniciarlos:

```powershell
docker-compose up -d
```

Esto creará y ejecutará:
- **MongoDB** en `localhost:27017`
- **Redis** en `localhost:6379`

### 2. Verificar que los contenedores estén corriendo

```powershell
docker ps
```

Deberías ver dos contenedores: `my_mongo` y `my_redis`

### 3. Detener los contenedores (cuando termines)

```powershell
docker-compose down
```

## Carga de Datos

### Cargar datos desde los archivos CSV

Los datos iniciales se encuentran en la carpeta `resources/` con los siguientes archivos:
- `clientes.csv`
- `polizas.csv`
- `siniestros.csv`
- `agentes.csv`
- `vehiculos.csv`

Para cargar los datos en MongoDB:

```powershell
# Asegúrate de que el entorno virtual esté activado (.venv)
python app/main.py
```

Este script:
1. Limpia la colección existente
2. Carga los clientes
3. Asocia pólizas, siniestros, vehículos y agentes a cada cliente
4. Construye un índice en Redis con el top de clientes por cobertura total

## Consultas Disponibles

### Query 1: Clientes activos con sus pólizas vigentes

Recupera información de clientes activos en el sistema.

```powershell
python app/queries/query1.py
```

### Query 2: Siniestros abiertos con tipo, monto y cliente afectado

Lista todos los siniestros con estado "Abierto".

```powershell
python app/queries/query2.py
```

### Query 3: Vehículos asegurados con su cliente y póliza

Muestra vehículos que están asegurados junto con información del cliente y póliza.

```powershell
python app/queries/query3.py
```

### Query 4: Clientes sin pólizas activas

Encuentra clientes que no tienen ninguna póliza activa.

```powershell
python app/queries/query4.py
```

### Query 5: Agentes activos con cantidad de pólizas asignadas

Lista agentes activos y la cantidad de pólizas que tienen asignadas.

```powershell
python app/queries/query5.py
```

### Query 6: Pólizas vencidas con el nombre del cliente

Muestra pólizas que están vencidas junto con el cliente asociado.

```powershell
python app/queries/query6.py
```

### Query 7: Top 10 clientes por cobertura total

Utiliza Redis para obtener los 10 clientes con mayor cobertura total.

```powershell
python app/queries/query7.py
```

### Query 8: Siniestros tipo "Accidente" del último año

Filtra siniestros de tipo "Accidente" ocurridos en el último año.

```powershell
python app/queries/query8.py
```

### Query 9: Vista de pólizas activas ordenadas por fecha de inicio

Muestra todas las pólizas activas ordenadas cronológicamente.

```powershell
python app/queries/query9.py
```

### Query 10: Pólizas suspendidas con estado del cliente

Lista pólizas suspendidas junto con el estado del cliente (activo/inactivo).

```powershell
python app/queries/query10.py
```

### Query 11: Clientes con más de un vehículo asegurado

Identifica clientes que tienen múltiples vehículos asegurados.

```powershell
python app/queries/query11.py
```

### Query 12: Agentes y cantidad de siniestros asociados

Muestra agentes con el conteo de siniestros en sus pólizas.

```powershell
python app/queries/query12.py
```

## Servicios ABM

### Query 13: ABM (Alta, Baja, Modificación) de Clientes

Operaciones CRUD completas para gestión de clientes.

**Funciones disponibles:**
- `create_client(client_data)`: Crear un nuevo cliente
- `read_client(id_cliente)`: Leer información de un cliente
- `update_client(id_cliente, update_data)`: Actualizar datos de un cliente
- `delete_client(id_cliente, soft_delete=True)`: Eliminar cliente (lógica o física)
- `list_clients(filter_active=None)`: Listar todos los clientes

**Ejemplo de uso:**

```python
from app.queries.query13 import create_client, read_client, update_client

# Crear cliente
nuevo_cliente = {
    "id_cliente": 1000,
    "nombre": "Juan",
    "apellido": "Pérez",
    "dni": "12345678",
    "email": "juan@example.com",
    "telefono": "1234567890",
    "direccion": "Calle Falsa 123",
    "ciudad": "Buenos Aires",
    "provincia": "Buenos Aires",
    "activo": True
}
create_client(nuevo_cliente)

# Leer cliente
cliente = read_client(1000)

# Actualizar cliente
update_client(1000, {"telefono": "9876543210"})
```

Ejecutar ejemplos:
```powershell
python run_query.py 13
```

### Query 14: Alta de nuevos siniestros

Crear y gestionar siniestros (reclamos de seguros).

**Funciones disponibles:**
- `create_claim(claim_data)`: Crear un nuevo siniestro
- `update_claim_status(nro_poliza, id_siniestro, nuevo_estado, ...)`: Actualizar estado del siniestro
- `get_claims_by_policy(nro_poliza)`: Obtener todos los siniestros de una póliza

**Ejemplo de uso:**

```python
from app.queries.query14 import create_claim, update_claim_status

# Crear siniestro
nuevo_siniestro = {
    "nro_poliza": 1,
    "id_siniestro": 5000,
    "tipo": "Accidente",
    "fecha": "12/11/2025",
    "monto_estimado": 50000.00,
    "estado": "Abierto",
    "descripcion": "Colisión frontal en autopista"
}
create_claim(nuevo_siniestro)

# Actualizar estado
update_claim_status(1, 5000, "En Proceso", monto_final=48000.00)
```

Ejecutar ejemplos:
```powershell
python run_query.py 14
```

### Query 15: Emisión de nuevas pólizas

Emitir nuevas pólizas con validación de cliente y agente.

**Funciones disponibles:**
- `issue_new_policy(policy_data)`: Emitir una nueva póliza
- `validate_policy_requirements(id_cliente, tipo_poliza)`: Validar requisitos del cliente
- `get_available_agents()`: Obtener agentes disponibles

**Ejemplo de uso:**

```python
from app.queries.query15 import issue_new_policy, get_available_agents
from datetime import datetime, timedelta

# Ver agentes disponibles
agentes = get_available_agents()

# Emitir póliza
today = datetime.now()
one_year_later = today + timedelta(days=365)

nueva_poliza = {
    "id_cliente": 1,
    "nro_poliza": 10000,
    "tipo": "Auto",
    "fecha_inicio": today.strftime("%d/%m/%Y"),
    "fecha_fin": one_year_later.strftime("%d/%m/%Y"),
    "prima_mensual": 5000.00,
    "cobertura_total": 500000.00,
    "deducible": 10000.00,
    "id_agente": 1,
    "estado": "Activa"
}
issue_new_policy(nueva_poliza)
```

Ejecutar ejemplos:
```powershell
python run_query.py 15
```

## 📁 Estructura del Proyecto

```
BD2_TPO/
├── app/
│   ├── db.py                    # Conexiones a MongoDB y Redis
│   ├── main.py                  # Script de carga de datos
│   └── queries/
│       ├── __init__.py
│       ├── query1.py            # Clientes activos
│       ├── query2.py            # Siniestros abiertos
│       ├── query3.py            # Vehículos asegurados
│       ├── query4.py            # Clientes sin pólizas activas
│       ├── query5.py            # Agentes con conteo de pólizas
│       ├── query6.py            # Pólizas vencidas
│       ├── query7.py            # Top 10 clientes (Redis)
│       ├── query8.py            # Siniestros tipo Accidente
│       ├── query9.py            # Vista pólizas activas
│       ├── query10.py           # Pólizas suspendidas
│       ├── query11.py           # Clientes con múltiples vehículos
│       ├── query12.py           # Agentes y siniestros
│       ├── query13.py           # ABM de clientes
│       ├── query14.py           # Alta de siniestros
│       └── query15.py           # Emisión de pólizas
├── resources/
│   ├── clientes.csv
│   ├── polizas.csv
│   ├── siniestros.csv
│   ├── agentes.csv
│   └── vehiculos.csv
├── mongo_data/                  # Datos persistentes de MongoDB
├── redis_data/                  # Datos persistentes de Redis
├── docker-compose.yml           # Configuración de contenedores
├── requirements.txt             # Dependencias de Python
└── README.md                    # Este archivo
```

## Modelo de Datos

### Estructura de documentos en MongoDB

Los datos se almacenan en la colección `aseguradoras` de la base de datos `tp_bd2`:

```json
{
  "id_cliente": 1,
  "nombre": "Laura",
  "apellido": "Gómez",
  "dni": "32456789",
  "email": "laura@gmail.com",
  "telefono": "1145678901",
  "direccion": "Av. Rivadavia 1234",
  "ciudad": "Buenos Aires",
  "provincia": "Buenos Aires",
  "activo": true,
  "polizas": [
    {
      "nro_poliza": 1,
      "tipo": "Auto",
      "fecha_inicio": "15/03/2024",
      "fecha_fin": "15/03/2025",
      "prima_mensual": 5000.00,
      "cobertura_total": 500000.00,
      "deducible": 10000.00,
      "id_agente": 1,
      "estado": "Activa",
      "agente": {
        "nombre": "Carlos",
        "apellido": "Martínez",
        "email": "carlos@agencia.com",
        "activo": true
      },
      "siniestros": [
        {
          "id_siniestro": 1,
          "tipo": "Accidente",
          "fecha": "05/01/2025",
          "monto_estimado": 15000.00,
          "estado": "Abierto",
          "descripcion": "Choque menor en estacionamiento"
        }
      ]
    }
  ],
  "vehiculos": [
    {
      "id_vehiculo": 1,
      "patente": "ABC123",
      "marca": "Toyota",
      "modelo": "Corolla",
      "anio": 2020,
      "asegurado": true
    }
  ]
}
```

### Redis

Redis se utiliza para almacenar un sorted set con los clientes ordenados por cobertura total:
- **Key**: `top_clients_coverage`
- **Score**: Cobertura total
- **Member**: `{id_cliente}|{nombre} {apellido}`

## Troubleshooting

### Error: "No module named 'app'" o "No module named 'pymongo'"

**Causa**: El entorno virtual no está activado o las dependencias no están instaladas.

**Solución**:
```powershell
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Verificar que esté activado (deberías ver (.venv) en tu prompt)
# Instalar dependencias si es necesario
pip install -r requirements.txt
```

### Los contenedores no inician

```powershell
# Verificar logs
docker-compose logs

# Reiniciar contenedores
docker-compose restart
```

### Error de conexión a MongoDB o Redis

Verificar que los contenedores estén corriendo:
```powershell
docker ps
```

Si no están corriendo, iniciarlos:
```powershell
docker-compose up -d
```

### Error al cargar datos

Asegurarse de que:
1. El entorno virtual esté activado
2. Los archivos CSV estén en la carpeta `resources/`
3. Los contenedores estén corriendo

### Puerto ya en uso

Si los puertos 27017 o 6379 están en uso:
1. Detener los servicios que los están usando
2. O modificar el `docker-compose.yml` para usar otros puertos


## Autores

Proyecto desarrollado para la materia Base de Datos 2 - ITBA


## Redis Caching

El sistema implementa una capa de caché con Redis para mejorar significativamente el rendimiento de las consultas.

### Beneficios del Caché

- **30-100x más rápido**: Las consultas cacheadas responden en 2-5ms vs 100-200ms
- **Menor carga en MongoDB**: Reduce operaciones de lectura en la base de datos
- **Invalidación automática**: El caché se actualiza automáticamente al modificar datos
- **TTL configurable**: Cada tipo de consulta tiene un tiempo de vida apropiado

### Consultas con Caché Implementado

| Query | Cache TTL | Descripción |
|-------|-----------|-------------|
| Query 1 | 5 minutos | Clientes activos |
| Query 2 | 2 minutos | Siniestros abiertos (cambian frecuentemente) |
| Query 5 | 10 minutos | Agentes con pólizas (datos más estáticos) |

### Uso del Caché

Las consultas usan caché por defecto. La primera llamada consulta MongoDB, las siguientes usan Redis:

```powershell
# Primera llamada - Cache MISS
python run_query.py 1
# Output: ✗ Cache MISS - Querying MongoDB...
#         ✓ Stored 147 clients in cache (TTL: 300 seconds)

# Segunda llamada - Cache HIT (mucho más rápido)
python run_query.py 1
# Output: ✓ Cache HIT - Retrieved 147 active clients from Redis
#         (TTL: 285 seconds remaining)
```

### Invalidación de Caché

Al realizar operaciones de escritura (crear, actualizar, eliminar), el sistema **invalida automáticamente** los cachés relacionados:

- **Crear/modificar cliente** → Invalida Query 1, Query 4
- **Crear/modificar siniestro** → Invalida Query 2, Query 8, Query 12  
- **Emitir póliza** → Invalida Query 4, Query 5, Query 7, Query 9

📖 **Ver guía completa**: [REDIS_CACHING_GUIDE.md](REDIS_CACHING_GUIDE.md)

## 🛠️ Cache Manager

Herramienta interactiva para gestionar y monitorear el caché de Redis:

```powershell
python cache_manager.py
```

### Funcionalidades

1. **Ver estadísticas** - Hit rate, total keys, conexiones
2. **Listar cachés** - Ver todas las consultas cacheadas con TTL
3. **Limpiar caché** - Eliminar todos los cachés o uno específico
4. **Limpiar query específica** - Eliminar caché de una sola consulta
5. **Test de performance** - Medir la mejora de velocidad con caché

### Ejemplo de Estadísticas

```
=== Redis Cache Statistics ===

Total Keys: 15
Total Connections: 234
Cache Hits: 1,523
Cache Misses: 145
Hit Rate: 91.3%
```

### Ejemplo de Performance Test

```
1. First call (should be MISS):
   Time: 0.156 seconds

2. Second call (should be HIT):
   Time: 0.003 seconds

Performance Improvement:
  Speed increase: 98.1%
  Speedup factor: 52.0x faster
```

