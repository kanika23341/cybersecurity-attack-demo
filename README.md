# Food Delivery Cybersecurity Lab

## Description
This project is a local cybersecurity demonstration lab based on a food delivery website.

It contains two Flask applications:
* A food delivery website used as the target.
* An attack console used to demonstrate different web security vulnerabilities.

The project is intended for educational and demonstration purposes.

## Project Structure

```text
FoodDelivery_Cybersecurity_Lab/
├── food_delivery/
│   ├── app.py
│   ├── templates/
│   └── static/
│
├── attack_page/
│   ├── app.py
│   ├── templates/
│   └── static/
│
└── README.md
```

## Requirements
* Python 3
* Flask
* Requests

## Installation

Install the required packages:
```bash
pip install flask requests
```

## How to Run
### 1. Start the Food Delivery Website

Open a terminal:
```bash
cd food_delivery
python app.py
```

The target website will run at:
```text
http://127.0.0.1:5000
```

### 2. Start the Attack Console
Open another terminal:

```bash
cd attack_page
python app.py
```

The attack console will run at:
```text
http://127.0.0.1:5001
```
Both applications must be running at the same time.

## Demo Credentials
### Customer
* Username: `customer`
* Password: `2468`

### Restaurant
* Username: `restaurant`
* Password: `5837`

## Demonstrated Vulnerabilities

| Attack               | Security Concept           |
| -------------------- | -------------------------- |
| Brute Force          | Weak authentication        |
| SQL Injection        | Authentication bypass      |
| IDOR                 | Broken access control      |
| Menu Price Tampering | Parameter tampering        |
| Fake Order           | API abuse                  |
| Privilege Escalation | Broken authorization       |
| Rate Limit Testing   | Missing/weak rate limiting |

## Security Concepts
### Brute Force
Attempts multiple possible passwords until the correct credentials are found.

### SQL Injection
Demonstrates how malicious input can be used to bypass an authentication mechanism.

### IDOR
Demonstrates unauthorized access to another object's data by changing an object identifier.

### Menu Price Tampering
Demonstrates changing a menu item's price through a request parameter without proper authorization checks.

### Fake Order
Demonstrates sending an order request directly to an insufficiently protected endpoint.

### Privilege Escalation
Demonstrates accessing functionality intended for a higher-privileged user without proper authorization.

### Rate Limit Testing
Demonstrates repeated requests to an endpoint and shows the server returning HTTP `429` when the rate limit is reached.

## Security Notice
This project contains intentionally vulnerable endpoints for educational purposes.

It is designed to run locally on `127.0.0.1` and should not be deployed as a real production application or used against systems without permission.
