# Redis Caching Strategy - Implementation Guide

## 📚 Overview

This project implements a **Redis caching layer** to significantly improve query performance. MongoDB is used for data consistency and persistence, while Redis serves as a high-speed cache.

## 🎯 Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Query Function  │
└──────┬───────────┘
       │
       ▼
┌──────────────┐     Cache HIT?     ┌──────────────┐
│    Redis     │◄──────YES──────────│   Return     │
│    Cache     │                    │   Result     │
└──────┬───────┘                    └──────────────┘
       │
       NO (Cache MISS)
       │
       ▼
┌──────────────┐
│   MongoDB    │
│   (Source    │
│   of Truth)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Store in    │───────────────────►│   Return     │
│  Redis Cache │                    │   Result     │
└──────────────┘                    └──────────────┘
```

## ✅ Implemented Queries with Caching

### Read Queries (with TTL)

| Query | Description | Cache Key | TTL | Rationale |
|-------|-------------|-----------|-----|-----------|
| **Query 1** | Active clients | `query1:active_clients` | 300s (5min) | Client status changes moderately |
| **Query 2** | Open claims | `query2:open_claims` | 120s (2min) | Claims change frequently |
| **Query 5** | Agents with policy count | `query5:active_agents_policies` | 600s (10min) | Agent data is relatively static |

### Write Operations (Cache Invalidation)

| Query | Operations | Invalidates |
|-------|-----------|-------------|
| **Query 13** | Create/Update/Delete Client | `query1:*`, `query4:*` |
| **Query 14** | Create/Update Claim | `query2:*`, `query8:*`, `query12:*` |
| **Query 15** | Issue Policy | `query4:*`, `query5:*`, `query7:*`, `query9:*` |

## 🚀 Usage Examples

### Using Cached Queries

```python
from app.queries.query1 import get_active_clients

# With cache (default)
result = get_active_clients(use_cache=True)

# Without cache (force MongoDB query)
result = get_active_clients(use_cache=False)
```

### Cache Behavior

**First call (Cache MISS):**
```
✗ Cache MISS - Querying MongoDB...
✓ Stored 147 clients in cache (TTL: 300 seconds)

Found 147 active clients:
  - Laura Gómez (ID: 1) - laura@gmail.com
  ...
```

**Second call (Cache HIT):**
```
✓ Cache HIT - Retrieved 147 active clients from Redis
  (TTL: 285 seconds remaining)
  - Laura Gómez (ID: 1) - laura@gmail.com
  ...
```

## 🛠️ Cache Management

### Using the Cache Manager Tool

```powershell
python cache_manager.py
```

**Features:**
1. **Show cache statistics** - View hit rate, total keys
2. **List all cached queries** - See what's cached with TTL
3. **Clear all cache** - Remove all cached queries
4. **Clear specific query** - Remove cache for one query
5. **Test performance** - Measure cache speedup

### Manual Cache Operations

```python
from app.cache import RedisCache, invalidate_cache_pattern

cache = RedisCache()

# Get cached data
data = cache.get("query1:active_clients")

# Set data with custom TTL
cache.set("my_key", {"data": "value"}, ttl=600)

# Check if key exists
exists = cache.exists("query1:active_clients")

# Get TTL
ttl = cache.get_ttl("query1:active_clients")

# Delete specific key
cache.delete("query1:active_clients")

# Invalidate by pattern
invalidate_cache_pattern("query1:*")
invalidate_cache_pattern("query*")  # All queries
```

## ⚡ Performance Benefits

### Typical Performance Improvement

| Operation | MongoDB (Cold) | Redis (Cached) | Speedup |
|-----------|----------------|----------------|---------|
| Query 1 (147 clients) | ~150-200ms | ~2-5ms | **30-100x faster** |
| Query 2 (Open claims) | ~100-150ms | ~2-4ms | **40-75x faster** |
| Query 5 (Agent stats) | ~80-120ms | ~2-3ms | **40-60x faster** |

### Cache Hit Rate Goals

- **Target**: >80% hit rate for read queries
- **Achieved**: Depends on query frequency and TTL settings
- **Monitor**: Use `cache_manager.py` to view statistics

## 🔄 Cache Invalidation Strategy

### Write-Through Pattern

When data is modified:
1. Update MongoDB (source of truth)
2. Immediately invalidate related caches
3. Next read will refresh cache from MongoDB

```python
# Example from query13.py
def create_client(client_data):
    # ... create client in MongoDB ...
    
    # Invalidate affected caches
    invalidate_cache_pattern("query1:*")  # Active clients
    invalidate_cache_pattern("query4:*")  # Clients without policies
    
    return result
