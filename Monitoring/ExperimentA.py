import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv(".env", override=True)

proxy = os.getenv("KAGGLE_PROXY", "").rstrip("/")
url = f"{proxy}/proxy/8000/v1/chat/completions"

def send_request(i):
    payload = {
        "model": "Qwen/Qwen2.5-0.5B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": f"Explain artificial intelligence in detail. "
                           f"Include concepts, examples and applications. "
                           f"Request number {i}."
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.6
    }

    response = requests.post(url, json=payload, timeout=180)
    response.raise_for_status()

    return response.json()["usage"]

start = time.perf_counter()

with ThreadPoolExecutor(max_workers=15) as executor:
    futures = [
        executor.submit(send_request, i)
        for i in range(20)
    ]

    for future in futures:
        print(future.result())

print("Total elapsed:", round(time.perf_counter() - start, 2), "seconds")