# Bank audit trail for independent validation

Each ordinary sync writes private JSON to `/app/data/audit` (override with
`TCB_AUDIT_DIR`). The deployment's host bind is
`ubuntu:/home/sil/apps-data/tcb-auto/audit`. Read via existing SSH access; do not
publish this directory or expose it through an unauthenticated HTTP endpoint.
Credentials, bearer tokens, cookies and browser state are not part of the export.

Start with `latest-attempt.json` and `latest-bank.json`. The former identifies the
most recent attempt, including cold login failures/cancellation. The latter is an
atomic pointer to the last **complete bank capture**, not necessarily a successful
Actual import or a current balance. Compare their run IDs and UTC timestamps.
Paths in the pointer are container paths: replace `/app/data` with the host bind
path when reading from the host. Never represent an old observation as live truth.

`runs/<run-id>/` retains:

- `manifest.json`: run ID, UTC timestamps, requested date window, stage and whether
  the Actual import completed. A fetching/pre_actual_saved stage without a final
  status can indicate a process crash. Inspect age and service status.
- `balances.json`: raw arrangement responses for **mapped arrangements only**, with
  their Actual account IDs and individual observation timestamps. These are bank
  observations, not Actual balances. Preserve bank field meanings: bookedBalance,
  working/sleeve balances, outstandingPayment, creditLimit, currency, etc.
- `transactions-page-<offset>.json`: raw successful API pages, saved immediately.
- `transactions-pre-actual.json`: merged raw feed, count, effective date window and
  pagination completion. Saved before conversion and any Actual connection.
- `actual-payload.json`: exact converted transactions grouped by Actual account,
  saved before connecting to Actual. Unmapped rows remain in the raw export.
- `actual-result-partial.json`: per-account acknowledgements after each import.
- `actual-result.json`: final import acknowledgement summary, if completed.

The bank snapshot remains readable if conversion or Actual later fails. A failed
bank fetch does not replace the last complete pointer; successful individual
transaction pages may exist in the failed run directory. The writer atomically
replaces and reads back JSON; audit persistence errors stop the import. TCB 401/403
refresh responses and non-200 balance/transaction responses stop the run. This
feature does not add a schedule, trigger a login, repair balances, or import any
additional source such as card statement fees. The transaction feed is not proof
of complete card accounting. Balances and transactions are sequential observations,
not a transactional bank snapshot.

Files are mode 0600 beneath a private mode 0700 audit root. History is retained
without automatic deletion so later manual checks can compare runs. Monitor disk
usage and arrange backups/retention separately. No real bank observation is
fabricated or backfilled on installation: the first ordinary authenticated run
populates the audit.

For a manual check, read both pointers, verify observation age and run status,
compare bank balance fields with the corresponding Actual account, and compare raw
bank rows with the outbound payload and import acknowledgement. Read Actual live
for ledger validation: these files are evidence, not the ledger of record.

Tests (isolated fixtures, no bank/Actual requests):
`python -m unittest discover -s tests -v`.
