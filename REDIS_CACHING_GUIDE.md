# Estrategia de Caché con Redis - Guía de Implementación

## 📚 Descripción General

Este proyecto implementa una **capa de caché con Redis** para mejorar significativamente el rendimiento de las consultas. MongoDB se utiliza para la consistencia y persistencia de datos, mientras que Redis sirve como caché de alta velocidad.

## 🎯 Arquitectura

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Función Query   │
└──────┬───────────┘
       │
       ▼
┌──────────────┐     ¿Cache HIT?    ┌──────────────┐
│    Redis     │◄──────SÍ───────────│  Devolver    │
│    Cache     │                    │  Resultado   │
└──────┬───────┘                    └──────────────┘
       │
       NO (Cache MISS)
       │
       ▼
┌──────────────┐
│   MongoDB    │
│   (Fuente    │
│   de Verdad) │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Guardar en  │───────────────────►│  Devolver    │
│  Redis Cache │                    │  Resultado   │
└──────────────┘                    └──────────────┘
```

## ✅ Consultas Implementadas con Caché

### Consultas de Lectura (con TTL)

| Query | Descripción | Clave Cache | TTL | Justificación |
|-------|-------------|-------------|-----|---------------|
| **Query 1** | Clientes activos | `query1:active_clients` | 300s (5min) | El estado de clientes cambia moderadamente |
| **Query 2** | Siniestros abiertos | `query2:open_claims` | 120s (2min) | Los siniestros cambian frecuentemente |
| **Query 5** | Agentes con conteo de pólizas | `query5:active_agents_policies` | 600s (10min) | Los datos de agentes son relativamente estáticos |

### Operaciones de Escritura (Invalidación de Caché)

| Query | Operaciones | Invalida |
|-------|-------------|----------|
| **Query 13** | Crear/Actualizar/Eliminar Cliente | `query1:*`, `query4:*` |
| **Query 14** | Crear/Actualizar Siniestro | `query2:*`, `query8:*`, `query12:*` |
| **Query 15** | Emitir Póliza | `query4:*`, `query5:*`, `query7:*`, `query9:*` |

## 🚀 Ejemplos de Uso

### Usar Consultas con Caché

```python
from app.queries.query1 import get_active_clients

# Con caché (por defecto)
result = get_active_clients(use_cache=True)

# Sin caché (forzar consulta a MongoDB)
result = get_active_clients(use_cache=False)
```

### Comportamiento del Caché

**Primera llamada (Cache MISS):**
```
✗ Cache MISS - Consultando MongoDB...
✓ Almacenados 147 clientes en caché (TTL: 300 segundos)

Encontrados 147 clientes activos:
  - Laura Gómez (ID: 1) - laura@gmail.com
  ...
```

**Segunda llamada (Cache HIT):**
```
✓ Cache HIT - Recuperados 147 clientes activos desde Redis
  (TTL: 285 segundos restantes)
  - Laura Gómez (ID: 1) - laura@gmail.com
  ...
```

## 🛠️ Gestión del Caché

### Usar la Herramienta Cache Manager

```powershell
python cache_manager.py
```

**Funcionalidades:**
1. **Mostrar estadísticas de caché** - Ver tasa de aciertos, total de claves
2. **Listar todas las consultas cacheadas** - Ver qué está en caché con TTL
3. **Limpiar todo el caché** - Eliminar todas las consultas cacheadas
4. **Limpiar consulta específica** - Eliminar caché de una consulta
5. **Probar rendimiento** - Medir la mejora de velocidad con caché

### Operaciones Manuales de Caché

```python
from app.cache import RedisCache, invalidate_cache_pattern

cache = RedisCache()

# Obtener datos cacheados
data = cache.get("query1:active_clients")

# Establecer datos con TTL personalizado
cache.set("my_key", {"data": "value"}, ttl=600)

# Verificar si existe la clave
exists = cache.exists("query1:active_clients")

# Obtener TTL
ttl = cache.get_ttl("query1:active_clients")

# Eliminar clave específica
cache.delete("query1:active_clients")

# Invalidar por patrón
invalidate_cache_pattern("query1:*")
invalidate_cache_pattern("query*")  # Todas las consultas
```

## 🔄 Estrategia de Invalidación de Caché

### Patrón Write-Through

Cuando se modifican los datos:
1. Actualizar MongoDB (fuente de verdad)
2. Invalidar inmediatamente los cachés relacionados
3. La próxima lectura refrescará el caché desde MongoDB

```python
# Ejemplo de query13.py
def create_client(client_data):
    # ... crear cliente en MongoDB ...
    
    # Invalidar cachés afectados
    invalidate_cache_pattern("query1:*")  # Clientes activos
    invalidate_cache_pattern("query4:*")  # Clientes sin pólizas
    
    return result
```

### Reglas de Invalidación

| Cambio de Datos | Invalida Estos Cachés |
|-----------------|------------------------|
| Cliente creado/actualizado/eliminado | `query1:*`, `query4:*` |
| Siniestro creado/actualizado | `query2:*`, `query8:*`, `query12:*` |
| Póliza emitida | `query4:*`, `query5:*`, `query7:*`, `query9:*` |
| Cualquier operación de eliminación | `query*` (todos los cachés) |

## 📊 Guías de TTL (Time-To-Live)

### Elegir un TTL Apropiado

| Tipo de Datos | TTL Recomendado | Razón |
|---------------|-----------------|--------|
| **Altamente dinámico** (siniestros, órdenes) | 1-2 minutos | Cambian frecuentemente |
| **Moderadamente dinámico** (clientes, pólizas) | 5-10 minutos | Cambian ocasionalmente |
| **Estático** (agentes, configuraciones) | 10-30 minutos | Rara vez cambia |
| **Datos de referencia** (catálogos) | 1-24 horas | Casi nunca cambian |

### Configuraciones Actuales de TTL

```python
# Query 1 - Clientes activos
cache.set(cache_key, result, ttl=300)  # 5 minutos

