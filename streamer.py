import json
import random
import sys
import time
from datetime import datetime, timezone

PATHS = ["/api/orders", "/api/users", "/api/cart", "/health"]

try:
    while True:
        lines = []
        for _ in range(4000):
            event = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "method": random.choice(["GET", "POST"]),
                "path": random.choice(PATHS),
                "status": random.choice([200, 200, 200, 404, 500]),
                "latency_ms": random.randint(5, 250),
            }
            lines.append(json.dumps(event))
        sys.stdout.write("\n".join(lines) + "\n")
        sys.stdout.flush()
        time.sleep(1)
except KeyboardInterrupt:
    pass  # Ctrl+C: exit quietly, which closes the pipe
