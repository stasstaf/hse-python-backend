from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from http import HTTPStatus

from typing import Optional, List, Any
from models import ItemBase, ItemCreate, ItemUpdate, CartItem, Cart
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)

items = {}
carts = {}
item_id_counter = 1
cart_id_counter = 1


@app.post("/item", status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate):
    global item_id_counter
    item_id = item_id_counter
    item_id_counter += 1
    new_item = ItemBase(id=item_id, name=item.name, price=item.price, deleted=False)
    items[item_id] = new_item
    return JSONResponse(
        content={"id": item_id, "name": new_item.name, "price": new_item.price},
        status_code=status.HTTP_201_CREATED,
        headers={"Location": f"/item/{item_id}"})


@app.get("/item/{item_id}", status_code=status.HTTP_200_OK)
def get_item(item_id: int):
    item = items.get(item_id)
    if item and not item.deleted:
        return {"id": item.id, "name": item.name, "price": item.price}
    else:
        raise HTTPException(status_code=404, detail="Item not found")


@app.get("/item", response_model=List[ItemBase])
def list_items(
        offset: int = 0,
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        show_deleted: bool = False
):
    result_items = []
    if offset < 0 or limit <= 0:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                            detail="Offset must be non-negative and limit positive")
    if any(val is not None and val < 0 for val in (min_price, max_price)):
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="Price must be non-negative")

    for item in items.values():
        if not show_deleted and item.deleted:
            continue
        if min_price is not None and item.price < min_price:
            continue
        if max_price is not None and item.price > max_price:
            continue
        result_items.append(item)

    return result_items[offset:offset + limit]


@app.put("/item/{item_id}")
def replace_item(item_id: int, item: ItemCreate):
    if item_id not in items or items[item_id].deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    items[item_id].name = item.name
    items[item_id].price = item.price
    new_item = items[item_id]
    return {"id": new_item.id, "name": new_item.name, "price": new_item.price}


@app.patch("/item/{item_id}")
def patch_item(item_id: int, body: dict[str, Any]):
    item = items.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.deleted:
        raise HTTPException(status_code=304, detail="Item is deleted")
    allowed_fields = {"name", "price"}
    if any(field not in allowed_fields for field in body):
        raise HTTPException(status_code=422, detail="Invalid field in request body")
    for key, value in body.items():
        setattr(item, key, value)
    return {"id": item.id, "name": item.name, "price": item.price}


@app.delete("/item/{item_id}")
def delete_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    items[item_id].deleted = True
    return {"message": "Item marked as deleted"}


@app.post("/cart", status_code=status.HTTP_201_CREATED)
def create_cart():
    global cart_id_counter
    cart_id = cart_id_counter
    cart_id_counter += 1
    new_cart = Cart(id=cart_id, items=[], price=0.0)
    carts[cart_id] = new_cart
    return JSONResponse(content={"id": cart_id},
                        status_code=status.HTTP_201_CREATED,
                        headers={"Location": f"/cart/{cart_id}"})


@app.get("/cart/{id}")
def get_cart(id: int):
    if id not in carts:
        raise HTTPException(status_code=404, detail="Cart not found")
    return carts[id]


@app.get("/cart", response_model=List[Cart])
def list_carts(
        offset: int = 0,
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_quantity: Optional[int] = None,
        max_quantity: Optional[int] = None
):
    if offset < 0 or limit <= 0:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                            detail="Offset must be non-negative and Limit must be positive")
    for value in [min_price, max_price, min_quantity, max_quantity]:
        if value is not None and value < 0:
            raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                                detail="Price and quantity must be a non-negative number")
    result_carts = []

    for cart in carts.values():
        total_price = 0.0
        total_quantity = 0
        updated_items = []
        for cart_item in cart.items:
            item_in_store = items.get(cart_item.id)
            if item_in_store and not item_in_store.deleted:
                cart_item.available = True
                total_price += item_in_store.price * cart_item.quantity
            else:
                cart_item.available = False
            total_quantity += cart_item.quantity
            updated_items.append(cart_item)
        cart.items = updated_items
        cart.price = total_price

        if min_price is not None and cart.price < min_price:
            continue
        if max_price is not None and cart.price > max_price:
            continue
        if min_quantity is not None and total_quantity < min_quantity:
            continue
        if max_quantity is not None and total_quantity > max_quantity:
            continue
        result_carts.append(cart)

    return result_carts[offset:offset + limit]


@app.post("/cart/{cart_id}/add/{item_id}")
def add_item_to_cart(cart_id: int, item_id: int):
    cart = carts.get(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    item = items.get(item_id)
    if not item or item.deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    for cart_item in cart.items:
        if cart_item.id == item_id:
            cart_item.quantity += 1
            break
    else:
        cart_item = CartItem(
            id=item.id,
            name=item.name,
            quantity=1,
            available=not item.deleted
        )
        cart.items.append(cart_item)
    total_price = 0.0
    for cart_item in cart.items:
        item_in_store = items.get(cart_item.id)
        if item_in_store and not item_in_store.deleted:
            total_price += item_in_store.price * cart_item.quantity
    cart.price = total_price
    return cart
