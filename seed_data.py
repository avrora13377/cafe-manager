from database import DatabaseManager
from datetime import datetime, timedelta
import random


def seed():
    db = DatabaseManager()

    # Clear existing data so script is idempotent
    db.conn.executescript("""
        DELETE FROM order_items;
        DELETE FROM orders;
        DELETE FROM dishes;
        DELETE FROM categories;
    """)
    db.conn.commit()

    # Categories
    categories = ["Пицца", "Салаты", "Напитки", "Десерты", "Супы"]
    cat_ids = {}
    for name in categories:
        cat_id = db.add_category(name)
        cat_ids[name] = cat_id

    # Dishes
    dishes_data = [
        ("Маргарита", 450.0, "Пицца"),
        ("Пепперони", 520.0, "Пицца"),
        ("Четыре сыра", 580.0, "Пицца"),
        ("Гавайская", 490.0, "Пицца"),
        ("Цезарь с курицей", 350.0, "Салаты"),
        ("Греческий салат", 320.0, "Салаты"),
        ("Овощной салат", 280.0, "Салаты"),
        ("Кола", 150.0, "Напитки"),
        ("Сок апельсиновый", 180.0, "Напитки"),
        ("Чай черный", 100.0, "Напитки"),
        ("Кофе американо", 200.0, "Напитки"),
        ("Чизкейк", 350.0, "Десерты"),
        ("Тирамису", 380.0, "Десерты"),
        ("Мороженое", 220.0, "Десерты"),
        ("Куриный суп", 250.0, "Супы"),
        ("Томатный суп", 280.0, "Супы"),
    ]
    dish_ids = {}
    for name, price, cat_name in dishes_data:
        d_id = db.add_dish(name, price, cat_ids[cat_name])
        dish_ids[name] = d_id

    # Orders with items
    today = datetime.now()
    statuses = ["Принят", "Готовится", "Готов", "Оплачен", "Отменен"]

    for i in range(10):
        table = random.randint(1, 8)
        created = today - timedelta(hours=random.randint(1, 72))
        status = random.choice(statuses)

        order_id = db.create_order(table)

        # Override created_at and status
        db.conn.execute(
            "UPDATE orders SET created_at = ?, status = ? WHERE id = ?",
            (created.strftime("%Y-%m-%d %H:%M:%S"), status, order_id),
        )
        db.conn.commit()

        # Add items
        items_count = random.randint(1, 4)
        selected_dishes = random.sample(list(dish_ids.values()), min(items_count, len(dish_ids)))
        for d_id in selected_dishes:
            dish = db.get_dish(d_id)
            qty = random.randint(1, 3)
            db.add_order_item(order_id, d_id, qty, dish["price"])

        db.update_order_total(order_id)

    print("Тестовые данные успешно добавлены!")

    # Summary
    orders = db.get_orders()
    items = db.get_order_items(orders[0]["id"]) if orders else []
    print(f"Добавлено категорий: {len(categories)}")
    print(f"Добавлено блюд: {len(dishes_data)}")
    print(f"Создано заказов: {len(orders)}")

    db.close()


if __name__ == "__main__":
    seed()
