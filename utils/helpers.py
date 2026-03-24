from config import ADMIN_IDS


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def format_price(price: float) -> str:
    return f"{price:,.0f} so'm".replace(",", " ")


def format_product_text(product) -> str:
    text = f"<b>{product['name']}</b>\n"
    if product['description']:
        text += f"\n{product['description']}\n"
    if product['is_sale'] and product['old_price']:
        text += f"\n<s>{format_price(product['old_price'])}</s>"
        text += f" → <b>🏷 {format_price(product['price'])}</b>"
    else:
        text += f"\n💰 <b>{format_price(product['price'])}</b>"
    return text
