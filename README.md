# Card Validation API

![tests](https://github.com/YOUR-GITHUB-USERNAME/card-validation-api/actions/workflows/tests.yml/badge.svg)

A REST API that validates payment card numbers with the Luhn (MOD 10) algorithm, detects the card brand, and records masked mock transactions. It uses **public test card numbers and fake data only**.

> Status: in progress. See the roadmap below.

## Tech stack

Python 3.12 · FastAPI · pytest · GitHub Actions

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
- [ ] Luhn check with unit tests
- [ ] Card-brand detection
- [ ] `POST /validate` with error codes
- [ ] PostgreSQL transactions table and endpoints
- [ ] Business rules (negative amounts, duplicate detection)
- [ ] Integration tests against a test database
- [ ] Docker and docker-compose
- [ ] Live deployment
