from flask import Flask, render_template, request, redirect, url_for, session, abort
from functools import wraps
from collections import defaultdict
from time import time
import secrets

app = Flask(__name__)
app.secret_key = "local-food-demo-key"
USERS = {
    "customer": {"password": "2468", "role": "customer", "name": "Customer"},
    "restaurant": {"password": "5837", "role": "restaurant", "name": "Restaurant Manager"},
}

MENU = [
    {"id": 1, "name": "Chicken Burger", "price": 140, "available": True},
    {"id": 2, "name": "Veg Pizza", "price": 210, "available": True},
    {"id": 3, "name": "French Fries", "price": 90, "available": True},
    {"id": 4, "name": "Cold Coffee", "price": 80, "available": True},
]

ORDERS = {
    1001: {"customer": "Customer", "items": "Chicken Burger x 1", "total": 140, "status": "Preparing"},
    1002: {"customer": "Other Customer", "items": "Veg Pizza x 2", "total": 420, "status": "Out for delivery"},
}

handoff_tokens = {}
rate_log = defaultdict(list)


def logged_in(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    return render_template("home.html", menu=MENU)


@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = USERS.get(username)

        if user and password == user["password"]:
            session["user"] = username
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))

        message = "Login failed"
    return render_template("login.html", message=message)


@app.route("/dashboard")
@logged_in
def dashboard():
    return render_template(
        "dashboard.html",
        username=session["user"],
        role=session["role"]
    )


@app.route("/restaurant")
@logged_in
def restaurant():
    if session.get("role") != "restaurant":
        return render_template("denied.html"), 403
    return render_template("restaurant.html", menu=MENU, orders=ORDERS)


@app.route("/customer")
@logged_in
def customer():
    if session.get("role") != "customer":
        return render_template("denied.html"), 403
    return render_template("customer.html", menu=MENU, orders=ORDERS)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/orders/<int:order_id>")
@logged_in
def order(order_id):
    item = ORDERS.get(order_id)
    if not item:
        abort(404)
    return render_template("order.html", order_id=order_id, order=item)


@app.route("/restaurant/menu")
@logged_in
def restaurant_menu():
    if session.get("role") != "restaurant":
        return render_template("denied.html"), 403
    return render_template("restaurant_menu.html", menu=MENU)


@app.route("/lab/menu/update", methods=["POST"])
def lab_menu_update():
    item_id = request.form.get("item_id", type=int)
    price = request.form.get("price", type=int)
    for item in MENU:
        if item["id"] == item_id and price is not None:
            old = item["price"]
            item["price"] = price
            return render_template(
                "lab_result.html",
                title="Menu changed",
                detail=f'{item["name"]}: ₹{old} -> ₹{price}'
            )
    return "Item not found", 404


@app.route("/lab/order", methods=["POST"])
def lab_order():
    item_id = request.form.get("item_id", type=int)
    quantity = request.form.get("quantity", type=int, default=1)
    item = next((x for x in MENU if x["id"] == item_id), None)
    if not item or quantity < 1:
        return "Invalid order", 400

    new_id = max(ORDERS) + 1
    ORDERS[new_id] = {
        "customer": "Unauthenticated caller",
        "items": f'{item["name"]} x {quantity}',
        "total": item["price"] * quantity,
        "status": "Received"
    }
    return render_template(
        "lab_result.html",
        title="Order created",
        detail=f"Order #{new_id} was created without a login."
    )


@app.route("/lab/admin")
def lab_admin():
    return render_template("admin.html", menu=MENU)


@app.route("/lab/sql-login", methods=["POST"])
def lab_sql_login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    payload = username.upper().replace(" ", "")
    classic_sqli = "'OR'1'='1" in payload or "'OR1=1" in payload or "'OR'1=1" in payload

    if classic_sqli:
        token = secrets.token_urlsafe(24)
        handoff_tokens[token] = {"user": "restaurant", "expires": time() + 60}
        return render_template(
            "lab_result.html",
            title="SQL injection accepted",
            detail="The vulnerable login treated the injected condition as true and granted restaurant access. No real SQL was executed.",
            handoff_url=url_for("open_handoff", token=token)
        )

    return render_template(
        "lab_result.html",
        title="SQL injection blocked",
        detail="The supplied input did not match the lab's SQL injection demonstration pattern."
    )


@app.route("/lab/rate-test")
def rate_test():
    now = time()
    key = (request.remote_addr or "local") + ":" + request.args.get("lab", "normal")
    recent = [x for x in rate_log[key] if now - x < 4]
    if len(recent) >= 3:
        rate_log[key] = recent
        return f"429 RATE LIMITED — request {len(recent) + 1} blocked", 429

    recent.append(now)
    rate_log[key] = recent
    return f"200 OK — request {len(recent)} accepted"


@app.route("/lab/handoff", methods=["POST"])
def handoff():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if username in USERS and password == USERS[username]["password"]:
        token = secrets.token_urlsafe(24)
        handoff_tokens[token] = {"user": username, "expires": time() + 60}
        return token
    return "invalid", 403


@app.route("/lab/open/<token>")
def open_handoff(token):
    info = handoff_tokens.pop(token, None)
    if not info or time() > info["expires"]:
        return "Handoff expired", 403
    session["user"] = info["user"]
    session["role"] = USERS[info["user"]]["role"]
    return redirect(url_for("restaurant"))


@app.route("/security")
def security():
    return render_template("security.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
