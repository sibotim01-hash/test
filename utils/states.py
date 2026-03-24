from aiogram.fsm.state import State, StatesGroup


class CatalogState(StatesGroup):
    choosing_brand = State()
    choosing_category = State()
    viewing_products = State()


class CartState(StatesGroup):
    viewing = State()
    waiting_contact = State()
    waiting_location = State()
    confirming = State()


class AdminState(StatesGroup):
    main = State()

    # Brend
    add_brand_name = State()
    add_brand_emoji = State()

    # Kategoriya
    add_cat_brand = State()
    add_cat_name = State()
    add_cat_emoji = State()

    # Mahsulot
    add_prod_brand = State()
    add_prod_cat = State()
    add_prod_name = State()
    add_prod_desc = State()
    add_prod_price = State()
    add_prod_photo = State()
    add_prod_sale = State()
    add_prod_old_price = State()

    # Narx tahrirlash
    edit_price_value = State()

    # Broadcast
    broadcast_text = State()
    broadcast_photo = State()


class BroadcastState(StatesGroup):
    waiting_content = State()
    confirm = State()
