"""Database access: one ConnectionPool for the whole app (Step 6)."""
import os

from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

load_dotenv()

# Created ONCE, when this module is first imported -- never inside a route.
pool = ConnectionPool(
    conninfo=os.environ["DATABASE_URL"],
    min_size=2,       # mini-project requirement
    max_size=8,       # mini-project requirement
    timeout=5.0,      # seconds to wait for a free connection, then PoolTimeout
    open=True,
)
print("ConnectionPool created (this line should print only once)")