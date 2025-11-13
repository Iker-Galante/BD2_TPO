# Resumen de Implementación - BD2 TPO

## 📊 Consultas Implementadas

### Consultas de Lectura (Queries 1-12)

| # | Descripción | Archivo | Estado |
|---|-------------|---------|--------|
| 1 | Clientes activos con sus pólizas vigentes | `query1.py` | ✅ Implementado |
| 2 | Siniestros abiertos con tipo, monto y cliente afectado | `query2.py` | ✅ Implementado |
| 3 | Vehículos asegurados con su cliente y póliza | `query3.py` | ✅ Implementado |
| 4 | Clientes sin pólizas activas | `query4.py` | ✅ Implementado |
| 5 | Agentes activos con cantidad de pólizas asignadas | `query5.py` | ✅ Implementado |
| 6 | Pólizas vencidas con el nombre del cliente | `query6.py` | ✅ Implementado |
| 7 | Top 10 clientes por cobertura total | `query7.py` | ✅ Implementado (Redis) |
| 8 | Siniestros tipo "Accidente" del último año | `query8.py` | ✅ Implementado |
| 9 | Vista de pólizas activas ordenadas por fecha de inicio | `query9.py` | ✅ Implementado |
| 10 | Pólizas suspendidas con estado del cliente | `query10.py` | ✅ Implementado |
| 11 | Clientes con más de un vehículo asegurado | `query11.py` | ✅ Implementado |
| 12 | Agentes y cantidad de siniestros asociados | `query12.py` | ✅ Implementado |

### Servicios de Escritura (Queries 13-15)

| # | Descripción | Archivo | Funciones Principales | Estado |
|---|-------------|---------|----------------------|--------|
| 13 | ABM de clientes | `query13.py` | `create_client()`, `read_client()`, `update_client()`, `delete_client()`, `list_clients()` | ✅ Implementado |
| 14 | Alta de nuevos siniestros | `query14.py` | `create_claim()`, `update_claim_status()`, `get_claims_by_policy()` | ✅ Implementado |
| 15 | Emisión de nuevas pólizas | `query15.py` | `issue_new_policy()`, `validate_policy_requirements()`, `get_available_agents()` | ✅ Implementado |


### Query 13 - ABM de Clientes

**Operaciones CRUD completas:**
- ✅ **Alta (Create)**: Crear nuevos clientes con validación de campos requeridos
- ✅ **Baja (Delete)**: Eliminar clientes (soft delete o hard delete)
- ✅ **Modificación (Update)**: Actualizar información del cliente
- ✅ **Lectura (Read)**: Consultar cliente por ID
- ✅ **Listado**: Listar todos los clientes con filtros opcionales

**Validaciones:**
- Campos requeridos: id_cliente, nombre, apellido, dni, email
- Prevención de duplicados por id_cliente
- Estado por defecto: activo = True
- Inicialización de arrays vacíos para pólizas y vehículos

### Query 14 - Alta de Siniestros

**Funcionalidades:**
- ✅ Crear nuevos siniestros asociados a pólizas existentes
- ✅ Actualizar estado de siniestros (Abierto → En Proceso → Cerrado/Rechazado)
- ✅ Consultar todos los siniestros de una póliza
- ✅ Registrar monto final y fecha de resolución

**Validaciones:**
- Verifica que la póliza existe
- Previene duplicados de id_siniestro
- Valida tipo de siniestro: Accidente, Robo, Incendio, Granizo, Otro
- Valida estado: Abierto, En Proceso, Cerrado, Rechazado
- Formato de fecha: DD/MM/YYYY

### Query 15 - Emisión de Pólizas

**Funcionalidades:**
- ✅ Emitir nuevas pólizas con validación completa
- ✅ Validar que el cliente existe y está activo
- ✅ Validar que el agente existe y está activo
- ✅ Verificar requisitos específicos por tipo de póliza
- ✅ Listar agentes disponibles para asignación

**Validaciones:**
- ✅ Cliente debe existir y estar activo
- ✅ Agente debe existir y estar activo
- ✅ Número de póliza único (sin duplicados)
- ✅ Tipos válidos: Auto, Hogar, Vida, Salud, Comercio
- ✅ Estados válidos: Activa, Suspendida, Vencida, Cancelada
- ✅ Validación de fechas (inicio < fin)
- ✅ Validación de montos (prima_mensual > 0, cobertura_total > 0)
- ✅ Formato de fecha: DD/MM/YYYY
- ✅ Asociación automática de información del agente

## 🗄️ Tecnologías Utilizadas

- **MongoDB**: Base de datos principal (documentos embebidos)
- **Redis**: Caché para top clientes por cobertura (sorted set)
- **Python 3.12**: Lenguaje de programación
- **PyMongo**: Cliente de MongoDB
- **Redis-py**: Cliente de Redis
- **Pandas**: Procesamiento de datos CSV
- **Docker & Docker Compose**: Contenedores para MongoDB y Redis

## 📦 Estructura de Datos

### Modelo de Documento (MongoDB)

```json
{
  "id_cliente": int,
  "nombre": string,
  "apellido": string,
  "dni": string,
  "email": string,
  "telefono": string,
  "direccion": string,
  "ciudad": string,
  "provincia": string,
  "activo": boolean,
  "polizas": [
    {
      "nro_poliza": int,
      "tipo": string,
      "fecha_inicio": string (DD/MM/YYYY),
      "fecha_fin": string (DD/MM/YYYY),
      "prima_mensual": float,
      "cobertura_total": float,
      "deducible": float,
      "id_agente": int,
      "estado": string,
      "agente": {
        "nombre": string,
        "apellido": string,
        "email": string,
        "telefono": string,
        "activo": boolean
      },
      "siniestros": [
        {
          "id_siniestro": int,
          "tipo": string,
          "fecha": string (DD/MM/YYYY),
          "monto_estimado": float,
          "monto_final": float,
          "estado": string,
          "descripcion": string,
          "fecha_resolucion": string
        }
      ]
    }
  ],
  "vehiculos": [
    {
      "id_vehiculo": int,
      "patente": string,
      "marca": string,
      "modelo": string,
      "anio": int,
      "asegurado": boolean
    }
  ]
}
```

### Redis - Sorted Set

**Key**: `top_clients_coverage`
- **Score**: cobertura_total (float)
- **Member**: `{id_cliente}|{nombre} {apellido}` (string)


## Documentación

 **README.md completo** con:
- Guía de inicio rápido
- Instalación paso a paso
- Descripción de cada consulta
- Ejemplos de uso para servicios ABM
- Estructura del proyecto
- Troubleshooting
- Modelo de datos


##  Características Destacadas

1. **Arquitectura embebida**: Pólizas, siniestros y vehículos embebidos en el documento del cliente
2. **Validaciones robustas**: Todas las operaciones de escritura incluyen validaciones completas
3. **Redis para optimización**: Top clientes pre-calculado en Redis para consultas rápidas
4. **Soft delete**: Opción de eliminación lógica para mantener historial
5. **Documentación completa**: README detallado con ejemplos prácticos

##  Posibles Mejoras Futuras

- Agregar índices en MongoDB para mejorar performance
- Implementar API REST con FastAPI o Flask para ayudar con front
- Agregar tests unitarios con pytest

