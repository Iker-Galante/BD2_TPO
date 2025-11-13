"""
Módulo de Ayuda para Caché Redis

Proporciona utilidades de caché para consultas MongoDB y mejorar el rendimiento.
"""

import json
import pickle
from datetime import datetime, timedelta
from app.db import get_redis_client


class RedisCache:
    """Clase auxiliar para operaciones de caché Redis"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis_client()
        self.default_ttl = 300  # TTL predeterminado de 5 minutos
    
    def get(self, key):
        """
        Obtener datos en caché desde Redis
        
        Args:
            key: Clave de caché
            
        Returns:
            Datos en caché o None si no se encuentra
        """
        try:
            cached = self.redis.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            print(f"Error en Redis GET: {e}")
            return None
    
    def set(self, key, data, ttl=None):
        """
        Almacenar datos en caché Redis
        
        Args:
            key: Clave de caché
            data: Datos a cachear (serán serializados a JSON)
            ttl: Tiempo de vida en segundos (predeterminado: 300)
        """
        try:
            ttl = ttl or self.default_ttl
            self.redis.setex(
                key,
                ttl,
                json.dumps(data, default=str)  # default=str maneja fechas
            )
            return True
        except Exception as e:
            print(f"Error en Redis SET: {e}")
            return False
    
    def delete(self, key):
        """
        Eliminar una clave del caché
        
        Args:
            key: Clave de caché a eliminar
        """
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Error en Redis DELETE: {e}")
            return False
    
    def clear_pattern(self, pattern):
        """
        Limpiar todas las claves que coincidan con un patrón
        
        Args:
            pattern: Patrón a coincidir (ej., "query:*")
        """
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            print(f"Error en Redis CLEAR: {e}")
            return 0
    
    def exists(self, key):
        """Verificar si la clave existe en caché"""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            print(f"Error en Redis EXISTS: {e}")
            return False
    
    def get_ttl(self, key):
        """Obtener el TTL restante para una clave"""
        try:
            return self.redis.ttl(key)
        except Exception as e:
            print(f"Error en Redis TTL: {e}")
            return -1


def cached_query(cache_key, ttl=300):
    """
    Decorador para cachear resultados de consultas
    
    Uso:
        @cached_query("query1:active_clients", ttl=600)
        def get_active_clients():
            # ... lógica de consulta
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = RedisCache()
            
            # Intentar obtener del caché
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                print(f"✓ Cache HIT: {cache_key}")
                return cached_result
            
            print(f"✗ Cache MISS: {cache_key} - Consultando MongoDB...")
            
            # Ejecutar la función
            result = func(*args, **kwargs)
            
            # Almacenar en caché
            cache.set(cache_key, result, ttl)
            print(f"✓ Resultado cacheado por {ttl} segundos")
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern):
    """
    Invalidar todas las entradas de caché que coincidan con un patrón
    
    Uso:
        invalidate_cache_pattern("query1:*")
    """
    cache = RedisCache()
    count = cache.clear_pattern(pattern)
    print(f"✓ Invalidadas {count} entradas de caché que coinciden con '{pattern}'")
    return count


def get_cache_stats():
    """Obtener estadísticas de caché Redis"""
    cache = RedisCache()
    redis = cache.redis
    
    try:
        info = redis.info('stats')
        keyspace = redis.info('keyspace')
        
        total_keys = 0
        if 'db0' in keyspace:
            total_keys = keyspace['db0']['keys']
        
        stats = {
            "total_keys": total_keys,
            "total_connections": info.get('total_connections_received', 0),
            "keyspace_hits": info.get('keyspace_hits', 0),
            "keyspace_misses": info.get('keyspace_misses', 0),
        }
        
        if stats['keyspace_hits'] + stats['keyspace_misses'] > 0:
            hit_rate = stats['keyspace_hits'] / (stats['keyspace_hits'] + stats['keyspace_misses']) * 100
            stats['hit_rate_percent'] = round(hit_rate, 2)
        else:
            stats['hit_rate_percent'] = 0
        
        return stats
    except Exception as e:
        print(f"Error obteniendo estadísticas de caché: {e}")
        return None


# Funciones de ejemplo de uso
if __name__ == "__main__":
    print("=== Estadísticas de Caché Redis ===")
    stats = get_cache_stats()
    if stats:
        for k, v in stats.items():
            print(f"{k}: {v}")
