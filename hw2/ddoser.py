import requests
import random
import time

API_BASE_URL = "http://localhost:8000"


class ShoppingCartAPI:
    def __init__(self):
        pass

    @staticmethod
    def create_item(name: str, price: float) -> dict:
        response = requests.post(f"{API_BASE_URL}/item", json={"name": name, "price": price})
        return response.json()

    @staticmethod
    def create_cart() -> dict:
        response = requests.post(f"{API_BASE_URL}/cart")
        return response.json()

    @staticmethod
    def add_item_to_cart(cart_id: int, item_id: int) -> dict:
        response = requests.post(f"{API_BASE_URL}/cart/{cart_id}/add/{item_id}")
        return response.json()

    @staticmethod
    def get_cart(cart_id: int) -> dict:
        response = requests.get(f"{API_BASE_URL}/cart/{cart_id}")
        return response.json()

    @staticmethod
    def get_item(item_id: int) -> dict:
        response = requests.get(f"{API_BASE_URL}/item/{item_id}")
        return response.json()


def simulate_shopping():
    for item_index in range(1000):
        item_name = f"Item{item_index + 1}"
        item_price = round(random.uniform(5.0, 50.0), 2)
        item = ShoppingCartAPI.create_item(item_name, item_price)

        cart = ShoppingCartAPI.create_cart()

        for _ in range(random.randint(1, 5)):
            ShoppingCartAPI.add_item_to_cart(cart['id'], item['id'])

        if random.random() < 0.2:
            fake_item_id = random.randint(1000, 9999)
            error_response = ShoppingCartAPI.add_item_to_cart(cart['id'], fake_item_id)
            print(f"Error response for adding invalid item ID {fake_item_id}: {error_response}")

        time.sleep(0.5)


if __name__ == "__main__":
    simulate_shopping()
