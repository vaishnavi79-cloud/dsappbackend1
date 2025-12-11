# backend/seed.py
import requests
from datetime import date, timedelta
import random

BASE = "http://localhost:8000"

def seed():
    items = ["Rice","Dal","Veg","Curd"]
    start = date.today() - timedelta(days=60)
    for i in range(60):
        d = start + timedelta(days=i)
        for item in items:
            prepared = round(random.uniform(10, 30),1)
            consumed = round(prepared - random.uniform(0, 6),1)
            payload = {
                "date": d.isoformat(),
                "item_name": item,
                "prepared_qty": prepared,
                "consumed_qty": max(0.0, consumed)
            }
            requests.post(f"{BASE}/add-entry", json=payload)
    print("seeded")
if __name__ == "__main__":
    seed()
