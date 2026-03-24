import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import hmac, hashlib, json
from urllib.parse import unquote

from database.db import (
    get_pool, init_db,
    get_brands, get_categories, get_all_categories,
    get_products, get_sale_products, get_product, get_all_products,
    add_to_cart, get_cart, remove_from_cart, clear_cart, update_cart_quantity,
    create_order, add_user, update_user_phone
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

app = FastAPI(title="Do'kon Mini App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Telegram initData tekshirish ──────────────────────────────────────────────
def verify_telegram_data(init_data: str) -> dict | None:
    """Telegram WebApp initData ni tekshiradi va user dict qaytaradi."""
    try:
        parsed = dict(item.split("=", 1) for item in init_data.split("&") if "=" in item)
        received_hash = parsed.pop("hash", "")
        check_string = "\n".join(
            f"{k}={unquote(v)}" for k, v in sorted(parsed.items())
        )
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received_hash):
            return None
        user_raw = parsed.get("user", "{}")
        return json.loads(unquote(user_raw))
    except Exception:
        return None


def get_user_from_header(init_data: str) -> dict:
    """Header'dan user oladi. Production'da verify qiladi."""
    if not BOT_TOKEN or BOT_TOKEN == "":
        # Development: initData'ni tekshirmasdan parse qilish
        try:
            parsed = dict(item.split("=", 1) for item in init_data.split("&") if "=" in item)
            return json.loads(unquote(parsed.get("user", "{}")))
        except Exception:
            return {}
    user = verify_telegram_data(init_data)
    if not user:
        raise HTTPException(status_code=403, detail="Noto'g'ri Telegram ma'lumot")
    return user


# ── Modellar ──────────────────────────────────────────────────────────────────
class CartAddRequest(BaseModel):
    product_id: int

class CartUpdateRequest(BaseModel):
    cart_id: int
    quantity: int

class OrderRequest(BaseModel):
    full_name: str
    phone: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ── Brendlar ──────────────────────────────────────────────────────────────────
@app.get("/api/brands")
async def api_get_brands():
    rows = await get_brands()
    return [dict(r) for r in rows]


# ── Kategoriyalar ─────────────────────────────────────────────────────────────
@app.get("/api/categories")
async def api_get_categories(brand_id: Optional[int] = None):
    if brand_id:
        rows = await get_categories(brand_id)
    else:
        rows = await get_all_categories()
    return [dict(r) for r in rows]


# ── Mahsulotlar ───────────────────────────────────────────────────────────────
@app.get("/api/products")
async def api_get_products(
    category_id: Optional[int] = None,
    brand_id: Optional[int] = None,
    sale: Optional[bool] = None
):
    if sale:
        rows = await get_sale_products()
    elif category_id:
        rows = await get_products(category_id)
    else:
        rows = await get_all_products()

    result = []
    for r in rows:
        row = dict(r)
        # Rasmni Telegram CDN orqali emas, file_id sifatida qaytaramiz
        # Mini App'da rasm ko'rsatish uchun alohida endpoint
        result.append(row)
    return result


@app.get("/api/products/{product_id}")
async def api_get_product(product_id: int):
    row = await get_product(product_id)
    if not row:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    return dict(row)


# ── Savatcha ──────────────────────────────────────────────────────────────────
@app.get("/api/cart")
async def api_get_cart(init_data: str = ""):
    user = get_user_from_header(init_data)
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Foydalanuvchi aniqlanmadi")
    rows = await get_cart(user_id)
    return [dict(r) for r in rows]


@app.post("/api/cart/add")
async def api_add_to_cart(body: CartAddRequest, init_data: str = ""):
    user = get_user_from_header(init_data)
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Foydalanuvchi aniqlanmadi")
    await add_to_cart(user_id, body.product_id)
    return {"ok": True}


@app.post("/api/cart/update")
async def api_update_cart(body: CartUpdateRequest, init_data: str = ""):
    user = get_user_from_header(init_data)
    if not user.get("id"):
        raise HTTPException(status_code=403, detail="Foydalanuvchi aniqlanmadi")
    await update_cart_quantity(body.cart_id, body.quantity)
    return {"ok": True}


@app.delete("/api/cart/{cart_id}")
async def api_remove_from_cart(cart_id: int, init_data: str = ""):
    user = get_user_from_header(init_data)
    if not user.get("id"):
        raise HTTPException(status_code=403, detail="Foydalanuvchi aniqlanmadi")
    await remove_from_cart(cart_id)
    return {"ok": True}


# ── Buyurtma ──────────────────────────────────────────────────────────────────
@app.post("/api/order")
async def api_create_order(body: OrderRequest, init_data: str = ""):
    user = get_user_from_header(init_data)
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Foydalanuvchi aniqlanmadi")

    cart_items = await get_cart(user_id)
    if not cart_items:
        raise HTTPException(status_code=400, detail="Savatcha bo'sh")

    total = sum(r["price"] * r["quantity"] for r in cart_items)
    items = [
        {
            "product_id": r["product_id"],
            "name": r["name"],
            "price": float(r["price"]),
            "quantity": r["quantity"]
        }
        for r in cart_items
    ]

    order_id = await create_order(
        user_id=user_id,
        full_name=body.full_name,
        phone=body.phone,
        lat=body.latitude,
        lon=body.longitude,
        total=float(total),
        items=items
    )
    await clear_cart(user_id)
    await update_user_phone(user_id, body.phone)

    return {"ok": True, "order_id": order_id, "total": float(total)}


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await init_db()


# ── Static fayllar (Mini App HTML/CSS/JS) ─────────────────────────────────────
app.mount("/", StaticFiles(directory="miniapp", html=True), name="miniapp")
