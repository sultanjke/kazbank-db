• Atomicity (4.1): both UPDATEs and the log rows run in one transaction. commit() makes them permanent together; any exception calls rollback(), so neither balance changes.

• SAVEPOINT (4.2): if the debit would make the balance negative, PostgreSQL raises CheckViolation. ROLLBACK TO SAVEPOINT undoes only the transfer step. The transaction stays usable, so a FAILED row is still logged and committed. Without the savepoint, the error would abort the whole transaction and nothing could be logged.

• SERIALIZABLE (4.3): a transfer reads balances, checks them, then writes. SERIALIZABLE makes concurrent transfers behave as if they ran one after another, so two simultaneous withdrawals can't both pass the balance check. The price is that PostgreSQL may abort one of two conflicting transfers with error 40001 (could not serialize access due to concurrent update). Step 5 adds the retry for that.

• Lock order (4.5): sorted() makes every transfer lock the lower account_id first. Two transfers between the same accounts then queue on the same first row instead of each holding one row and waiting for the other.