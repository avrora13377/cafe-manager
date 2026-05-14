import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime, date
import csv
import os

from database import DatabaseManager, OrderManager
from sound import order_placed, status_changed, item_added, error, cancel as sound_cancel


class MenuTab(ttk.Frame):
    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent)
        self.db = db
        self.current_category_id = None
        self.create_widgets()
        self.refresh_categories()

    def create_widgets(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ---- Left: Categories ----
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Категории", font=("", 12, "bold")).pack(
            anchor=tk.W, pady=(0, 5)
        )

        cat_columns = ("id", "name")
        self.cat_tree = ttk.Treeview(
            left_frame, columns=cat_columns, show="headings", height=12
        )
        self.cat_tree.heading("id", text="ID")
        self.cat_tree.heading("name", text="Название")
        self.cat_tree.column("id", width=40, anchor=tk.CENTER)
        self.cat_tree.column("name", width=200)
        self.cat_tree.pack(fill=tk.BOTH, expand=True)
        self.cat_tree.bind("<<TreeviewSelect>>", self.on_category_select)

        cat_btn_frame = ttk.Frame(left_frame)
        cat_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(cat_btn_frame, text="Добавить", command=self.add_category).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(cat_btn_frame, text="Изменить", command=self.edit_category).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(cat_btn_frame, text="Удалить", command=self.delete_category).pack(
            side=tk.LEFT, padx=2
        )

        # ---- Right: Dishes ----
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        ttk.Label(right_frame, text="Блюда", font=("", 12, "bold")).pack(
            anchor=tk.W, pady=(0, 5)
        )

        dish_columns = ("id", "name", "price", "category_name")
        self.dish_tree = ttk.Treeview(
            right_frame, columns=dish_columns, show="headings", height=12
        )
        self.dish_tree.heading("id", text="ID")
        self.dish_tree.heading("name", text="Название")
        self.dish_tree.heading("price", text="Цена (₽)")
        self.dish_tree.heading("category_name", text="Категория")
        self.dish_tree.column("id", width=40, anchor=tk.CENTER)
        self.dish_tree.column("name", width=200)
        self.dish_tree.column("price", width=100, anchor=tk.CENTER)
        self.dish_tree.column("category_name", width=150)
        self.dish_tree.pack(fill=tk.BOTH, expand=True)

        dish_btn_frame = ttk.Frame(right_frame)
        dish_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(dish_btn_frame, text="Добавить", command=self.add_dish).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(dish_btn_frame, text="Изменить", command=self.edit_dish).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(dish_btn_frame, text="Удалить", command=self.delete_dish).pack(
            side=tk.LEFT, padx=2
        )

    # ---- Category handlers ----

    def refresh_categories(self):
        for row in self.cat_tree.get_children():
            self.cat_tree.delete(row)
        categories = self.db.get_categories()
        for cat in categories:
            self.cat_tree.insert("", tk.END, values=(cat["id"], cat["name"]))
        self.refresh_dishes()

    def get_selected_category(self):
        sel = self.cat_tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите категорию")
            return None
        return self.cat_tree.item(sel[0])["values"]

    def on_category_select(self, event=None):
        sel = self.cat_tree.selection()
        if sel:
            vals = self.cat_tree.item(sel[0])["values"]
            self.current_category_id = vals[0]
        else:
            self.current_category_id = None
        self.refresh_dishes()

    def add_category(self):
        name = simpledialog.askstring("Добавление категории", "Введите название категории:")
        if name:
            name = name.strip()
            if not name:
                messagebox.showerror("Ошибка", "Название не может быть пустым")
                return
            try:
                self.db.add_category(name)
                self.refresh_categories()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Категория уже существует: {e}")

    def edit_category(self):
        vals = self.get_selected_category()
        if not vals:
            return
        cat_id, old_name = vals
        name = simpledialog.askstring(
            "Изменение категории", "Введите новое название:", initialvalue=old_name
        )
        if name:
            name = name.strip()
            if not name:
                messagebox.showerror("Ошибка", "Название не может быть пустым")
                return
            try:
                self.db.update_category(cat_id, name)
                self.refresh_categories()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def delete_category(self):
        vals = self.get_selected_category()
        if not vals:
            return
        cat_id, name = vals
        count = self.db.get_category_dish_count(cat_id)
        if count > 0:
            messagebox.showerror(
                "Ошибка",
                f"Нельзя удалить категорию '{name}': "
                f"в ней {count} блюд(а/о). Сначала удалите блюда.",
            )
            return
        if messagebox.askyesno("Подтверждение", f"Удалить категорию '{name}'?"):
            self.db.delete_category(cat_id)
            self.refresh_categories()

    # ---- Dish handlers ----

    def refresh_dishes(self):
        for row in self.dish_tree.get_children():
            self.dish_tree.delete(row)
        dishes = self.db.get_dishes(category_id=self.current_category_id)
        for d in dishes:
            self.dish_tree.insert(
                "",
                tk.END,
                values=(d["id"], d["name"], f"{d['price']:.2f}", d["category_name"]),
            )

    def get_selected_dish(self):
        sel = self.dish_tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите блюдо")
            return None
        return self.dish_tree.item(sel[0])["values"]

    def add_dish(self):
        categories = self.db.get_categories()
        if not categories:
            messagebox.showwarning("Внимание", "Сначала создайте хотя бы одну категорию")
            return

        dialog = DishEditDialog(self, "Добавление блюда", None, categories)
        self.wait_window(dialog)
        if dialog.result:
            self.db.add_dish(dialog.result["name"], dialog.result["price"], dialog.result["category_id"])
            self.refresh_dishes()

    def edit_dish(self):
        vals = self.get_selected_dish()
        if not vals:
            return
        dish_id, old_name, old_price_str, _ = vals
        old_price = float(old_price_str.replace(",", "."))
        dish = self.db.get_dish(dish_id)
        if not dish:
            messagebox.showerror("Ошибка", "Блюдо не найдено")
            return

        categories = self.db.get_categories()
        dialog = DishEditDialog(self, "Изменение блюда", dish, categories)
        self.wait_window(dialog)
        if dialog.result:
            self.db.update_dish(
                dish_id,
                dialog.result["name"],
                dialog.result["price"],
                dialog.result["category_id"],
            )
            self.refresh_dishes()

    def delete_dish(self):
        vals = self.get_selected_dish()
        if not vals:
            return
        dish_id, name, _, _ = vals
        count = self.db.get_dish_order_count(dish_id)
        if count > 0:
            messagebox.showerror(
                "Ошибка",
                f"Нельзя удалить блюдо '{name}': оно используется в {count} заказах.",
            )
            return
        if messagebox.askyesno("Подтверждение", f"Удалить блюдо '{name}'?"):
            self.db.delete_dish(dish_id)
            self.refresh_dishes()


