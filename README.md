# Card Validation API

![tests](https://github.com/YOUR-GITHUB-USERNAME/card-validation-api/actions/workflows/tests.yml/badge.svg)

A REST API that validates payment card numbers with the Luhn (MOD 10) algorithm, detects the card brand, and records masked mock transactions. It uses **public test card numbers and fake data only**.

> Status: in progress. See the roadmap below.

## Tech stack

Python 3.12 · FastAPI · pytest · GitHub Actions

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

A number that fails validation still returns HTTP 200 with `valid: false`; a malformed request returns 422. The full card number is never returned, only the last 4 digits.

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

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
- [ ] PostgreSQL transactions table and endpoints
- [ ] Business rules (negative amounts, duplicate detection)
- [ ] Integration tests against a test database
- [ ] Docker and docker-compose
- [ ] Live deployment
