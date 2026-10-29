"""Step 6 / Task 3: fire concurrent requests and show the pool reusing connections.

Start the API first (flask --app app run), then:  python loadtest.py
"""
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "http://127.0.0.1:5000"
N_REQUESTS = 20


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return r.status, json.loads(r.read())


def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def show_stats(label):
    stats = get("/health")[1]["pool"]
    keys = ["pool_min", "pool_max", "pool_size", "pool_available",
            "requests_num", "requests_queued", "connections_num"]
    print(label, {k: stats.get(k, 0) for k in keys})


if __name__ == "__main__":
    show_stats("before:")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=N_REQUESTS) as ex:
        statuses = list(ex.map(lambda _: get("/customers")[0], range(N_REQUESTS)))
    print(f"{N_REQUESTS} concurrent GET /customers -> statuses {sorted(set(statuses))} "
          f"in {time.time() - t0:.2f}s")

    # optional: 20 concurrent transfers on the SAME two accounts exercise SERIALIZABLE + retry
    with ThreadPoolExecutor(max_workers=N_REQUESTS) as ex:
        codes = list(ex.map(
            lambda _: post("/transfer", {"from_account": 1, "to_account": 2, "amount": 100}),
            range(N_REQUESTS)))
    print(f"{N_REQUESTS} concurrent transfers -> status counts",
          {c: codes.count(c) for c in sorted(set(codes))})

    show_stats("after: ")
    print("connections_num stays <= pool_max while requests_num grows: connections are reused.")