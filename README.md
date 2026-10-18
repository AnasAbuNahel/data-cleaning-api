# Data Cleaning API

A small Flask REST API that takes a messy CSV and returns a cleaned one, plus a report of what was fixed. The cleaning logic lives in a separate, tested pandas module (`cleaner/cleaning.py`) so it can also be used from scripts and notebooks.

It is a portfolio project based on the kind of data preparation I did for programme and beneficiary data: trimming text, standardising phone numbers and dates, flagging invalid IDs and removing duplicate rows. All sample data is fictional.

## What it does

| Step | Detail |
|------|--------|
| Whitespace | trims and collapses spaces in text columns, turns empty strings into missing values |
| Phone numbers | normalises Palestinian mobile numbers (`+970 59…`, `059-…`, spaces) to `05XXXXXXXX`; invalid numbers are kept but counted |
| IDs | flags values that are not exactly 9 digits (rows are kept, count is reported) |
| Dates | parses day-first and ISO dates to `YYYY-MM-DD`; unparseable dates become empty |
| Duplicates | removes fully duplicated rows after the steps above, so `"Sara  Ahmad"` and `"Sara Ahmad"` count as the same row |

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | liveness check |
| POST | `/api/profile` | data-quality profile: rows, missing values, duplicates per column |
| POST | `/api/clean` | cleaned CSV (default) or `?format=json` for the report and rows |

`/api/clean` options (query string): `phone_column`, `id_column`, `date_columns` (comma separated), `drop_duplicates=false`.

Uploads go in the `file` form field and are limited to 5 MB. Errors are returned as JSON with a 400 status.

## Run it

```bash
pip install -r requirements.txt
python -m cleaner.app
```

```bash
curl -F "file=@sample.csv" http://127.0.0.1:5000/api/profile

curl -F "file=@sample.csv" \
  "http://127.0.0.1:5000/api/clean?format=json&phone_column=phone&id_column=id&date_columns=joined"
```

## Tests

```bash
python -m unittest discover -s tests -t .
```

14 tests cover the cleaning functions (including that the input frame is not modified and that ISO dates are not swapped to day/month) and the API (success, JSON report, missing file, empty file).

## Layout

```
cleaner/cleaning.py   profile() and clean(): pure pandas, no Flask
cleaner/app.py        Flask app factory and endpoints
tests/                unit and API tests
sample.csv            fictional messy data to try it on
```
