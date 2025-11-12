"""
Cache Management Utility

Provides commands to view and manage Redis cache
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.cache import RedisCache, get_cache_stats, invalidate_cache_pattern


def show_cache_stats():
    """Display Redis cache statistics"""
    print("=== Redis Cache Statistics ===\n")
    
    stats = get_cache_stats()
    if stats:
        print(f"Total Keys: {stats['total_keys']}")
        print(f"Total Connections: {stats['total_connections']}")
        print(f"Cache Hits: {stats['keyspace_hits']}")
        print(f"Cache Misses: {stats['keyspace_misses']}")
        print(f"Hit Rate: {stats['hit_rate_percent']}%")
    else:
        print("Could not retrieve cache stats")
    
    print("\n" + "="*40 + "\n")


def list_cache_keys():
    """List all cache keys"""
    print("=== Cached Query Keys ===\n")
    
    cache = RedisCache()
    keys = cache.redis.keys("query*")
    
    if not keys:
        print("No cached queries found")
        return
    
    print(f"Found {len(keys)} cached queries:\n")
    
    for key in keys:
        key_str = key.decode() if isinstance(key, bytes) else key
        ttl = cache.get_ttl(key_str)
        
        if ttl > 0:
            minutes = ttl // 60
            seconds = ttl % 60
            ttl_str = f"{minutes}m {seconds}s"
        elif ttl == -1:
            ttl_str = "No expiry"
        else:
            ttl_str = "Expired"
        
        print(f"  {key_str:<40} TTL: {ttl_str}")
    
    print("\n" + "="*60 + "\n")


def clear_all_cache():
    """Clear all query caches"""
    print("=== Clearing All Query Caches ===\n")
    
    count = invalidate_cache_pattern("query*")
    print(f"\n✓ Cleared {count} cache entries")
    print("\n" + "="*40 + "\n")


def clear_specific_query(query_num):
    """Clear cache for a specific query"""
    print(f"=== Clearing Cache for Query {query_num} ===\n")
    
    pattern = f"query{query_num}:*"
    count = invalidate_cache_pattern(pattern)
    print(f"\n✓ Cleared {count} cache entries for query {query_num}")
    print("\n" + "="*40 + "\n")


def test_cache_performance():
    """Test cache performance"""
    print("=== Cache Performance Test ===\n")
    
    import time
    from app.queries.query1 import get_active_clients
    
    # First call - should hit MongoDB
    print("1. First call (should be MISS):")
    start = time.time()
    result1 = get_active_clients(use_cache=True)
    time1 = time.time() - start
    print(f"   Time: {time1:.3f} seconds\n")
    
    # Second call - should hit cache
    print("2. Second call (should be HIT):")
    start = time.time()
    result2 = get_active_clients(use_cache=True)
    time2 = time.time() - start
    print(f"   Time: {time2:.3f} seconds\n")
    
    # Calculate improvement
    if time1 > 0:
        improvement = ((time1 - time2) / time1) * 100
        speedup = time1 / time2 if time2 > 0 else 0
        print(f"Performance Improvement:")
        print(f"  Speed increase: {improvement:.1f}%")
        print(f"  Speedup factor: {speedup:.1f}x faster")
    
    print("\n" + "="*40 + "\n")


def show_menu():
    """Display menu options"""
    print("\n" + "="*60)
    print("           Redis Cache Management Utility")
    print("="*60 + "\n")
    
    print("Options:")
    print("  1 - Show cache statistics")
    print("  2 - List all cached queries")
    print("  3 - Clear all cache")
    print("  4 - Clear specific query cache")
    print("  5 - Test cache performance")
    print("  0 - Exit")
    print()


def main():
    """Main menu loop"""
    while True:
        show_menu()
        
        try:
            choice = input("Select an option: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting...")
            break
        
        print()
        
        if choice == "0":
            print("Exiting...\n")
            break
        elif choice == "1":
            show_cache_stats()
        elif choice == "2":
            list_cache_keys()
        elif choice == "3":
            confirm = input("Are you sure you want to clear ALL caches? (yes/no): ").lower()
            if confirm == "yes":
                clear_all_cache()
            else:
                print("Cancelled\n")
        elif choice == "4":
            query_num = input("Enter query number (1-15): ").strip()
            if query_num.isdigit() and 1 <= int(query_num) <= 15:
                clear_specific_query(query_num)
            else:
                print("Invalid query number\n")
        elif choice == "5":
            test_cache_performance()
        else:
            print("Invalid option\n")
        
        input("Press Enter to continue...")


if __name__ == "__main__":
    print("\n🚀 Redis Cache Management Utility\n")
    
    # Quick stats on startup
    stats = get_cache_stats()
    if stats:
        print(f"Cache Status: ✓ Connected")
        print(f"Total Keys: {stats['total_keys']}")
        print(f"Hit Rate: {stats['hit_rate_percent']}%")
    else:
        print("⚠️  Could not connect to Redis. Make sure Docker containers are running.")
        sys.exit(1)
    
    main()
