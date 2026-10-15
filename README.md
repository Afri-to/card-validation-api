# Card Validation API

![tests](https://github.com/Afri-to/card-validation-api/actions/workflows/tests.yml/badge.svg)

A REST API that validates payment card numbers with the Luhn (MOD 10) algorithm, detects the card brand, and records masked mock transactions. It uses **public test card numbers and fake data only**.

> Status: in progress. See the roadmap below.

## Tech stack

Python 3.12 · FastAPI · PostgreSQL · SQLAlchemy · pytest · GitHub Actions

## Example

```bash
curl -X POST http://127.0.0.1:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"number": "4111-1111-1111-1112"}'
```

```json
{
  "valid": false,
  "brand": "visa",
  "luhn_valid": false,
  "masked_number": "**** 1112",
  "errors": [
    {"code": "LUHN_CHECK_FAILED", "message": "The number fails the Luhn checksum (likely a typo)."}
  ]
}
```

| Error code | Meaning |
|---|---|
| `EMPTY_NUMBER` | Nothing was sent |
| `INVALID_CHARACTERS` | Something other than digits, spaces or dashes |
| `UNKNOWN_BRAND` | Prefix doesn't match Visa, Mastercard, Amex or Discover |
| `INVALID_LENGTH` | Right brand prefix, wrong number of digits |
| `LUHN_CHECK_FAILED` | Checksum fails, usually a typo |

### Transactions

| Method | Path | What it does |
|---|---|---|
| `POST` | `/transactions` | Validates the card and records a mock transaction (201). An invalid card returns 422 with the error codes above. |
| `GET` | `/transactions` | Lists transactions, newest first. Filters: `status`, `from`, `to` (ISO dates), `limit` (1–100), `offset`. |
| `GET` | `/transactions/{id}` | One transaction, or 404. |

### Business rules

| Situation | Result |
|---|---|
| Amount is zero or negative | 422, nothing recorded |
| Amount over the mock limit (10,000.00) | Recorded as `declined`, reason `OVER_LIMIT` |
| Same card, amount and currency within 60 seconds | Recorded as `flagged`, reason `POSSIBLE_DUPLICATE` |
| Otherwise | Recorded as `approved` |

Duplicate detection compares an HMAC-SHA256 **fingerprint** of the card number instead of the number itself. The same card always gives the same fingerprint, but the number can't be recovered from the database without the secret key (`CARD_FINGERPRINT_KEY`). The limit and window are configurable through `MAX_APPROVED_AMOUNT` and `DUPLICATE_WINDOW_SECONDS`.

Only the masked card (`**** 1111`) and brand are stored. The full number is never written to the database.

A number that fails validation still returns HTTP 200 with `valid: false`; a malformed request returns 422. The full card number is never returned, only the last 4 digits.

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

You need PostgreSQL running locally with databases named `cards` and `cards_test`. Set `DATABASE_URL` (and `TEST_DATABASE_URL` for tests) if your connection details differ from `postgresql+psycopg://postgres:postgres@localhost:5432/cards`.

Then open http://127.0.0.1:8000/docs for the interactive API docs.

## Run the tests

```bash
pytest -v
```

## Roadmap

- [x] FastAPI app with `/health` and CI
- [x] Luhn check with unit tests
- [x] Card-brand detection
- [x] `POST /validate` with error codes
- [x] PostgreSQL transactions table and endpoints
- [x] Business rules (negative amounts, over-limit declines, duplicate detection)
- [ ] Integration tests against a test database
- [ ] Docker and docker-compose
- [ ] Live deployment