class DishEditDialog(tk.Toplevel):
    def __init__(self, parent, title, dish, categories):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.categories = categories

        pad = {"padx": 10, "pady": 5}

        ttk.Label(self, text="Название:").grid(row=0, column=0, sticky=tk.W, **pad)
        self.name_var = tk.StringVar(value=dish["name"] if dish else "")
        self.name_entry = ttk.Entry(self, textvariable=self.name_var, width=35)
        self.name_entry.grid(row=0, column=1, **pad)

        ttk.Label(self, text="Цена (₽):").grid(row=1, column=0, sticky=tk.W, **pad)
        self.price_var = tk.StringVar(
            value=f"{dish['price']:.2f}" if dish else ""
        )
        self.price_entry = ttk.Entry(self, textvariable=self.price_var, width=35)
        self.price_entry.grid(row=1, column=1, **pad)

        ttk.Label(self, text="Категория:").grid(row=2, column=0, sticky=tk.W, **pad)
        self.category_var = tk.IntVar(
            value=dish["category_id"] if dish else categories[0]["id"]
        )
        self.cat_combo = ttk.Combobox(
            self,
            textvariable=self.category_var,
            values=[c["name"] for c in categories],
            state="readonly",
            width=32,
        )
        self.cat_combo.grid(row=2, column=1, **pad)
        if dish:
            default_idx = next(
                (i for i, c in enumerate(categories) if c["id"] == dish["category_id"]), 0
            )
        else:
            default_idx = 0
        self.cat_combo.current(default_idx)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(
            side=tk.LEFT, padx=5
        )

        self.grab_set()
        self.name_entry.focus_set()

    def on_ok(self):
        name = self.name_var.get().strip()
        price_str = self.price_var.get().strip().replace(",", ".")
        if not name:
            messagebox.showerror("Ошибка", "Введите название блюда")
            return
        try:
            price = float(price_str)
            if price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную цену (положительное число)")
            return
        cat_name = self.cat_combo.get()
        cat_id = None
        for c in self.categories:
            if c["name"] == cat_name:
                cat_id = c["id"]
                break
        if cat_id is None:
            messagebox.showerror("Ошибка", "Выберите категорию")
            return
        self.result = {"name": name, "price": price, "category_id": cat_id}
        self.destroy()


