FOOD DELIVERY ATTACK DEMONSTRATION
==================================

There are two separate websites.

1. food_delivery
   Target website
   http://127.0.0.1:5000

2. attack_page
   Attack simulation page
   http://127.0.0.1:5001

START
-----
Open two terminals.

Terminal 1:
    cd food_delivery
    pip install flask requests
    python app.py

Terminal 2:
    cd attack_page
    pip install flask requests
    python app.py

Open both pages in the browser.

ATTACKS
-------
1. Brute force
   The attack page actually tries all 0000-9999 four-digit combinations
   against the local restaurant login. The successful value is not printed.
   After success, a one-time browser handoff opens the restaurant page.

2. SQL injection
   Sends a classic SQL injection-shaped input to a safe simulation endpoint.
   No arbitrary SQL is executed.

3. IDOR
   Requests order 1002 without an ownership check.

4. Menu tampering
   Changes a menu price through an intentionally unprotected endpoint.

5. Fake order
   Creates an order through an unauthenticated demo API.

6. Privilege escalation
   Opens an administration page with a missing authorization check.

7. API abuse
   Sends 12 controlled requests and demonstrates the target's 429 rate limit.

IMPORTANT
---------
The target application is intentionally vulnerable. Use this only on localhost
for the project demonstration. Do not deploy it or point the attack page at
systems you do not own or have permission to test.
