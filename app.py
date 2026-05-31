from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
import os
import psycopg2

app = Flask(__name__)

# SECRET KEY
app.secret_key = "secret123"

# UPLOAD FOLDER
UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# CREATE UPLOAD FOLDER IF NOT EXISTS
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DATABASE CONNECTION
conn = psycopg2.connect(
    host="127.0.0.1",
    database="testdb",
    user="postgres",
    password="Rodron30",
    port="5432"
)

conn.autocommit = True

cur = conn.cursor()

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":

            session["user"] = username

            return redirect("/")

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/login")


# HOME
@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    search = request.args.get("search")

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

    total_value = 0

    for product in rows:

        if product[2]:
            total_value += float(product[2])

    return render_template(
        "index.html",
        products=rows,
        total_products=total_products,
        total_value=total_value
    )


# ADD PRODUCT
@app.route("/add", methods=["GET", "POST"])
def add_product():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        product_name = request.form["product_name"]
        price = request.form["price"]

        # DEFAULT IMAGE
        filename = "default.png"

        # CHECK IMAGE
        if "image" in request.files:

            image = request.files["image"]

            if image and image.filename != "":

                filename = secure_filename(image.filename)

                image_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )

                image.save(image_path)

        # INSERT DATABASE
        cur.execute("""
            INSERT INTO "Inventory".products(
                product_name,
                price_numeric,
                image
            )
            VALUES (%s, %s, %s)
        """, (product_name, price, filename))

        conn.commit()

        return redirect("/")

    return render_template("add.html")


# DELETE PRODUCT
@app.route("/delete/<int:id>")
def delete_product(id):

    if "user" not in session:
        return redirect("/login")

    cur.execute("""
        DELETE FROM "Inventory".products
        WHERE id = %s
    """, (id,))

    conn.commit()

    return redirect("/")


# EDIT PRODUCT
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        product_name = request.form["product_name"]
        price = request.form["price"]

        cur.execute("""
            UPDATE "Inventory".products
            SET product_name = %s,
                price_numeric = %s
            WHERE id = %s
        """, (product_name, price, id))

        conn.commit()

        return redirect("/")

    cur.execute("""
        SELECT * FROM "Inventory".products
        WHERE id = %s
    """, (id,))

    product = cur.fetchone()

    return render_template(
        "edit.html",
        product=product
    )


if __name__ == "__main__":
    app.run(debug=True)