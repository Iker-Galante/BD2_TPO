import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_redis_client


def get_top10_clients_by_total_coverage():

    redis_client = get_redis_client()
    redis_key = "top_clients_coverage"

    entries = redis_client.zrevrange(redis_key, 0, 9, withscores=True)

    result = []

    if isinstance(entries[0], tuple):
        for member, score in entries:
            member = member.decode() if isinstance(member, bytes) else member
            id_cliente_str, nombre = member.split("|", 1)
            result.append({
                "id_cliente": int(id_cliente_str),
                "cobertura_total": float(score)
            })
    else:
        result = entries

    print("Top 10 clientes por cobertura total:")
    for r in result:
        print(
            f"Cliente {r['id_cliente']}: "
            f"cobertura total = {r['cobertura_total']}"
        )

    return result


if __name__ == "__main__":
    print("=== MongoDB + Redis Query 7 ===\n")
    get_top10_clients_by_total_coverage()
