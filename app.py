from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            UNIQUE(name, category_id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            customer_name TEXT NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    conn.commit()

    # Seed default categories
    default_categories = ["Electronics", "Furniture", "Stationery"]
    for category in default_categories:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category,))

    conn.commit()

    # Fetch category ids
    category_map = {
        row["name"]: row["id"]
        for row in conn.execute("SELECT id, name FROM categories").fetchall()
    }

    default_products = [
        ("Laptop", "Electronics"),
        ("Mouse", "Electronics"),
        ("Keyboard", "Electronics"),
        ("Monitor", "Electronics"),
        ("Desk", "Furniture"),
        ("Office Chair", "Furniture"),
        ("Bookshelf", "Furniture"),
        ("Notebook", "Stationery"),
        ("Pen Pack", "Stationery")
    ]

    for product_name, category_name in default_products:
        category_id = category_map.get(category_name)
        if category_id:
            cursor.execute("""
                INSERT OR IGNORE INTO products (name, category_id)
                VALUES (?, ?)
            """, (product_name, category_id))

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/records", methods=["GET", "POST"])
def records():
    conn = get_db_connection()

    if request.method == "POST":
        product_id = request.form.get("product_id", "").strip()
        quantity = request.form.get("quantity", "").strip()
        price = request.form.get("price", "").strip()
        customer_name = request.form.get("customer_name", "").strip()
        order_date = request.form.get("order_date", "").strip()

        if all([product_id, quantity, price, customer_name, order_date]):
            conn.execute("""
                INSERT INTO sales_data (product_id, quantity, price, customer_name, order_date)
                VALUES (?, ?, ?, ?, ?)
            """, (
                int(product_id),
                int(quantity),
                float(price),
                customer_name,
                order_date
            ))
            conn.commit()

        conn.close()
        return redirect(url_for("records"))

    search = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()

    query = """
        SELECT s.id,
               p.name AS product_name,
               c.name AS category_name,
               s.quantity,
               s.price,
               s.customer_name,
               s.order_date,
               ROUND(s.quantity * s.price, 2) AS revenue
        FROM sales_data s
        JOIN products p ON s.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (p.name LIKE ? OR s.customer_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if category_filter:
        query += " AND c.id = ?"
        params.append(category_filter)

    query += " ORDER BY s.order_date DESC, s.id DESC"

    rows = conn.execute(query, params).fetchall()

    categories = conn.execute("""
        SELECT id, name
        FROM categories
        ORDER BY name
    """).fetchall()

    products = conn.execute("""
        SELECT p.id, p.name, p.category_id, c.name AS category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        ORDER BY c.name, p.name
    """).fetchall()

    conn.close()

    return render_template(
        "records.html",
        records=rows,
        categories=categories,
        products=products,
        search=search,
        category_filter=category_filter
    )


@app.route("/masters", methods=["GET"])
def masters():
    conn = get_db_connection()

    categories = conn.execute("""
        SELECT id, name
        FROM categories
        ORDER BY name
    """).fetchall()

    products = conn.execute("""
        SELECT p.id, p.name, c.name AS category_name, c.id AS category_id
        FROM products p
        JOIN categories c ON p.category_id = c.id
        ORDER BY c.name, p.name
    """).fetchall()

    conn.close()

    return render_template("masters.html", categories=categories, products=products)


@app.route("/add-category", methods=["POST"])
def add_category():
    category_name = request.form.get("category_name", "").strip()
    if category_name:
        conn = get_db_connection()
        conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category_name,))
        conn.commit()
        conn.close()
    return redirect(url_for("masters"))


@app.route("/delete-category/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    conn = get_db_connection()

    product_count = conn.execute(
        "SELECT COUNT(*) AS count FROM products WHERE category_id = ?",
        (category_id,)
    ).fetchone()["count"]

    if product_count == 0:
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()

    conn.close()
    return redirect(url_for("masters"))


@app.route("/add-product", methods=["POST"])
def add_product():
    product_name = request.form.get("product_name", "").strip()
    category_id = request.form.get("category_id", "").strip()

    if product_name and category_id:
        conn = get_db_connection()
        conn.execute("""
            INSERT OR IGNORE INTO products (name, category_id)
            VALUES (?, ?)
        """, (product_name, int(category_id)))
        conn.commit()
        conn.close()

    return redirect(url_for("masters"))


@app.route("/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    conn = get_db_connection()

    sales_count = conn.execute(
        "SELECT COUNT(*) AS count FROM sales_data WHERE product_id = ?",
        (product_id,)
    ).fetchone()["count"]

    if sales_count == 0:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()

    conn.close()
    return redirect(url_for("masters"))


@app.route("/api/products-by-category/<int:category_id>")
def products_by_category(category_id):
    conn = get_db_connection()
    products = conn.execute("""
        SELECT id, name
        FROM products
        WHERE category_id = ?
        ORDER BY name
    """, (category_id,)).fetchall()
    conn.close()

    return jsonify([
        {"id": row["id"], "name": row["name"]}
        for row in products
    ])


@app.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM sales_data WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("records"))


@app.route("/api/summary")
def api_summary():
    conn = get_db_connection()

    total_revenue = conn.execute("""
        SELECT IFNULL(ROUND(SUM(quantity * price), 2), 0) AS total_revenue
        FROM sales_data
    """).fetchone()["total_revenue"]

    total_orders = conn.execute("""
        SELECT COUNT(*) AS total_orders
        FROM sales_data
    """).fetchone()["total_orders"]

    avg_order_value = conn.execute("""
        SELECT IFNULL(ROUND(AVG(quantity * price), 2), 0) AS avg_order_value
        FROM sales_data
    """).fetchone()["avg_order_value"]

    top_product_row = conn.execute("""
        SELECT p.name AS product_name, SUM(s.quantity) AS total_qty
        FROM sales_data s
        JOIN products p ON s.product_id = p.id
        GROUP BY p.name
        ORDER BY total_qty DESC
        LIMIT 1
    """).fetchone()

    recent_records = conn.execute("""
        SELECT p.name AS product_name,
               c.name AS category_name,
               s.customer_name,
               s.quantity,
               s.price,
               ROUND(s.quantity * s.price, 2) AS revenue,
               s.order_date
        FROM sales_data s
        JOIN products p ON s.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        ORDER BY s.order_date DESC, s.id DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return jsonify({
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "avg_order_value": avg_order_value,
        "top_product": top_product_row["product_name"] if top_product_row else "N/A",
        "recent_records": [
            {
                "product_name": row["product_name"],
                "category_name": row["category_name"],
                "customer_name": row["customer_name"],
                "quantity": row["quantity"],
                "price": row["price"],
                "revenue": row["revenue"],
                "order_date": row["order_date"]
            }
            for row in recent_records
        ]
    })


