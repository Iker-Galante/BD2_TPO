# BD2 TPO - Sistema de Gestión de Aseguradoras

Sistema de gestión de una aseguradora implementado con MongoDB y Redis, que permite consultar información sobre clientes, pólizas, vehículos, agentes y siniestros.

## 📚 Documentación Completa

- **[RESUMEN_EJECUTIVO.md](RESUMEN_EJECUTIVO.md)**: Resumen ejecutivo con razonamiento, esquemas y demo del sistema ⭐ **COMIENCE AQUÍ**
- **[DOCUMENTACION_BASES_DATOS.md](DOCUMENTACION_BASES_DATOS.md)**: Razonamiento técnico detallado de la elección de bases de datos, esquemas lógicos y físicos
- **[DIAGRAMAS.md](DIAGRAMAS.md)**: Diagramas visuales de arquitectura, flujos de datos y comparación de performance
- **[DEMO_SISTEMA.md](DEMO_SISTEMA.md)**: Guía completa de demostración del sistema con ejemplos de todas las funcionalidades
- **[demo_script.py](demo_script.py)**: Script interactivo de demostración automática

## Características Principales

- **MongoDB**: Base de datos principal con documentos embebidos
- **Redis**: Capa de caché para optimización de consultas (30-100x más rápido)
- **Caching inteligente**: Invalidación automática al modificar datos
- **15 Consultas y servicios**: Desde lecturas simples hasta operaciones ABM completas
- **Cache Manager**: Herramienta para monitorear y gestionar el caché

## Requisitos Previos

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

### 3. Instalar dependencias de Python

```powershell
pip install -r requirements.txt
```

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
python app/main.py
```

Este script:
1. Limpia la colección existente
2. Carga el contenido de los archivos .csv a MongoDB
3. Construye un índice en Redis con el top de clientes por cobertura total

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
  
Ejecutar ejemplos:
```powershell
python app/queries/query13.py
```

### Query 14: Alta de nuevos siniestros

Crear y gestionar siniestros (reclamos de seguros).

**Funciones disponibles:**
- `create_claim(claim_data)`: Crear un nuevo siniestro
- `update_claim_status(nro_poliza, id_siniestro, nuevo_estado, ...)`: Actualizar estado del siniestro
- `get_claims_by_policy(nro_poliza)`: Obtener todos los siniestros de una póliza

**Ejemplo de uso:**

Ejecutar ejemplos:
```powershell
python app/queries/query14.py
```

### Query 15: Emisión de nuevas pólizas

Emitir nuevas pólizas con validación de cliente y agente.

**Funciones disponibles:**
- `issue_new_policy(policy_data)`: Emitir una nueva póliza
- `get_available_agents()`: Obtener agentes disponibles

**Ejemplo de uso:**

Ejecutar ejemplos:
```powershell
python app/queries/query15.py
```

## Demo del Sistema

### Demo Interactiva Automática

Ejecuta una demostración completa del sistema que muestra:
- Verificación de conexiones (MongoDB y Redis)
- Overview de datos cargados
- Comparación de performance (caché vs sin caché)
- Rankings con Redis Sorted Sets
- Operaciones ABM (Alta, Baja, Modificación)
- Estadísticas del caché

```powershell
python demo_script.py
```

### Demo Manual Completa

Para una demostración detallada paso a paso, consulta [DEMO_SISTEMA.md](DEMO_SISTEMA.md) que incluye:
- Configuración inicial del sistema
- Ejecución de todas las queries (1-15)
- Ejemplos de casos de uso completos
- Comandos útiles de Docker, MongoDB y Redis

## Redis Caching

El sistema implementa una capa de caché con Redis para mejorar significativamente el rendimiento de las consultas.

### Cache Manager

Herramienta interactiva para gestionar y monitorear el caché de Redis:

```powershell
python cache_manager.py
```

#### Funcionalidades

1. **Ver estadísticas** - Hit rate, total keys, conexiones
2. **Listar cachés** - Ver todas las consultas cacheadas con TTL
3. **Limpiar caché** - Eliminar todos los cachés o uno específico
4. **Limpiar query específica** - Eliminar caché de una sola consulta
5. **Test de performance** - Medir la mejora de velocidad con caché