```

### Invalidation Rules

| Data Change | Invalidate These Caches |
|-------------|-------------------------|
| Client created/updated/deleted | `query1:*`, `query4:*` |
| Claim created/updated | `query2:*`, `query8:*`, `query12:*` |
| Policy issued | `query4:*`, `query5:*`, `query7:*`, `query9:*` |
| Any delete operation | `query*` (all caches) |

## 📊 TTL (Time-To-Live) Guidelines

### Choosing Appropriate TTL

| Data Type | Recommended TTL | Reason |
|-----------|----------------|--------|
| **Highly dynamic** (claims, orders) | 1-2 minutes | Changes frequently |
| **Moderately dynamic** (clients, policies) | 5-10 minutes | Changes occasionally |
| **Static** (agents, configurations) | 10-30 minutes | Rarely changes |
| **Reference data** (catalogs) | 1-24 hours | Almost never changes |

### Current TTL Settings

```python
# Query 1 - Active clients
cache.set(cache_key, result, ttl=300)  # 5 minutes

# Query 2 - Open claims  
cache.set(cache_key, result, ttl=120)  # 2 minutes

# Query 5 - Agents with policy count
cache.set(cache_key, result, ttl=600)  # 10 minutes
```

## 🔍 Monitoring Cache Performance

### View Statistics

```powershell
python cache_manager.py
# Select option 1 - Show cache statistics
```

**Output:**
```
=== Redis Cache Statistics ===

Total Keys: 15
Total Connections: 234
Cache Hits: 1,523
Cache Misses: 145
Hit Rate: 91.3%
```

### List Cached Queries

```powershell
python cache_manager.py
# Select option 2 - List all cached queries
```

**Output:**
```
=== Cached Query Keys ===

Found 3 cached queries:

  query1:active_clients                    TTL: 4m 23s
  query2:open_claims                       TTL: 1m 45s
  query5:active_agents_policies            TTL: 9m 12s
```

## 🎓 Best Practices

### ✅ DO

- ✅ Use caching for **read-heavy queries**
- ✅ Set **appropriate TTL** based on data volatility
- ✅ **Invalidate cache** when related data changes
- ✅ Monitor **hit rates** and adjust TTL accordingly
- ✅ Use **descriptive cache keys** with patterns
- ✅ Handle Redis **connection errors** gracefully

### ❌ DON'T

- ❌ Cache data that changes every second
- ❌ Set TTL too long for dynamic data
- ❌ Forget to invalidate cache on writes
- ❌ Cache very large result sets (>10MB)
- ❌ Use cache for critical consistency requirements
- ❌ Depend solely on cache (always have MongoDB fallback)

## 🧪 Testing Cache Performance

### Run Performance Test

```powershell
python cache_manager.py
# Select option 5 - Test cache performance
```

**Sample Output:**
```
=== Cache Performance Test ===

1. First call (should be MISS):
✗ Cache MISS - Querying MongoDB...
✓ Stored 147 clients in cache (TTL: 300 seconds)
   Time: 0.156 seconds

2. Second call (should be HIT):
✓ Cache HIT - Retrieved 147 active clients from Redis
   Time: 0.003 seconds

Performance Improvement:
  Speed increase: 98.1%
  Speedup factor: 52.0x faster
```

## 🔧 Troubleshooting

### Cache Not Working

**Problem:** Always seeing "Cache MISS"

**Solutions:**
1. Verify Redis is running: `docker ps`
2. Check Redis connection in `app/db.py`
3. Ensure `use_cache=True` parameter
4. Check TTL isn't set to 0

### Stale Data in Cache

**Problem:** Seeing old data even after updates

**Solutions:**
1. Check cache invalidation is called after writes
2. Verify invalidation pattern matches cache key
3. Manually clear cache: `python cache_manager.py` → Option 3
4. Reduce TTL for that query type

### Cache Keys Not Expiring

**Problem:** Keys staying in Redis forever

**Solutions:**
1. Check TTL is set when calling `cache.set()`
2. Verify Redis `maxmemory-policy` allows expiration
3. Use `cache.get_ttl(key)` to debug

## 📈 Scaling Considerations

### When to Scale

- Cache hit rate < 70%
- Redis memory usage > 80%
- Query response time degrading
- High write/invalidation rate

### Scaling Options

1. **Increase Redis memory**: Modify Docker compose
2. **Implement cache partitioning**: Multiple Redis instances
3. **Use Redis Cluster**: For high availability
4. **Implement cache warming**: Pre-populate frequently used queries
5. **Add read replicas**: For MongoDB

## 🎯 Summary

### Key Benefits

✅ **30-100x faster** query response times  
✅ **Reduced MongoDB load** for read operations  
✅ **Automatic invalidation** on data changes  
✅ **Flexible TTL** configuration  
✅ **Easy monitoring** with cache manager  
✅ **Graceful degradation** if Redis fails  

### Quick Commands

```powershell
# Run cached query
python run_query.py 1

# Manage cache
python cache_manager.py

# Clear all cache
python cache_manager.py → Option 3

# View statistics
python cache_manager.py → Option 1
```

---

**Remember**: MongoDB is the source of truth. Redis is just a performance optimization layer!
