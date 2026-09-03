# Agent Instructions

## Before summarizing any change

Run the unit test suite and confirm it passes before telling the user a
change is complete:

```bash
make test-unit
```

(equivalent to `uv run pytest tests/unit/ -v --tb=short`)

If any test fails:
- Do not report the task as done.
- Either fix the failure or, if it's unrelated to the change (pre-existing
  breakage), say so explicitly in the summary rather than staying silent
  about it.

If you added or changed seeder logic under `demostackkit/seeders/` or
`industries/*/seeders/`, also add/update a test in `tests/unit/` that would
fail without your fix — not just a test that asserts on generated script
text, but one that exercises the actual behavior where practical (see
`tests/unit/test_sales_invoices.py` for an example of executing a
generated script against faked ERPNext stand-ins).

## Other checks worth running before a PR

```bash
make lint
```
