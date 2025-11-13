"""
Redis Cache Helper Module

Provides caching utilities for MongoDB queries to improve performance.
"""

import json
import pickle
from datetime import datetime, timedelta
from app.db import get_redis_client


class RedisCache:
    """Helper class for Redis caching operations"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis_client()
        self.default_ttl = 300  # 5 minutes default TTL
    
    def get(self, key):
        """
        Get cached data from Redis
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found
        """
        try:
            cached = self.redis.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            print(f"Redis GET error: {e}")
            return None
    
    def set(self, key, data, ttl=None):
        """
        Store data in Redis cache
        
        Args:
            key: Cache key
            data: Data to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 300)
        """
        try:
            ttl = ttl or self.default_ttl
            self.redis.setex(
                key,
                ttl,
                json.dumps(data, default=str)  # default=str handles dates
            )
            return True
        except Exception as e:
            print(f"Redis SET error: {e}")
            return False
    
    def delete(self, key):
        """
        Delete a key from cache
        
        Args:
            key: Cache key to delete
        """
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Redis DELETE error: {e}")
            return False
    
    def clear_pattern(self, pattern):
        """
        Clear all keys matching a pattern
        
        Args:
            pattern: Pattern to match (e.g., "query:*")
        """
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            print(f"Redis CLEAR error: {e}")
            return 0
    
    def exists(self, key):
        """Check if key exists in cache"""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            print(f"Redis EXISTS error: {e}")
            return False
    
    def get_ttl(self, key):
        """Get remaining TTL for a key"""
        try:
            return self.redis.ttl(key)
        except Exception as e:
            print(f"Redis TTL error: {e}")
            return -1


def cached_query(cache_key, ttl=300):
    """
    Decorator for caching query results
    
    Usage:
        @cached_query("query1:active_clients", ttl=600)
        def get_active_clients():
            # ... query logic
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = RedisCache()
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                print(f"✓ Cache HIT: {cache_key}")
                return cached_result
            
            print(f"✗ Cache MISS: {cache_key} - Querying MongoDB...")
            
            # Execute the function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            print(f"✓ Cached result for {ttl} seconds")
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern):
    """
    Invalidate all cache entries matching a pattern
    
    Usage:
        invalidate_cache_pattern("query1:*")
    """
    cache = RedisCache()
    count = cache.clear_pattern(pattern)
    print(f"✓ Invalidated {count} cache entries matching '{pattern}'")
    return count


def get_cache_stats():
    """Get Redis cache statistics"""
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
        print(f"Error getting cache stats: {e}")
        return None


# Example usage functions
if __name__ == "__main__":
    print("=== Redis Cache Stats ===")
    stats = get_cache_stats()
    if stats:
        for k, v in stats.items():
            print(f"{k}: {v}")