class OrdersTab(ttk.Frame):
    def __init__(self, parent, db: DatabaseManager, order_manager: OrderManager):
        super().__init__(parent)
        self.db = db
        self.om = order_manager
        self.current_order_id = None
        self.create_widgets()
        self.refresh_orders()

    def create_widgets(self):
        # ---- Toolbar ----
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Новый заказ", command=self.new_order).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(toolbar, text="Сменить статус", command=self.change_status).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(toolbar, text="Отменить заказ", command=self.cancel_order).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(toolbar, text="Обновить", command=self.refresh_orders).pack(
            side=tk.RIGHT, padx=2
        )

        # ---- Filter ----
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Label(filter_frame, text="Фильтр по статусу:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_filter_var = tk.StringVar(value="Все")
        self.status_filter = ttk.Combobox(
            filter_frame,
            textvariable=self.status_filter_var,
            values=["Все", "Принят", "Готовится", "Готов", "Оплачен", "Отменен"],
            state="readonly",
            width=15,
        )
        self.status_filter.pack(side=tk.LEFT)
        self.status_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_orders())

        # ---- Orders table ----
        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        top_frame = ttk.Frame(paned)
        paned.add(top_frame, weight=2)

        ttk.Label(top_frame, text="Заказы", font=("", 12, "bold")).pack(
            anchor=tk.W, pady=(0, 5)
        )

        order_columns = ("id", "table_number", "status", "created_at", "total")
        self.order_tree = ttk.Treeview(
            top_frame, columns=order_columns, show="headings", height=8
        )
        self.order_tree.heading("id", text="№")
        self.order_tree.heading("table_number", text="Стол")
        self.order_tree.heading("status", text="Статус")
        self.order_tree.heading("created_at", text="Дата")
        self.order_tree.heading("total", text="Сумма (₽)")
        self.order_tree.column("id", width=50, anchor=tk.CENTER)
        self.order_tree.column("table_number", width=60, anchor=tk.CENTER)
        self.order_tree.column("status", width=100, anchor=tk.CENTER)
        self.order_tree.column("created_at", width=160, anchor=tk.CENTER)
        self.order_tree.column("total", width=100, anchor=tk.CENTER)
        self.order_tree.pack(fill=tk.BOTH, expand=True)
        self.order_tree.bind("<<TreeviewSelect>>", self.on_order_select)

        # ---- Order items ----
        bottom_frame = ttk.Frame(paned)
        paned.add(bottom_frame, weight=1)

        items_header = ttk.Frame(bottom_frame)
        items_header.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(
            items_header, text="Позиции заказа", font=("", 12, "bold")
        ).pack(side=tk.LEFT)
        self.total_label = ttk.Label(items_header, text="", font=("", 11, "bold"))
        self.total_label.pack(side=tk.RIGHT, padx=10)

        item_columns = ("id", "dish_name", "quantity", "price", "subtotal")
        self.item_tree = ttk.Treeview(
            bottom_frame, columns=item_columns, show="headings", height=5
        )
        self.item_tree.heading("id", text="ID")
        self.item_tree.heading("dish_name", text="Блюдо")
        self.item_tree.heading("quantity", text="Кол-во")
        self.item_tree.heading("price", text="Цена (₽)")
        self.item_tree.heading("subtotal", text="Сумма (₽)")
        self.item_tree.column("id", width=40, anchor=tk.CENTER)
        self.item_tree.column("dish_name", width=200)
        self.item_tree.column("quantity", width=60, anchor=tk.CENTER)
        self.item_tree.column("price", width=80, anchor=tk.CENTER)
        self.item_tree.column("subtotal", width=90, anchor=tk.CENTER)
        self.item_tree.pack(fill=tk.BOTH, expand=True)

        item_btn_frame = ttk.Frame(bottom_frame)
        item_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(
            item_btn_frame, text="Добавить позицию", command=self.add_item
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            item_btn_frame, text="Удалить позицию", command=self.remove_item
        ).pack(side=tk.LEFT, padx=2)

    # ---- Order handlers ----

    def refresh_orders(self):
        for row in self.order_tree.get_children():
            self.order_tree.delete(row)
        status = self.status_filter_var.get()
        filter_val = None if status == "Все" else status
        orders = self.db.get_orders(status=filter_val)
        for o in orders:
            self.order_tree.insert(
                "",
                tk.END,
                values=(
                    o["id"],
                    o["table_number"],
                    o["status"],
                    o["created_at"],
                    f"{o['total']:.2f}",
                ),
            )
        if not self.order_tree.selection():
            self.clear_items()

    def get_selected_order(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите заказ")
            return None
        return self.order_tree.item(sel[0])["values"]

    def get_selected_order_id(self):
        vals = self.get_selected_order()
        return vals[0] if vals else None

    def on_order_select(self, event=None):
        sel = self.order_tree.selection()
        if sel:
            vals = self.order_tree.item(sel[0])["values"]
            self.current_order_id = int(vals[0])
            self.refresh_items()
        else:
            self.current_order_id = None
            self.clear_items()

    def clear_items(self):
        for row in self.item_tree.get_children():
            self.item_tree.delete(row)
        self.total_label.config(text="")

    def new_order(self):
        table_str = simpledialog.askstring(
            "Новый заказ", "Введите номер стола:", initialvalue="1"
        )
        if table_str:
            try:
                table_num = int(table_str)
                if table_num <= 0:
                    raise ValueError
                order_id = self.db.create_order(table_num)
                order_placed()
                messagebox.showinfo(
                    "Успешно", f"Создан заказ №{order_id} для стола {table_num}"
                )
                self.refresh_orders()
                # Select the new order
                for child in self.order_tree.get_children():
                    if self.order_tree.item(child)["values"][0] == order_id:
                        self.order_tree.selection_set(child)
                        self.order_tree.focus(child)
                        break
            except ValueError:
                error()
                messagebox.showerror("Ошибка", "Введите корректный номер стола")

    def change_status(self):
        order_id = self.get_selected_order_id()
        if not order_id:
            return
        order = self.db.get_order(order_id)
        if not order:
            return
        current = order["status"]
        next_statuses = self.om.get_next_statuses(current)
        if not next_statuses:
            messagebox.showinfo(
                "Информация",
                f"Заказ №{order_id} в статусе '{current}'. Дальнейшие переходы невозможны.",
            )
            return

        dialog = StatusDialog(self, f"Смена статуса заказа №{order_id}", next_statuses)
        self.wait_window(dialog)
        if dialog.result:
            success, msg = self.om.change_status(order_id, dialog.result)
            if success:
                status_changed()
                self.refresh_orders()
                self.on_order_select()
            messagebox.showinfo("Результат", msg)

    def cancel_order(self):
        order_id = self.get_selected_order_id()
        if not order_id:
            return
        order = self.db.get_order(order_id)
        if not order:
            return
        current = order["status"]
        if current in ("Оплачен", "Отменен"):
            messagebox.showinfo(
                "Информация",
                f"Заказ №{order_id} в статусе '{current}'. Отмена невозможна.",
            )
            return
        if messagebox.askyesno("Подтверждение", f"Отменить заказ №{order_id}?"):
            self.db.cancel_order(order_id)
            sound_cancel()
            messagebox.showinfo("Успешно", f"Заказ №{order_id} отменен")
            self.refresh_orders()
            self.on_order_select()

    # ---- Item handlers ----

    def refresh_items(self):
        for row in self.item_tree.get_children():
            self.item_tree.delete(row)
        if not self.current_order_id:
            self.total_label.config(text="")
            return
        items = self.db.get_order_items(self.current_order_id)
        for item in items:
            subtotal = item["quantity"] * item["price"]
            self.item_tree.insert(
                "",
                tk.END,
                values=(
                    item["id"],
                    item["dish_name"],
                    item["quantity"],
                    f"{item['price']:.2f}",
                    f"{subtotal:.2f}",
                ),
            )
        order = self.db.get_order(self.current_order_id)
        if order:
            self.total_label.config(text=f"ИТОГО: {order['total']:.2f} ₽")

    def add_item(self):
        order_id = self.get_selected_order_id()
        if not order_id:
            return
        order = self.db.get_order(order_id)
        if order and order["status"] != "Принят":
            messagebox.showwarning(
                "Внимание",
                "Добавлять позиции можно только в заказы со статусом 'Принят'",
            )
            return

        dishes = self.db.get_dishes()
        if not dishes:
            messagebox.showwarning("Внимание", "Нет блюд в меню. Сначала добавьте блюда.")
            return

        dialog = AddItemDialog(self, "Добавление позиции", dishes)
        self.wait_window(dialog)
        if dialog.result:
            success, msg = self.om.add_item_to_order(
                order_id,
                dialog.result["dish_id"],
                dialog.result["quantity"],
                dialog.result["price"],
            )
            item_added()
            self.refresh_orders()
            self.refresh_items()
            messagebox.showinfo("Результат", msg)

    def remove_item(self):
        order_id = self.get_selected_order_id()
        if not order_id:
            return
        sel = self.item_tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите позицию для удаления")
            return
        item_id = int(self.item_tree.item(sel[0])["values"][0])
        if messagebox.askyesno("Подтверждение", "Удалить позицию из заказа?"):
            success, msg = self.om.remove_item_from_order(item_id, order_id)
            item_added()
            self.refresh_orders()
            self.refresh_items()
            messagebox.showinfo("Результат", msg)


class StatusDialog(tk.Toplevel):
    def __init__(self, parent, title, statuses):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None

        ttk.Label(self, text="Выберите новый статус:", padding=10).pack()

        self.status_var = tk.StringVar(value=statuses[0])
        for s in statuses:
            ttk.Radiobutton(
                self, text=s, variable=self.status_var, value=s, padding=5
            ).pack(anchor=tk.W, padx=20)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(
            side=tk.LEFT, padx=5
        )

        self.grab_set()

    def on_ok(self):
        self.result = self.status_var.get()
        self.destroy()


class AddItemDialog(tk.Toplevel):
    def __init__(self, parent, title, dishes):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.dishes = dishes

        pad = {"padx": 10, "pady": 5}

        ttk.Label(self, text="Блюдо:").grid(row=0, column=0, sticky=tk.W, **pad)
        dish_names = [f"{d['id']}: {d['name']} ({d['price']:.2f} ₽)" for d in dishes]
        self.dish_var = tk.StringVar()
        self.dish_combo = ttk.Combobox(
            self,
            textvariable=self.dish_var,
            values=dish_names,
            state="readonly",
            width=40,
        )
        self.dish_combo.grid(row=0, column=1, **pad)
        if dish_names:
            self.dish_combo.current(0)

        ttk.Label(self, text="Количество:").grid(row=1, column=0, sticky=tk.W, **pad)
        self.qty_var = tk.StringVar(value="1")
        self.qty_entry = ttk.Entry(self, textvariable=self.qty_var, width=38)
        self.qty_entry.grid(row=1, column=1, **pad)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(
            side=tk.LEFT, padx=5
        )

        self.grab_set()

    def on_ok(self):
        dish_str = self.dish_combo.get()
        if not dish_str:
            messagebox.showerror("Ошибка", "Выберите блюдо")
            return
        try:
            dish_id = int(dish_str.split(":")[0])
        except (ValueError, IndexError):
            messagebox.showerror("Ошибка", "Выберите блюдо из списка")
            return
        qty_str = self.qty_var.get().strip()
        try:
            qty = int(qty_str)
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество (целое число > 0)")
            return

        price = None
        for d in self.dishes:
            if d["id"] == dish_id:
                price = d["price"]
                break
        self.result = {"dish_id": dish_id, "quantity": qty, "price": price}
        self.destroy()


class ReportsTab(ttk.Frame):
    def __init__(self, parent, db: DatabaseManager):
        super().__init__(parent)
        self.db = db
        self.create_widgets()

    def create_widgets(self):
        # ---- Date inputs ----
        date_frame = ttk.LabelFrame(self, text="Период отчета", padding=10)
        date_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(date_frame, text="С (ГГГГ-ММ-ДД):").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )
        self.start_var = tk.StringVar(value=date.today().strftime("%Y-%m-01"))
        self.start_entry = ttk.Entry(date_frame, textvariable=self.start_var, width=15)
        self.start_entry.grid(row=0, column=1, padx=(0, 15))

        ttk.Label(date_frame, text="По (ГГГГ-ММ-ДД):").grid(
            row=0, column=2, sticky=tk.W, padx=(0, 5)
        )
        self.end_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.end_entry = ttk.Entry(date_frame, textvariable=self.end_var, width=15)
        self.end_entry.grid(row=0, column=3, padx=(0, 15))

        ttk.Button(date_frame, text="Сформировать отчет", command=self.generate).grid(
            row=0, column=4
        )

        # ---- Summary ----
        summary_frame = ttk.LabelFrame(self, text="Сводка", padding=10)
        summary_frame.pack(fill=tk.X, padx=5, pady=5)

        self.summary_label = ttk.Label(summary_frame, text="")
        self.summary_label.pack()

        # ---- Sales by day ----
        day_frame = ttk.LabelFrame(self, text="Продажи по дням", padding=5)
        day_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        day_columns = ("day", "total_orders", "paid_orders", "revenue")
        self.day_tree = ttk.Treeview(
            day_frame, columns=day_columns, show="headings", height=5
        )
        self.day_tree.heading("day", text="Дата")
        self.day_tree.heading("total_orders", text="Всего заказов")
        self.day_tree.heading("paid_orders", text="Оплачено")
        self.day_tree.heading("revenue", text="Выручка (₽)")
        self.day_tree.column("day", width=140, anchor=tk.CENTER)
        self.day_tree.column("total_orders", width=120, anchor=tk.CENTER)
        self.day_tree.column("paid_orders", width=100, anchor=tk.CENTER)
        self.day_tree.column("revenue", width=120, anchor=tk.CENTER)
        self.day_tree.pack(fill=tk.BOTH, expand=True)

        # ---- Sales by dish ----
        dish_frame = ttk.LabelFrame(self, text="Продажи по блюдам", padding=5)
        dish_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        dish_columns = ("dish_name", "total_qty", "total_sum")
        self.dish_tree = ttk.Treeview(
            dish_frame, columns=dish_columns, show="headings", height=5
        )
        self.dish_tree.heading("dish_name", text="Блюдо")
        self.dish_tree.heading("total_qty", text="Кол-во")
        self.dish_tree.heading("total_sum", text="Сумма (₽)")
        self.dish_tree.column("dish_name", width=250)
        self.dish_tree.column("total_qty", width=100, anchor=tk.CENTER)
        self.dish_tree.column("total_sum", width=150, anchor=tk.CENTER)
        self.dish_tree.pack(fill=tk.BOTH, expand=True)

    def generate(self):
        start = self.start_var.get().strip()
        end = self.end_var.get().strip()
        try:
            datetime.strptime(start, "%Y-%m-%d")
            datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите даты в формате ГГГГ-ММ-ДД")
            return

        if start > end:
            messagebox.showerror("Ошибка", "Дата начала не может быть позже даты окончания")
            return

        # Clear
        for row in self.day_tree.get_children():
            self.day_tree.delete(row)
        for row in self.dish_tree.get_children():
            self.dish_tree.delete(row)

        # Day report
        day_data = self.db.get_sales_report(start, end)
        total_orders = 0
        total_paid = 0
        total_revenue = 0.0
        for row in day_data:
            self.day_tree.insert(
                "",
                tk.END,
                values=(
                    row["day"],
                    row["total_orders"],
                    row["paid_orders"],
                    f"{row['revenue']:.2f}",
                ),
            )
            total_orders += row["total_orders"]
            total_paid += row["paid_orders"]
            total_revenue += row["revenue"]

        # Dish report
        dish_data = self.db.get_detailed_sales(start, end)
        for row in dish_data:
            self.dish_tree.insert(
                "",
                tk.END,
                values=(
                    row["dish_name"],
                    row["total_qty"],
                    f"{row['total_sum']:.2f}",
                ),
            )

        self.summary_label.config(
            text=f"За период с {start} по {end}: "
            f"заказов — {total_orders}, "
            f"оплачено — {total_paid}, "
            f"выручка — {total_revenue:.2f} ₽"
        )


