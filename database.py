import sqlite3
import os
from datetime import datetime
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(__file__), "cafe.db")


class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_db()

    def init_db(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS dishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL CHECK(price > 0),
                category_id INTEGER NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_number INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Принят',
                created_at TEXT NOT NULL,
                total REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                dish_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                price REAL NOT NULL CHECK(price > 0),
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE RESTRICT
            );
        """)
        self.conn.commit()

    # ---- Categories ----

    def get_categories(self):
        cursor = self.conn.execute("SELECT * FROM categories ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def add_category(self, name: str) -> int:
        cursor = self.conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        self.conn.commit()
        return cursor.lastrowid

    def update_category(self, id: int, name: str):
        self.conn.execute("UPDATE categories SET name = ? WHERE id = ?", (name, id))
        self.conn.commit()

    def delete_category(self, id: int):
        self.conn.execute("DELETE FROM categories WHERE id = ?", (id,))
        self.conn.commit()

    def get_category_dish_count(self, id: int) -> int:
        cursor = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM dishes WHERE category_id = ?", (id,)
        )
        return cursor.fetchone()["cnt"]

    # ---- Dishes ----

    def get_dishes(self, category_id: Optional[int] = None):
        if category_id is not None:
            cursor = self.conn.execute(
                """SELECT d.*, c.name as category_name
                   FROM dishes d
                   JOIN categories c ON d.category_id = c.id
                   WHERE d.category_id = ?
                   ORDER BY d.name""",
                (category_id,),
            )
        else:
            cursor = self.conn.execute(
                """SELECT d.*, c.name as category_name
                   FROM dishes d
                   JOIN categories c ON d.category_id = c.id
                   ORDER BY d.name"""
            )
        return [dict(row) for row in cursor.fetchall()]

    def get_dish(self, dish_id: int):
        cursor = self.conn.execute(
            """SELECT d.*, c.name as category_name
               FROM dishes d
               JOIN categories c ON d.category_id = c.id
               WHERE d.id = ?""",
            (dish_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def add_dish(self, name: str, price: float, category_id: int) -> int:
        cursor = self.conn.execute(
            "INSERT INTO dishes (name, price, category_id) VALUES (?, ?, ?)",
            (name, price, category_id),
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_dish(self, id: int, name: str, price: float, category_id: int):
        self.conn.execute(
            "UPDATE dishes SET name = ?, price = ?, category_id = ? WHERE id = ?",
            (name, price, category_id, id),
        )
        self.conn.commit()

    def delete_dish(self, id: int):
        self.conn.execute("DELETE FROM dishes WHERE id = ?", (id,))
        self.conn.commit()

    def get_dish_order_count(self, id: int) -> int:
        cursor = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM order_items WHERE dish_id = ?", (id,)
        )
        return cursor.fetchone()["cnt"]

    # ---- Orders ----

    def create_order(self, table_number: int) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.conn.execute(
            "INSERT INTO orders (table_number, status, created_at, total) VALUES (?, 'Принят', ?, 0)",
            (table_number, now),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_orders(self, status: Optional[str] = None):
        if status:
            cursor = self.conn.execute(
                "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM orders ORDER BY created_at DESC"
            )
        return [dict(row) for row in cursor.fetchall()]

    def get_order(self, order_id: int):
        cursor = self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_order_status(self, order_id: int, status: str):
        self.conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
        )
        self.conn.commit()

    def update_order_total(self, order_id: int) -> float:
        cursor = self.conn.execute(
            "SELECT SUM(quantity * price) as total FROM order_items WHERE order_id = ?",
            (order_id,),
        )
        total = cursor.fetchone()["total"] or 0.0
        self.conn.execute(
            "UPDATE orders SET total = ? WHERE id = ?", (total, order_id)
        )
        self.conn.commit()
        return total

    def cancel_order(self, order_id: int):
        self.conn.execute(
            "UPDATE orders SET status = 'Отменен' WHERE id = ?", (order_id,)
        )
        self.conn.commit()

    # ---- Order Items ----

    def add_order_item(self, order_id: int, dish_id: int, quantity: int, price: float):
        self.conn.execute(
            "INSERT INTO order_items (order_id, dish_id, quantity, price) VALUES (?, ?, ?, ?)",
            (order_id, dish_id, quantity, price),
        )
        self.conn.commit()

    def get_order_items(self, order_id: int):
        cursor = self.conn.execute(
            """SELECT oi.*, d.name as dish_name
               FROM order_items oi
               JOIN dishes d ON oi.dish_id = d.id
               WHERE oi.order_id = ?""",
            (order_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def remove_order_item(self, item_id: int):
        self.conn.execute("DELETE FROM order_items WHERE id = ?", (item_id,))
        self.conn.commit()

    # ---- Reports ----

    def get_sales_report(self, start_date: str, end_date: str):
        cursor = self.conn.execute(
            """SELECT DATE(created_at) as day,
                      COUNT(*) as order_count,
                      SUM(total) as total_sales
               FROM orders
               WHERE status = 'Оплачен'
                 AND DATE(created_at) BETWEEN ? AND ?
               GROUP BY DATE(created_at)
               ORDER BY day""",
            (start_date, end_date),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_detailed_sales(self, start_date: str, end_date: str):
        cursor = self.conn.execute(
            """SELECT d.name as dish_name,
                      SUM(oi.quantity) as total_qty,
                      SUM(oi.quantity * oi.price) as total_sum
               FROM order_items oi
               JOIN dishes d ON oi.dish_id = d.id
               JOIN orders o ON oi.order_id = o.id
               WHERE o.status = 'Оплачен'
                 AND DATE(o.created_at) BETWEEN ? AND ?
               GROUP BY d.id, d.name
               ORDER BY total_sum DESC""",
            (start_date, end_date),
        )
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()


class OrderManager:
    VALID_TRANSITIONS = {
        "Принят": ["Готовится", "Отменен"],
        "Готовится": ["Готов", "Отменен"],
        "Готов": ["Оплачен"],
        "Оплачен": [],
        "Отменен": [],
    }

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_next_statuses(self, current_status: str) -> list:
        return self.VALID_TRANSITIONS.get(current_status, [])

    def change_status(self, order_id: int, new_status: str):
        order = self.db.get_order(order_id)
        if not order:
            return False, "Заказ не найден"
        current = order["status"]
        allowed = self.get_next_statuses(current)
        if new_status not in allowed:
            return (
                False,
                f"Невозможно перевести заказ из статуса "
                f"'{current}' в '{new_status}'",
            )
        self.db.update_order_status(order_id, new_status)
        return True, f"Статус заказа №{order_id} изменен на '{new_status}'"

    def add_item_to_order(self, order_id: int, dish_id: int, quantity: int, price: float):
        self.db.add_order_item(order_id, dish_id, quantity, price)
        self.db.update_order_total(order_id)
        return True, "Позиция добавлена в заказ"

    def remove_item_from_order(self, item_id: int, order_id: int):
        self.db.remove_order_item(item_id)
        self.db.update_order_total(order_id)
        return True, "Позиция удалена из заказа"
