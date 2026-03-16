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
        CREATE TABLE IF NOT EXISTS sales_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            customer_name TEXT NOT NULL,
            order_date TEXT NOT NULL
        )
    """)

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
        product_name = request.form.get("product_name", "").strip()
        category = request.form.get("category", "").strip()
        quantity = request.form.get("quantity", "").strip()
        price = request.form.get("price", "").strip()
        customer_name = request.form.get("customer_name", "").strip()
        order_date = request.form.get("order_date", "").strip()

        if all([product_name, category, quantity, price, customer_name, order_date]):
            conn.execute("""
                INSERT INTO sales_data
                (product_name, category, quantity, price, customer_name, order_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                product_name,
                category,
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
        SELECT *, ROUND(quantity * price, 2) AS revenue
        FROM sales_data
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (product_name LIKE ? OR customer_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    query += " ORDER BY order_date DESC, id DESC"

    rows = conn.execute(query, params).fetchall()

    categories = conn.execute("""
        SELECT DISTINCT category
        FROM sales_data
        ORDER BY category
    """).fetchall()

    conn.close()

    return render_template(
        "records.html",
        records=rows,
        categories=categories,
        search=search,
        category_filter=category_filter
    )


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
        SELECT product_name, SUM(quantity) AS total_qty
        FROM sales_data
        GROUP BY product_name
        ORDER BY total_qty DESC
        LIMIT 1
    """).fetchone()

    recent_records = conn.execute("""
        SELECT *,
               ROUND(quantity * price, 2) AS revenue
        FROM sales_data
        ORDER BY order_date DESC, id DESC
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
                "category": row["category"],
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
        SELECT category,
               ROUND(SUM(quantity * price), 2) AS revenue
        FROM sales_data
        GROUP BY category
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
        SELECT product_name,
               SUM(quantity) AS total_quantity
        FROM sales_data
        GROUP BY product_name
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