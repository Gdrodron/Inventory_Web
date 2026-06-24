from unicodedata import category

from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
import os
import uuid
import psycopg2

app = Flask(__name__)

# SECRET KEY
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "inventory-secret-key"
)
# ADMIN CREDENTIALS
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# UPLOAD FOLDER
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# CREATE UPLOAD FOLDER IF NOT EXISTS
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DATABASE CONNECTION
try:
    conn = psycopg2.connect(
        host="127.0.0.1",
        database="testdb",
        user="postgres",
        password="Rodron30",
        port="5432"
    )

    conn.autocommit = False
    cur = conn.cursor()

    print("DATABASE CONNECTED SUCCESSFULLY")

except Exception as e:
    print("DATABASE CONNECTION ERROR:", e)
    raise

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if "user" in session:
        return redirect("/")

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        cur.execute("""
            SELECT id, username, role
            FROM "Inventory".users
            WHERE username = %s
            AND password = %s
        """, (
            username,
            password
        ))

        user = cur.fetchone()

        if user:

            session["user_id"] = user[0]
            session["user"] = user[1]
            session["role"] = user[2]


            return redirect("/")

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")

# LOGOUT
@app.route("/logout")
def logout():

        session.pop("user", None)

        return redirect("/login")

#HOME 
@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    search = request.args.get("search", "").strip()

    if search:

        cur.execute("""
            SELECT * FROM "Inventory".products
            WHERE product_name ILIKE %s
            ORDER BY id ASC
        """, ('%' + search + '%',))

    else:

        cur.execute("""
            SELECT * FROM "Inventory".products
            ORDER BY id ASC
        """)

    rows = cur.fetchall()

    total_products = len(rows)

    total_value = sum(
        float(product[2] or 0) * int(product[4] or 0)
        for product in rows
    )

    # NEW DASHBOARD STATS
    total_stock = sum(
        int(product[4] or 0)
        for product in rows
    )
    out_of_stock = sum(
        1
        for product in rows
        if int(product[4] or 0) == 0
    )

    low_stock = sum(
        1
        for product in rows
        if 0 < int(product[4] or 0) <= 5
    )
    

    # STOCK IN TODAY
    cur.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM "Inventory".transactions
        WHERE transaction_type = 'STOCK IN'
        AND DATE(transaction_date) = CURRENT_DATE
    """)

    stock_in_today = cur.fetchone()[0]

    # STOCK OUT TODAY
    cur.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM "Inventory".transactions
        WHERE transaction_type = 'STOCK OUT'
        AND DATE(transaction_date) = CURRENT_DATE
    """)

    stock_out_today = cur.fetchone()[0]

    # TOTAL TRANSACTIONS
    cur.execute("""
        SELECT COUNT(*)
        FROM "Inventory".transactions
    """)

    total_transactions = cur.fetchone()[0]

    cur.execute("""
        SELECT
            p.product_name,
            COALESCE(SUM(t.quantity), 0) AS total_sold
        FROM "Inventory".transactions t
        JOIN "Inventory".products p
            ON p.id = t.product_id
        WHERE t.transaction_type = 'STOCK OUT'
        GROUP BY p.product_name
        ORDER BY total_sold DESC
        LIMIT 1
    """)

    top_product = cur.fetchone()

    if top_product:
        top_selling = f"{top_product[0]} ({top_product[1]})"
    else:
        top_selling = "No sales yet"

    return render_template(
        "index.html",
        products=rows,
        total_products=total_products,
        total_value=f"{total_value:,.2f}",
        total_stock=total_stock,
        out_of_stock=out_of_stock,
        low_stock=low_stock,
        stock_in_today=stock_in_today,
        stock_out_today=stock_out_today,
        total_transactions=total_transactions,
        top_selling=top_selling,
    )

 # ADD PRODUCT
