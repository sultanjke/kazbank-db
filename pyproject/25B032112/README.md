# KazBank Transaction API

Flask + psycopg3 REST API over the KazBank PostgreSQL schema.
CSCI2204 Python + PostgreSQL Integration Practice - **Sultan Mecheyev**, ID - **25B032112**.

## Requirements

- Python 3.10+
- PostgreSQL 15+ with a database named `kazbank`

## Setup

```
python -m venv venv
source venv/bin/activate            # Windows Git Bash: source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env                # then put your password in .env
python check_conn.py                # Step 1
python setup_db.py                  # Step 2
flask --app app run                 # API on http://127.0.0.1:5000
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | /customers[?city=Almaty] | List customers |
| POST | /customers | Create customer {full_name, email, city} |
| PUT / DELETE | /customers/<id> | Update / delete customer |
| GET | /accounts?customer_id=n | Accounts of a customer |
| POST | /transactions | Single DEBIT/CREDIT {account_id, amount, tx_type} |
| GET | /transactions?account_id=n | History, newest first |
| POST | /transfer | Atomic transfer {from_account, to_account, amount} |
| GET | /health | Pool check + pool.get_stats() |

## Sample curl commands

### Endpoint CURLs

| Test | Command | Output |
| --- | --- | --- |
| List all | `curl -i http://127.0.0.1:5000/customers` | 200, 10 customers |
| Filter by city | `curl -i "http://127.0.0.1:5000/customers?city=Almaty"` | 200, 3 customers |
| Create | `curl -i -X POST http://127.0.0.1:5000/customers -H "Content-Type: application/json" -d '{"full_name":"Aliya Nur","email":"aliya@mail.kz","city":"Astana"}'` | 201, `{"customer_id": 11}` |
| Update | `curl -i -X PUT http://127.0.0.1:5000/customers/11 -H "Content-Type: application/json" -d '{"full_name":"Aliya Nurova","city":"Almaty"}'` | 200, `{"updated": 11}` |
| Delete | `curl -i -X DELETE http://127.0.0.1:5000/customers/11` | 200, `{"deleted": 11}` |
| Accounts | `curl -i "http://127.0.0.1:5000/accounts?customer_id=1"` | 200, KZ0001 and KZ0002 |
| Debit | `curl -i -X POST http://127.0.0.1:5000/transactions -H "Content-Type: application/json" -d '{"account_id":1,"amount":5000,"tx_type":"DEBIT"}'` | 201, balance `245000.00` |
| Overdraft | same as Debit with `"account_id":15,"amount":999999` | 400, `accounts_balance_check` |
| **SQL injection** | `curl -i "http://127.0.0.1:5000/customers?city=Almaty'%20OR%20'1'='1"` | 200, `[]` |
| **SQL injection** | `curl -i "http://127.0.0.1:5000/accounts?customer_id=1%20OR%201=1"` | 400 |


### Transactions and ACID tests

| Test | Command | Output |
| --- | --- | --- |
| Normal transfer | `curl -i -X POST http://127.0.0.1:5000/transfer -H "Content-Type: application/json" -d '{"from_account":1,"to_account":3,"amount":10000}'` | 200, `"status": "completed"` |
| Insufficient funds | same with `"from_account":15,"to_account":1,"amount":5000` | 400, `"insufficient funds"`; both balances unchanged |
| Same account | same with `"from_account":1,"to_account":1` | 400 |
| Unknown account | same with `"to_account":999` | 404 |

### Error handling tests

| Error path | How to trigger it | Output |
| --- | --- | --- |
| Duplicate email → 409 | `curl -i -X POST http://127.0.0.1:5000/customers -H "Content-Type: application/json" -d '{"full_name":"Copy","email":"arman.bekov@mail.kz"}'` | `409`, `"Duplicate value"` |
| Missing field → 400 | `curl -i -X POST http://127.0.0.1:5000/customers -H "Content-Type: application/json" -d '{"email":"new@mail.kz"}'` | `400`, `"Missing required field: full_name"` |
| DB down → 503 | Stop PostgreSQL (below), then `curl -i http://127.0.0.1:5000/customers` | `503`, `"Database unavailable"` |
| Delete with accounts → 409 | `curl -i -X DELETE http://127.0.0.1:5000/customers/1` | `409`, `"Referenced by other rows"` |

## Test evidence

- SQL injection, 409 / 400 / 503 tests, overdraft test, load-test output (paste outputs)
- [Deadlock](docs/deadlock.png) and [No Deadlock](docs/no_deadlock.png)

### Deadlock simulation order

| Order | Session A | Session B |
| --- | --- | --- |
| 1 | `BEGIN;` |  |
| 2 |  | `BEGIN;` |
| 3 | `UPDATE accounts SET balance = balance - 10 WHERE account_id = 1;` |  |
| 4 |  | `UPDATE accounts SET balance = balance - 10 WHERE account_id = 2;` |
| 5 | `UPDATE accounts SET balance = balance + 10 WHERE account_id = 2;` (hangs, waiting) |  |
| 6 |  | `UPDATE accounts SET balance = balance + 10 WHERE account_id = 1;` |

## Design notes

- Atomicity (4.1): both UPDATEs and the log rows run in one transaction. commit() makes them permanent together; any exception calls rollback(), so neither balance changes.

- SAVEPOINT (4.2): if the debit would make the balance negative, PostgreSQL raises CheckViolation. ROLLBACK TO SAVEPOINT undoes only the transfer step. The transaction stays usable, so a FAILED row is still logged and committed. Without the savepoint, the error would abort the whole transaction and nothing could be logged.

- SERIALIZABLE (4.3): a transfer reads balances, checks them, then writes. SERIALIZABLE makes concurrent transfers behave as if they ran one after another, so two simultaneous withdrawals can't both pass the balance check. The price is that PostgreSQL may abort one of two conflicting transfers with error 40001 (could not serialize access due to concurrent update). Step 5 adds the retry for that.

- Lock order (4.5): sorted() makes every transfer lock the lower account_id first. Two transfers between the same accounts then queue on the same first row instead of each holding one row and waiting for the other.