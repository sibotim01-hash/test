import asyncpg
import os

DB_PATH = "asbob_bot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                emoji TEXT DEFAULT '🔧',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                emoji TEXT DEFAULT '📦',
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                old_price REAL,
                photo_id TEXT,
                is_active INTEGER DEFAULT 1,
                is_sale INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (brand_id) REFERENCES brands(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );

            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                full_name TEXT,
                phone TEXT,
                latitude REAL,
                longitude REAL,
                total_price REAL,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            );
        """)
        await db.commit()


# ─────────────── USERS ───────────────
async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name)
        )
        await db.commit()


async def get_user_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            return row[0]


async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]


async def update_user_phone(user_id: int, phone: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET phone=? WHERE user_id=?", (phone, user_id))
        await db.commit()


# ─────────────── BRANDS ───────────────
async def get_brands() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM brands WHERE is_active=1 ORDER BY name") as cur:
            return await cur.fetchall()


async def add_brand(name: str, emoji: str = "🔧") -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO brands (name, emoji) VALUES (?, ?)", (name, emoji))
            await db.commit()
        return True
    except Exception:
        return False


async def delete_brand(brand_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM brands WHERE id=?", (brand_id,))
        await db.commit()


async def get_brand_by_name(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM brands WHERE name=?", (name,)) as cur:
            return await cur.fetchone()


# ─────────────── CATEGORIES ───────────────
async def get_categories(brand_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM categories WHERE brand_id=? AND is_active=1 ORDER BY name",
            (brand_id,)
        ) as cur:
            return await cur.fetchall()


async def add_category(brand_id: int, name: str, emoji: str = "📦") -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO categories (brand_id, name, emoji) VALUES (?, ?, ?)",
                (brand_id, name, emoji)
            )
            await db.commit()
        return True
    except Exception:
        return False


async def delete_category(category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM categories WHERE id=?", (category_id,))
        await db.commit()


async def get_category_by_name(brand_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM categories WHERE brand_id=? AND name=?",
            (brand_id, name)
        ) as cur:
            return await cur.fetchone()


async def get_all_categories() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT c.*, b.name as brand_name FROM categories c
               JOIN brands b ON c.brand_id=b.id WHERE c.is_active=1"""
        ) as cur:
            return await cur.fetchall()


# ─────────────── PRODUCTS ───────────────
async def get_products(category_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM products WHERE category_id=? AND is_active=1 ORDER BY name",
            (category_id,)
        ) as cur:
            return await cur.fetchall()


async def get_sale_products() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT p.*, b.name as brand_name, c.name as cat_name
               FROM products p
               JOIN brands b ON p.brand_id=b.id
               JOIN categories c ON p.category_id=c.id
               WHERE p.is_sale=1 AND p.is_active=1"""
        ) as cur:
            return await cur.fetchall()


async def get_product(product_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE id=?", (product_id,)) as cur:
            return await cur.fetchone()


async def add_product(brand_id: int, category_id: int, name: str, description: str,
                      price: float, photo_id: str, is_sale: int = 0, old_price: float = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO products (brand_id, category_id, name, description, price,
               old_price, photo_id, is_sale) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (brand_id, category_id, name, description, price, old_price, photo_id, is_sale)
        )
        await db.commit()


async def update_product_price(product_id: int, new_price: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE products SET price=? WHERE id=?", (new_price, product_id))
        await db.commit()


async def delete_product(product_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM products WHERE id=?", (product_id,))
        await db.commit()


async def get_all_products() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT p.*, b.name as brand_name, c.name as cat_name
               FROM products p
               JOIN brands b ON p.brand_id=b.id
               JOIN categories c ON p.category_id=c.id
               WHERE p.is_active=1 ORDER BY p.name"""
        ) as cur:
            return await cur.fetchall()


# ─────────────── CART ───────────────
async def add_to_cart(user_id: int, product_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, quantity FROM cart WHERE user_id=? AND product_id=?",
            (user_id, product_id)
        ) as cur:
            existing = await cur.fetchone()
        if existing:
            await db.execute(
                "UPDATE cart SET quantity=quantity+1 WHERE id=?",
                (existing[0],)
            )
        else:
            await db.execute(
                "INSERT INTO cart (user_id, product_id) VALUES (?, ?)",
                (user_id, product_id)
            )
        await db.commit()


async def get_cart(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT c.id, c.quantity, p.name, p.price, p.photo_id, p.id as product_id
               FROM cart c JOIN products p ON c.product_id=p.id
               WHERE c.user_id=?""",
            (user_id,)
        ) as cur:
            return await cur.fetchall()


async def remove_from_cart(cart_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM cart WHERE id=?", (cart_id,))
        await db.commit()


async def clear_cart(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
        await db.commit()


async def update_cart_quantity(cart_id: int, quantity: int):
    async with aiosqlite.connect(DB_PATH) as db:
        if quantity <= 0:
            await db.execute("DELETE FROM cart WHERE id=?", (cart_id,))
        else:
            await db.execute("UPDATE cart SET quantity=? WHERE id=?", (quantity, cart_id))
        await db.commit()


# ─────────────── ORDERS ───────────────
async def create_order(user_id: int, full_name: str, phone: str,
                       lat: float, lon: float, total: float, items: list) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO orders (user_id, full_name, phone, latitude, longitude, total_price)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, full_name, phone, lat, lon, total)
        )
        order_id = cur.lastrowid
        for item in items:
            await db.execute(
                """INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
                   VALUES (?, ?, ?, ?, ?)""",
                (order_id, item["product_id"], item["name"], item["price"], item["quantity"])
            )
        await db.commit()
        return order_id


async def get_order_items(order_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM order_items WHERE order_id=?", (order_id,)
        ) as cur:
            return await cur.fetchall()
