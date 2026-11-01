
import os
import csv
import time
import statistics
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import requests
from dotenv import load_dotenv

# ---------------------------------------
# Configuration
# ---------------------------------------

load_dotenv(Path(__file__).with_name(".env"), override=True)

KAGGLE_PROXY = os.getenv("KAGGLE_PROXY", "").strip().rstrip("/")

if not KAGGLE_PROXY:
    raise RuntimeError("KAGGLE_PROXY is missing")

URL = f"{KAGGLE_PROXY}/proxy/8000/v1/chat/completions"

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

DURATION = 180
CONCURRENCY = 5
MAX_TOKENS = 256

results = []
lock = threading.Lock()
stop_event = threading.Event()

# ---------------------------------------
# Worker function
# ---------------------------------------

def worker(worker_id, deadline):
    session = requests.Session()
    request_id = 0

    while time.monotonic() < deadline and not stop_event.is_set():
        request_id += 1

        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Worker {worker_id}, request {request_id}. "
                        "Explain how transformers work, including "
                        "attention, embeddings, and inference. "
                        "Give examples and detailed explanations."
                    )
                }
            ],
            "max_tokens": MAX_TOKENS,
            "temperature": 0.7
        }

        start = time.perf_counter()
        success = False
        output_tokens = 0
        error = ""

        try:
            response = session.post(
                URL,
                json=payload,
                timeout=60
            )

            response.raise_for_status()

            data = response.json()

            output_tokens = data.get(
                "usage", {}
            ).get("completion_tokens", 0)

            success = True

        except requests.RequestException as exc:
            error = type(exc).__name__

        except (ValueError, KeyError) as exc:
            error = type(exc).__name__

        latency = time.perf_counter() - start

        with lock:
            results.append({
                "worker": worker_id,
                "request": request_id,
                "success": success,
                "latency_sec": round(latency, 4),
                "output_tokens": output_tokens,
                "error": error
            })

    session.close()


# ---------------------------------------
# Run experiment
# ---------------------------------------

print("Starting sustained load test")
print("Duration:", DURATION, "seconds")
print("Concurrency:", CONCURRENCY)
print("Max tokens:", MAX_TOKENS)
print("Press Ctrl+C to stop early")

start_time = time.perf_counter()
deadline = time.monotonic() + DURATION

try:
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [
            executor.submit(worker, i, deadline)
            for i in range(CONCURRENCY)
        ]

        for future in futures:
            future.result()

except KeyboardInterrupt:
    stop_event.set()
    print("\nStopping after in-flight requests finish...")

elapsed = time.perf_counter() - start_time

# ---------------------------------------
# Save CSV
# ---------------------------------------

csv_path = Path(__file__).with_name(
    "experiment_b_results.csv"
)

with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "worker",
            "request",
            "success",
            "latency_sec",
            "output_tokens",
            "error"
        ]
    )

    writer.writeheader()
    writer.writerows(results)

# ---------------------------------------
# Calculate metrics
# ---------------------------------------

successful = [r for r in results if r["success"]]
failed = [r for r in results if not r["success"]]

latencies = sorted(
    r["latency_sec"] for r in successful
)

def percentile(values, p):
    if not values:
        return 0

    index = (len(values) - 1) * p / 100
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    fraction = index - lower

    return (
        values[lower] * (1 - fraction)
        + values[upper] * fraction
    )

total_tokens = sum(
    r["output_tokens"] for r in successful
)

print("\n========== EXPERIMENT B RESULTS ==========")

print("Elapsed time:", round(elapsed, 2), "sec")
print("Total requests:", len(results))
print("Successful:", len(successful))
print("Failed:", len(failed))

print(
    "Error rate:",
    round(100 * len(failed) / max(len(results), 1), 2),
    "%"
)

print(
    "Throughput:",
    round(len(successful) / elapsed, 2),
    "requests/sec"
)

print(
    "Output throughput:",
    round(total_tokens / elapsed, 2),
    "tokens/sec"
)

if latencies:
    print(
        "Mean latency:",
        round(statistics.mean(latencies), 3),
        "sec"
    )

    print(
        "p50 latency:",
        round(percentile(latencies, 50), 3),
        "sec"
    )

    print(
        "p95 latency:",
        round(percentile(latencies, 95), 3),
        "sec"
    )

print("CSV saved:", csv_path)