@app.route("/add", methods=["GET", "POST"])
def add_product():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        product_name = request.form.get(
            "product_name", ""
        ).strip()

        category = request.form.get(
            "category", ""
        ).strip()

        if not product_name:
            return "Product name is required.", 400

        if len(product_name) > 100:
            return "Product name is too long.", 400

        if not category:
            return "Category is required.", 400

        if len(category) > 100:
            return "Category is too long.", 400

        try:
            price = float(
                request.form.get("price", 0)
            )

            quantity = int(
                request.form.get("quantity", 0)
            )

        except ValueError:
            return "Invalid input.", 400

        if price < 0:
            return "Price cannot be negative.", 400

        if quantity < 0:
            return "Quantity cannot be negative.", 400

        filename = "default.png"

        # IMAGE UPLOAD
        if "image" in request.files:

            image = request.files["image"]

            if image and image.filename != "":

                filename = (
                    f"{uuid.uuid4()}_"
                    f"{secure_filename(image.filename)}"
                )

                image_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )

                image.save(image_path)

        try:

            cur.execute("""
                INSERT INTO "Inventory".products (
                    product_name,
                    price_numeric,
                    image,
                    quantity,
                    category
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                product_name,
                price,
                filename,
                quantity,
                category
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            print("ADD PRODUCT ERROR:", e)

            return "Database Error", 500

        return redirect("/")

    return render_template("add.html")

# DELETE PRODUCT
@app.route("/delete/<int:id>")
def delete_product(id):

        if "user" not in session:
            return redirect("/login")

        if session.get("role") != "admin":
            return "Access Denied", 403    

        # GET IMAGE NAME
        cur.execute("""
            SELECT image
            FROM "Inventory".products
            WHERE id = %s
        """, (id,))

        result = cur.fetchone()

        try:
            cur.execute("""
                DELETE FROM "Inventory".products
                WHERE id = %s
            """, (id,))

            conn.commit()

            # DELETE IMAGE FILE AFTER SUCCESSFUL DB DELETE
            if result:
                image_name = result[0]

                if image_name and image_name != "default.png":

                    image_path = os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        image_name
                    )

                    if os.path.exists(image_path):
                        os.remove(image_path)

        except Exception as e:
            conn.rollback()
            print("DELETE PRODUCT ERROR:", e)
            return "Database Error", 500

        return redirect("/")


# EDIT PRODUCT
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        product_name = request.form["product_name"]
        price = request.form["price"]
        quantity = request.form["quantity"]

        cur.execute("""
            SELECT image
            FROM "Inventory".products
            WHERE id = %s
        """, (id,))

        result = cur.fetchone()

        if not result:
            return redirect("/")

        image_name = result[0]

        try:
            cur.execute("""
                UPDATE "Inventory".products
                SET
                    product_name = %s,
                    price_numeric = %s,
                    quantity = %s,
                    image = %s
                WHERE id = %s
            """, (
                product_name,
                price,
                quantity,
                image_name,
                id
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            print("EDIT PRODUCT ERROR:", e)
            return "Database Error", 500

        return redirect("/")

    cur.execute("""
        SELECT *
        FROM "Inventory".products
        WHERE id = %s
    """, (id,))

    product = cur.fetchone()

    if not product:
        return redirect("/")

    return render_template(
        "edit.html",
        product=product
    )

# STOCK IN
@app.route("/stock-in/<int:id>", methods=["GET", "POST"])
def stock_in(id):

    if "user" not in session:
        return redirect("/login")

    cur.execute("""
        SELECT *
        FROM "Inventory".products
        WHERE id = %s
    """, (id,))

    product = cur.fetchone()

    if not product:
        return redirect("/")

    if request.method == "POST":

        try:
            qty = int(request.form["quantity"])

            if qty <= 0:
                return "Quantity must be greater than zero.", 400

        except ValueError:
            return "Invalid quantity.", 400

        try:

            # update stock
            cur.execute("""
                UPDATE "Inventory".products
                SET quantity = COALESCE(quantity, 0) + %s
                WHERE id = %s
            """, (
                qty,
                id
            ))

            # log transaction (FIXED)
            cur.execute("""
                INSERT INTO "Inventory".transactions (
                    product_id,
                    user_id,
                    transaction_type,
                    quantity
                )
                VALUES (%s, %s, %s, %s)
            """, (
                id,
                session["user_id"],
                "STOCK IN",
                qty
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            print("STOCK IN ERROR:", repr(e))
            return "Database Error", 500

        return redirect("/")

    return render_template(
        "stock_in.html",
        product=product
    )

# STOCK OUT
@app.route("/stock-out/<int:id>", methods=["GET", "POST"])
def stock_out(id):

    if "user" not in session:
        return redirect("/login")

    cur.execute("""
        SELECT *
        FROM "Inventory".products
        WHERE id = %s
    """, (id,))

    product = cur.fetchone()

    if not product:
        return redirect("/")

    if request.method == "POST":

        try:
            qty = int(request.form["quantity"])

            if qty <= 0:
                return "Quantity must be greater than zero.", 400

        except ValueError:
            return "Invalid quantity.", 400

        current_stock = product[4] or 0

        if qty > current_stock:
            return "Not enough stock available.", 400

        try:

            cur.execute("""
                UPDATE "Inventory".products
                SET quantity = quantity - %s
                WHERE id = %s
            """, (
                qty,
                id
            ))

            cur.execute("""
                INSERT INTO "Inventory".transactions (
                    product_id,
                    user_id,
                    transaction_type,
                    quantity
                )
                VALUES (%s, %s, %s, %s)
            """, (
                id,
                session["user_id"],
                "STOCK OUT",
                qty
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            print("STOCK OUT ERROR:", e)

            return "Database Error", 500

        return redirect("/")

    return render_template(
        "stock_out.html",
        product=product
    )

#TRANSACTIONS HISTORY
@app.route("/transactions")
def transactions():

    if "user" not in session:
        return redirect("/login")

    search = request.args.get("search", "").strip()
    filter_type = request.args.get("type")
    date_filter = request.args.get("date")

    query = """
        SELECT
            t.id,
            p.product_name,
            u.username,
            t.transaction_type,
            t.quantity,
            t.transaction_date
        FROM "Inventory".transactions t
        JOIN "Inventory".products p
            ON p.id = t.product_id
        LEFT JOIN "Inventory".users u
            ON u.id = t.user_id
        WHERE 1=1    
    """

    params = []

    if search:
        query += """
            AND (
                p.product_name ILIKE %s
                OR u.username ILIKE %s
            )
        """
        params.extend([
            f"%{search}%",
            f"%{search}%"
        ])

    if filter_type in ["STOCK IN", "STOCK OUT"]:
        query += " AND t.transaction_type = %s"
        params.append(filter_type)

    if date_filter == "today":
        query += " AND DATE(t.transaction_date) = CURRENT_DATE"

    elif date_filter == "week":
        query += """
            AND t.transaction_date >=
            CURRENT_DATE - INTERVAL '7 days'
        """

    elif date_filter == "month":
        query += """
            AND t.transaction_date >=
            CURRENT_DATE - INTERVAL '30 days'
        """

    query += " ORDER BY t.transaction_date DESC"

    cur.execute(query, params)

    rows = cur.fetchall()

    return render_template(
        "transactions.html",
        transactions=rows,
        filter_type=filter_type
    )

# RUN APP
if __name__ == "__main__":
    app.run(debug=True)