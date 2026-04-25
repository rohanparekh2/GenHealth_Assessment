import os

import requests


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
PDF_PATH = os.getenv(
    "PDF_PATH",
    "/Users/rohanparekh99/Downloads/DME Patient Demo Document CPAP.fax.pdf",
)


def print_step(name, response):
    print(f"\n=== {name} ===")
    print("Status:", response.status_code)
    try:
        print("Response:", response.json())
    except Exception:
        print("Response:", response.text)


def main():
    # 1) CREATE ORDER
    create_payload = {
        "patient_first_name": "John",
        "patient_last_name": "Doe",
        "date_of_birth": "1990-01-01",
    }
    response = requests.post(f"{BASE_URL}/orders", json=create_payload, timeout=30)
    print_step("CREATE ORDER", response)

    if response.status_code >= 400:
        print("Create failed, stopping.")
        return

    order = response.json()
    order_id = order.get("id")
    if not order_id:
        print("No order id returned, stopping.")
        return

    # 2) GET ALL ORDERS
    response = requests.get(f"{BASE_URL}/orders", timeout=30)
    print_step("GET ALL ORDERS", response)

    # 3) UPDATE ORDER
    update_payload = {"date_of_birth": "1990-01-02"}
    response = requests.put(f"{BASE_URL}/orders/{order_id}", json=update_payload, timeout=30)
    print_step("UPDATE ORDER", response)

    # 4) DELETE ORDER
    response = requests.delete(f"{BASE_URL}/orders/{order_id}", timeout=30)
    print_step("DELETE ORDER", response)

    # 5) UPLOAD PDF
    try:
        with open(PDF_PATH, "rb") as file_handle:
            files = {"file": (os.path.basename(PDF_PATH), file_handle, "application/pdf")}
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=60)
            print_step("UPLOAD PDF", response)
    except FileNotFoundError:
        print("\n=== UPLOAD PDF ===")
        print(f"PDF not found at '{PDF_PATH}' (skip or set PDF_PATH env var).")


if __name__ == "__main__":
    main()
