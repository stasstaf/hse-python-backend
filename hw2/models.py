from pydantic import BaseModel
from typing import List, Optional


class ItemBase(BaseModel):
    id: int  # идентификатор товара
    name: str  # наименование товара
    price: float  # цена товара
    deleted: bool = False  # помечен ли товар как удаленный, по умолчанию False


class ItemCreate(BaseModel):
    name: str
    price: float


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None


class CartItem(BaseModel):
    id: int  # id товара
    name: str  # название
    quantity: int  # количество товара в корзине
    available: bool  # доступен ли (не удален ли) товар


class Cart(BaseModel):
    id: int  # идентификатор корзины
    items: List[CartItem]  # список товаров в корзине
    price: float  # общая сумма заказа