@app.route("/api/insights")
def api_insights():
    conn = get_db_connection()

    monthly_sales = conn.execute("""
        SELECT substr(order_date, 1, 7) AS month,
               ROUND(SUM(quantity * price), 2) AS revenue
        FROM sales_data
        GROUP BY substr(order_date, 1, 7)
        ORDER BY month
    """).fetchall()

    category_sales = conn.execute("""
        SELECT c.name AS category,
               ROUND(SUM(s.quantity * s.price), 2) AS revenue
        FROM sales_data s
        JOIN products p ON s.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        GROUP BY c.name
        ORDER BY revenue DESC
    """).fetchall()

    top_customers = conn.execute("""
        SELECT customer_name,
               ROUND(SUM(quantity * price), 2) AS total_spent
        FROM sales_data
        GROUP BY customer_name
        ORDER BY total_spent DESC
        LIMIT 5
    """).fetchall()

    top_products = conn.execute("""
        SELECT p.name AS product_name,
               SUM(s.quantity) AS total_quantity
        FROM sales_data s
        JOIN products p ON s.product_id = p.id
        GROUP BY p.name
        ORDER BY total_quantity DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return jsonify({
        "monthly_sales": [
            {"month": row["month"], "revenue": row["revenue"]}
            for row in monthly_sales
        ],
        "category_sales": [
            {"category": row["category"], "revenue": row["revenue"]}
            for row in category_sales
        ],
        "top_customers": [
            {"customer_name": row["customer_name"], "total_spent": row["total_spent"]}
            for row in top_customers
        ],
        "top_products": [
            {"product_name": row["product_name"], "total_quantity": row["total_quantity"]}
            for row in top_products
        ]
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True)