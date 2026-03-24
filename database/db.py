import asyncpg
import os

_pool: asyncpg.Pool = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL"),
            min_size=1,
            max_size=10,
            ssl="require"
        )
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS brands (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                emoji TEXT DEFAULT '🔧',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                emoji TEXT DEFAULT '📦',
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                brand_id INTEGER NOT NULL REFERENCES brands(id),
                category_id INTEGER NOT NULL REFERENCES categories(id),
                name TEXT NOT NULL,
                description TEXT,
                price NUMERIC NOT NULL,
                old_price NUMERIC,
                photo_id TEXT,
                is_active INTEGER DEFAULT 1,
                is_sale INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS cart (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                full_name TEXT,
                phone TEXT,
                latitude NUMERIC,
                longitude NUMERIC,
                total_price NUMERIC,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(id),
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price NUMERIC NOT NULL,
                quantity INTEGER NOT NULL
            );
        """)


# ─────────────── USERS ───────────────
async def add_user(user_id: int, username: str, full_name: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO users (user_id, username, full_name)
               VALUES ($1, $2, $3) ON CONFLICT (user_id) DO NOTHING""",
            user_id, username, full_name
        )


async def get_user_count() -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM users")


async def get_all_user_ids() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM users")
        return [r["user_id"] for r in rows]


async def update_user_phone(user_id: int, phone: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET phone=$1 WHERE user_id=$2", phone, user_id
        )


# ─────────────── BRANDS ───────────────
async def get_brands() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM brands WHERE is_active=1 ORDER BY name"
        )


async def add_brand(name: str, emoji: str = "🔧") -> bool:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO brands (name, emoji) VALUES ($1, $2)", name, emoji
            )
        return True
    except Exception:
        return False


async def delete_brand(brand_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM brands WHERE id=$1", brand_id)


async def get_brand_by_name(name: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM brands WHERE name=$1", name)


# ─────────────── CATEGORIES ───────────────
async def get_categories(brand_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM categories WHERE brand_id=$1 AND is_active=1 ORDER BY name",
            brand_id
        )


async def add_category(brand_id: int, name: str, emoji: str = "📦") -> bool:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO categories (brand_id, name, emoji) VALUES ($1, $2, $3)",
                brand_id, name, emoji
            )
        return True
    except Exception:
        return False


async def delete_category(category_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM categories WHERE id=$1", category_id)


async def get_all_categories() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            """SELECT c.*, b.name as brand_name FROM categories c
               JOIN brands b ON c.brand_id=b.id WHERE c.is_active=1"""
        )


# ─────────────── PRODUCTS ───────────────
async def get_products(category_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM products WHERE category_id=$1 AND is_active=1 ORDER BY name",
            category_id
        )


async def get_sale_products() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            """SELECT p.*, b.name as brand_name, c.name as cat_name
               FROM products p
               JOIN brands b ON p.brand_id=b.id
               JOIN categories c ON p.category_id=c.id
               WHERE p.is_sale=1 AND p.is_active=1"""
        )


async def get_product(product_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM products WHERE id=$1", product_id
        )


async def add_product(brand_id: int, category_id: int, name: str, description: str,
                      price: float, photo_id: str, is_sale: int = 0, old_price: float = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO products
               (brand_id, category_id, name, description, price, old_price, photo_id, is_sale)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            brand_id, category_id, name, description,
            price, old_price, photo_id, is_sale
        )


async def update_product_price(product_id: int, new_price: float):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE products SET price=$1 WHERE id=$2", new_price, product_id
        )


async def delete_product(product_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM products WHERE id=$1", product_id)


async def get_all_products() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            """SELECT p.*, b.name as brand_name, c.name as cat_name
               FROM products p
               JOIN brands b ON p.brand_id=b.id
               JOIN categories c ON p.category_id=c.id
               WHERE p.is_active=1 ORDER BY p.name"""
        )


# ─────────────── CART ───────────────
async def add_to_cart(user_id: int, product_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id, quantity FROM cart WHERE user_id=$1 AND product_id=$2",
            user_id, product_id
        )
        if existing:
            await conn.execute(
                "UPDATE cart SET quantity=quantity+1 WHERE id=$1", existing["id"]
            )
        else:
            await conn.execute(
                "INSERT INTO cart (user_id, product_id) VALUES ($1, $2)",
                user_id, product_id
            )


async def get_cart(user_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            """SELECT c.id, c.quantity, p.name, p.price, p.photo_id, p.id as product_id
               FROM cart c JOIN products p ON c.product_id=p.id
               WHERE c.user_id=$1""",
            user_id
        )


async def remove_from_cart(cart_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM cart WHERE id=$1", cart_id)


async def clear_cart(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM cart WHERE user_id=$1", user_id)


async def update_cart_quantity(cart_id: int, quantity: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if quantity <= 0:
            await conn.execute("DELETE FROM cart WHERE id=$1", cart_id)
        else:
            await conn.execute(
                "UPDATE cart SET quantity=$1 WHERE id=$2", quantity, cart_id
            )


# ─────────────── ORDERS ───────────────
async def create_order(user_id: int, full_name: str, phone: str,
                       lat: float, lon: float, total: float, items: list) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        order_id = await conn.fetchval(
            """INSERT INTO orders (user_id, full_name, phone, latitude, longitude, total_price)
               VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
            user_id, full_name, phone, lat, lon, total
        )
        for item in items:
            await conn.execute(
                """INSERT INTO order_items
                   (order_id, product_id, product_name, price, quantity)
                   VALUES ($1, $2, $3, $4, $5)""",
                order_id, item["product_id"], item["name"],
                item["price"], item["quantity"]
            )
        return order_id


async def get_order_items(order_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM order_items WHERE order_id=$1", order_id
        )