# Query 2 - Siniestros abiertos
cache.set(cache_key, result, ttl=120)  # 2 minutos

# Query 5 - Agentes con conteo de pólizas
cache.set(cache_key, result, ttl=600)  # 10 minutos
```

## 🔍 Monitoreo del Rendimiento del Caché

### Ver Estadísticas

```powershell
python cache_manager.py
# Seleccionar opción 1 - Mostrar estadísticas de caché
```

**Salida:**
```
=== Estadísticas de Caché Redis ===

Total de Claves: 15
Total de Conexiones: 234
Aciertos de Caché: 1,523
Fallos de Caché: 145
Tasa de Aciertos: 91.3%
```

### Listar Consultas Cacheadas

```powershell
python cache_manager.py
# Seleccionar opción 2 - Listar todas las consultas cacheadas
```

**Salida:**
```
=== Claves de Consultas Cacheadas ===

Encontradas 3 consultas cacheadas:

  query1:active_clients                    TTL: 4m 23s
  query2:open_claims                       TTL: 1m 45s
  query5:active_agents_policies            TTL: 9m 12s
```

## 🎓 Mejores Prácticas

### ✅ QUÉ HACER

- ✅ Usar caché para **consultas de lectura intensiva**
- ✅ Establecer **TTL apropiado** basado en la volatilidad de los datos
- ✅ **Invalidar caché** cuando los datos relacionados cambien
- ✅ Monitorear **tasas de aciertos** y ajustar el TTL en consecuencia
- ✅ Usar **claves de caché descriptivas** con patrones
- ✅ Manejar **errores de conexión a Redis** con elegancia

### ❌ QUÉ NO HACER

- ❌ Cachear datos que cambian cada segundo
- ❌ Establecer TTL demasiado largo para datos dinámicos
- ❌ Olvidar invalidar el caché en escrituras
- ❌ Cachear conjuntos de resultados muy grandes (>10MB)
- ❌ Usar caché para requisitos críticos de consistencia
- ❌ Depender únicamente del caché (siempre tener fallback a MongoDB)

## 🧪 Pruebas de Rendimiento del Caché

### Ejecutar Prueba de Rendimiento

```powershell
python cache_manager.py
# Seleccionar opción 5 - Probar rendimiento del caché
```

**Salida de Ejemplo:**
```
=== Prueba de Rendimiento del Caché ===

1. Primera llamada (debería ser MISS):
✗ Cache MISS - Consultando MongoDB...
✓ Almacenados 147 clientes en caché (TTL: 300 segundos)
   Tiempo: 0.156 segundos

2. Segunda llamada (debería ser HIT):
✓ Cache HIT - Recuperados 147 clientes activos desde Redis
   Tiempo: 0.003 segundos

Mejora de Rendimiento:
  Incremento de velocidad: 98.1%
  Factor de aceleración: 52.0x más rápido
```

## 🔧 Solución de Problemas

### El Caché No Funciona

**Problema:** Siempre veo "Cache MISS"

**Soluciones:**
1. Verificar que Redis esté corriendo: `docker ps`
2. Revisar la conexión a Redis en `app/db.py`
3. Asegurar que el parámetro `use_cache=True`
4. Verificar que el TTL no esté en 0

### Datos Obsoletos en el Caché

**Problema:** Veo datos antiguos incluso después de actualizaciones

**Soluciones:**
1. Verificar que la invalidación de caché se llame después de escrituras
2. Verificar que el patrón de invalidación coincida con la clave de caché
3. Limpiar caché manualmente: `python cache_manager.py` → Opción 3
4. Reducir el TTL para ese tipo de consulta

### Las Claves de Caché No Expiran

**Problema:** Las claves se quedan en Redis para siempre

**Soluciones:**
1. Verificar que el TTL esté configurado al llamar `cache.set()`
2. Verificar que la `maxmemory-policy` de Redis permita expiración
3. Usar `cache.get_ttl(key)` para depurar

## 📈 Consideraciones de Escalabilidad

### Cuándo Escalar

- Tasa de aciertos de caché < 70%
- Uso de memoria de Redis > 80%
- Tiempo de respuesta de consultas degradado
- Alta tasa de escritura/invalidación

### Opciones de Escalabilidad

1. **Aumentar memoria de Redis**: Modificar Docker compose
2. **Implementar particionamiento de caché**: Múltiples instancias de Redis
3. **Usar Redis Cluster**: Para alta disponibilidad
4. **Implementar precalentamiento de caché**: Pre-poblar consultas frecuentes
5. **Agregar réplicas de lectura**: Para MongoDB

## 🎯 Resumen

### Beneficios Clave

✅ **30-100x más rápido** tiempos de respuesta de consultas  
✅ **Carga reducida en MongoDB** para operaciones de lectura  
✅ **Invalidación automática** en cambios de datos  
✅ **Configuración flexible de TTL**  
✅ **Monitoreo fácil** con cache manager  
✅ **Degradación elegante** si Redis falla  

### Comandos Rápidos

```powershell
# Ejecutar consulta con caché
python run_query.py 1

# Gestionar caché
python cache_manager.py

# Limpiar todo el caché
python cache_manager.py → Opción 3

# Ver estadísticas
python cache_manager.py → Opción 1
```

---

**Recuerda**: MongoDB es la fuente de verdad. ¡Redis es solo una capa de optimización de rendimiento!
