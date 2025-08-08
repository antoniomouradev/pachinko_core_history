import os
import requests
from dotenv import load_dotenv

load_dotenv()


BASE_URL = "http://localhost:8890"
API_KEY = os.getenv("API_SECRET_KEY")
UUID = "abc123"

HEADERS = {
    "Content-Type": "application/json",
    "X-API-KEY": API_KEY,
}


def test_save_input():
    data = {
        "usuario": "Maria",
        "valor": 120
    }
    response = requests.post(
        f"{BASE_URL}/save_input",
        params={"uuid": UUID},
        headers=HEADERS,
        json=data
    )
    print("Save Input:", response.status_code, response.json())


def test_save_output():
    data = {
        "status": "ok",
        "tempo": 3.2
    }
    response = requests.post(
        f"{BASE_URL}/save_output",
        params={"uuid": UUID},
        headers=HEADERS,
        json=data
    )
    print("Save Output:", response.status_code, response.json())


def test_get_payload():
    response = requests.get(
        f"{BASE_URL}/get_payload",
        params={"uuid": UUID},
        headers=HEADERS
    )
    print("Get Payload:", response.status_code)
    try:
        print(response.json())
    except Exception as e:
        print("Erro ao decodificar resposta:", e)
        print(response.text)


if __name__ == "__main__":
    test_save_input()
    test_save_output()
    test_get_payload()
