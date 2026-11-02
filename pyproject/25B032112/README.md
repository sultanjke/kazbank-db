## Task 3.4. Test every endpoint with curl


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

## Transaction and ACID

-  Atomicity (4.1): both UPDATEs and the log rows run in one transaction. commit() makes them permanent together; any exception calls rollback(), so neither balance changes.

- SAVEPOINT (4.2): if the debit would make the balance negative, PostgreSQL raises CheckViolation. ROLLBACK TO SAVEPOINT undoes only the transfer step. The transaction stays usable, so a FAILED row is still logged and committed. Without the savepoint, the error would abort the whole transaction and nothing could be logged.

- SERIALIZABLE (4.3): a transfer reads balances, checks them, then writes. SERIALIZABLE makes concurrent transfers behave as if they ran one after another, so two simultaneous withdrawals can't both pass the balance check. The price is that PostgreSQL may abort one of two conflicting transfers with error 40001 (could not serialize access due to concurrent update). Step 5 adds the retry for that.

- Lock order (4.5): sorted() makes every transfer lock the lower account_id first. Two transfers between the same accounts then queue on the same first row instead of each holding one row and waiting for the other.

## Task 5.4. Restart Flask and test every error path

| Error path | How to trigger it | Output |
| --- | --- | --- |
| Duplicate email → 409 | `curl -i -X POST http://127.0.0.1:5000/customers -H "Content-Type: application/json" -d '{"full_name":"Copy","email":"arman.bekov@mail.kz"}'` | `409`, `"Duplicate value"` |
| Missing field → 400 | `curl -i -X POST http://127.0.0.1:5000/customers -H "Content-Type: application/json" -d '{"email":"new@mail.kz"}'` | `400`, `"Missing required field: full_name"` |
| DB down → 503 | Stop PostgreSQL (below), then `curl -i http://127.0.0.1:5000/customers` | `503`, `"Database unavailable"` |
| Delete with accounts → 409 | `curl -i -X DELETE http://127.0.0.1:5000/customers/1` | `409`, `"Referenced by other rows"` |

## Python loadtest.py

(venv) C:\Users\Sultan\kazbank-db\pyproject\25B032112>python loadtest.py

before: {'pool_min': 2, 'pool_max': 8, 'pool_size': 8, 'pool_available': 7, 'requests_num': 69, 'requests_queued': 34, 'connections_num': 8}
20 concurrent GET /customers -> statuses [200] in 0.04s
20 concurrent transfers -> status counts {200: 9, 409: 11}
after:  {'pool_min': 2, 'pool_max': 8, 'pool_size': 8, 'pool_available': 8, 'requests_num': 141, 'requests_queued': 43, 'connections_num': 8}
connections_num stays <= pool_max while requests_num grows: connections are reused.