class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Управление заказами кафе")
        self.geometry("1100x750")
        self.minsize(900, 600)

        self.db = DatabaseManager()
        self.order_manager = OrderManager(self.db)

        self.create_menu()
        self.create_widgets()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)

        export_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Экспорт", menu=export_menu)
        export_menu.add_command(label="Меню (категории и блюда)", command=self.export_menu)
        export_menu.add_command(label="Все заказы", command=self.export_orders)
        export_menu.add_command(label="Отчет за период", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_close)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.menu_tab = MenuTab(notebook, self.db)
        self.orders_tab = OrdersTab(notebook, self.db, self.order_manager)
        self.reports_tab = ReportsTab(notebook, self.db)

        notebook.add(self.menu_tab, text="Меню")
        notebook.add(self.orders_tab, text="Заказы")
        notebook.add(self.reports_tab, text="Отчеты")

    def _write_csv(self, path, headers, rows):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(rows)

    def export_menu(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Экспорт меню",
            initialfile="menu.csv",
        )
        if not path:
            return
        categories = self.db.get_categories()
        dishes = self.db.get_dishes()
        rows = []
        for d in dishes:
            rows.append([d["id"], d["name"], f"{d['price']:.2f}", d["category_name"]])
        self._write_csv(
            path,
            ["ID", "Название", "Цена (₽)", "Категория"],
            rows,
        )
        messagebox.showinfo("Экспорт", f"Меню сохранено:\n{os.path.basename(path)}")

    def export_orders(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Экспорт заказов",
            initialfile="orders.csv",
        )
        if not path:
            return
        orders = self.db.get_orders()
        rows = []
        for o in orders:
            items = self.db.get_order_items(o["id"])
            items_str = "; ".join(
                f"{i['dish_name']} x{i['quantity']}" for i in items
            )
            rows.append([
                o["id"], o["table_number"], o["status"],
                o["created_at"], f"{o['total']:.2f}", items_str,
            ])
        self._write_csv(
            path,
            ["№", "Стол", "Статус", "Дата", "Сумма (₽)", "Позиции"],
            rows,
        )
        messagebox.showinfo("Экспорт", f"Заказы сохранены:\n{os.path.basename(path)}")

    def export_report(self):
        start = self.reports_tab.start_var.get().strip()
        end = self.reports_tab.end_var.get().strip()
        try:
            datetime.strptime(start, "%Y-%m-%d")
            datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка", "Сначала выберите корректный период на вкладке Отчеты")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Экспорт отчета",
            initialfile=f"report_{start}_{end}.csv",
        )
        if not path:
            return
        day_data = self.db.get_sales_report(start, end)
        rows = []
        for r in day_data:
            rows.append([r["day"], r["total_orders"], r["paid_orders"], f"{r['revenue']:.2f}"])
        self._write_csv(
            path,
            ["Дата", "Всего заказов", "Оплачено", "Выручка (₽)"],
            rows,
        )
        messagebox.showinfo("Экспорт", f"Отчет сохранен:\n{os.path.basename(path)}")

    def show_about(self):
        messagebox.showinfo(
            "О программе",
            "Управление заказами кафе\n"
            "Версия 1.0\n"
            "Разработано в рамках производственной практики\n"
            "ПМ.01 Разработка модулей программного обеспечения\n"
            "для компьютерных систем\n\n"
            "Технологии: Python, tkinter, SQLite",
        )

    def on_close(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
