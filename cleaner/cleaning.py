"""Reusable data-cleaning and data-quality functions built on pandas."""
import re
from dataclasses import dataclass, field

import pandas as pd

PHONE_RE = re.compile(r"^(?:\+970|0)?(5\d{8})$")
ID_RE = re.compile(r"^\d{9}$")


@dataclass
class CleaningReport:
    rows_in: int = 0
    rows_out: int = 0
    duplicates_removed: int = 0
    whitespace_fixed: int = 0
    phones_normalised: int = 0
    invalid_phones: int = 0
    invalid_ids: int = 0
    dates_parsed: int = 0
    missing_by_column: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def profile(df: pd.DataFrame) -> dict:
    """Quick data-quality profile: size, missing values and duplicates per column."""
    return {
        "rows": int(len(df)),
        "columns": list(map(str, df.columns)),
        "missing_by_column": {str(c): int(n) for c, n in df.isna().sum().items() if n},
        "fully_duplicated_rows": int(df.duplicated().sum()),
        "duplicates_by_column": {
            str(c): int(df[c].dropna().duplicated().sum()) for c in df.columns
            if df[c].dropna().duplicated().any()
        },
    }


def _normalise_phone(value):
    if pd.isna(value):
        return value, None
    digits = re.sub(r"[\s\-()]", "", str(value))
    m = PHONE_RE.match(digits)
    if not m:
        return value, False
    return "0" + m.group(1), True


def clean(
    df: pd.DataFrame,
    *,
    phone_column: str | None = None,
    id_column: str | None = None,
    date_columns: tuple[str, ...] = (),
    drop_duplicates: bool = True,
) -> tuple[pd.DataFrame, CleaningReport]:
    """Return a cleaned copy of ``df`` plus a report of what changed.

    - trims and collapses whitespace in text columns
    - normalises Palestinian mobile numbers to 05XXXXXXXX
    - flags IDs that are not exactly nine digits (they are kept, but counted)
    - parses date columns to ISO format (YYYY-MM-DD)
    - drops fully duplicated rows
    """
    report = CleaningReport(rows_in=len(df))
    out = df.copy()

    for col in out.select_dtypes(include="object").columns:
        before = out[col].copy()
        out[col] = out[col].map(
            lambda v: " ".join(v.split()) if isinstance(v, str) else v
        )
        out[col] = out[col].replace("", pd.NA)
        report.whitespace_fixed += int((before.fillna("") != out[col].fillna("")).sum())

    if phone_column and phone_column in out:
        results = out[phone_column].map(_normalise_phone)
        new_values = results.map(lambda r: r[0])
        status = results.map(lambda r: r[1])
        report.phones_normalised = int(
            ((status == True) & (new_values != out[phone_column])).sum()  # noqa: E712
        )
        report.invalid_phones = int((status == False).sum())  # noqa: E712
        out[phone_column] = new_values

    if id_column and id_column in out:
        ids = out[id_column].dropna().astype(str).str.strip()
        report.invalid_ids = int((~ids.str.match(ID_RE)).sum())

    for col in date_columns:
        if col in out:
            parsed = pd.to_datetime(out[col], errors="coerce", dayfirst=True, format="mixed")
            report.dates_parsed += int(parsed.notna().sum())
            out[col] = parsed.dt.strftime("%Y-%m-%d")

    if drop_duplicates:
        before = len(out)
        out = out.drop_duplicates().reset_index(drop=True)
        report.duplicates_removed = before - len(out)

    report.rows_out = len(out)
    report.missing_by_column = {
        str(c): int(n) for c, n in out.isna().sum().items() if n
    }
    return out, report
