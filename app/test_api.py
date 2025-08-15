# test_records_client.py
import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# ---- Config ----
BASE_URL = "http://localhost:8890"
# BASE_URL = os.getenv("BASE_URL", "http://sv3.cletrix.net:8890")
API_KEY = os.getenv("API_SECRET_KEY")

# Sample identifiers for testing
USER_ID = os.getenv("TEST_USER_ID", "cleyton")
MATCH_ID = os.getenv("TEST_MATCH_ID", "match-007")
LIMIT = int(os.getenv("TEST_LIMIT", "12"))

HEADERS = {
    "Content-Type": "application/json",
    "X-API-KEY": API_KEY or "",
}


def _check_api_key():
    """Ensure API key is present before hitting the server."""
    if not API_KEY:
        print("ERROR: API_SECRET_KEY not found in environment (.env).", file=sys.stderr)
        sys.exit(1)


def pretty(label: str, resp: requests.Response):
    """Print status + JSON (or text) nicely."""
    print(f"\n=== {label} ===")
    print("Status:", resp.status_code)
    try:
        data = resp.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text)


# ---------- New endpoints ----------

def test_upsert_record(input_data=None, output_data=None):
    """POST /record -> create/update with input and optional output."""
    payload = {
        "user_id": USER_ID,
        "match": MATCH_ID,
    }
    if input_data is not None:
        payload["input"] = input_data
    if output_data is not None:
        payload["output"] = output_data

    resp = requests.post(
        f"{BASE_URL}/record",
        headers=HEADERS,
        json=payload,
        timeout=15,
    )
    pretty("POST /record (upsert)", resp)


def test_set_output(output_data):
    """PUT /record/output -> set/replace output only."""
    payload = {
        "user_id": USER_ID,
        "match": MATCH_ID,
        "output": output_data,
    }
    resp = requests.put(
        f"{BASE_URL}/record/output",
        headers=HEADERS,
        json=payload,
        timeout=15,
    )
    pretty("PUT /record/output", resp)


def test_get_one():
    """GET /record?user_id=...&match=..."""
    params = {
        "user_id": USER_ID,
        "match": MATCH_ID,
    }
    resp = requests.get(
        f"{BASE_URL}/record",
        headers=HEADERS,
        params=params,
        timeout=15,
    )
    pretty("GET /record", resp)


def test_get_recent(n=LIMIT):
    """GET /records?user_id=...&limit=n"""
    params = {
        "user_id": USER_ID,
        "limit": n,
    }
    resp = requests.get(
        f"{BASE_URL}/records",
        headers=HEADERS,
        params=params,
        timeout=15,
    )
    pretty("GET /records (recent)", resp)


# ---------- Demo flow ----------

if __name__ == "__main__":
    # _check_api_key()
    #
    # # 1) Upsert with input only
    # test_upsert_record(input_data={"usuario": "Maria", "valor": 120})
    #
    # # 2) Read single record
    # test_get_one()
    #
    # # 3) Set/replace output
    # test_set_output({"status": "ok", "tempo": 3.2})
    #
    # # 4) Read again single record
    # test_get_one()
    #
    # # 5) Get recent records for the user
    test_get_recent()
