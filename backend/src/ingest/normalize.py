"""Deterministic row transforms: apply a ColumnMapping to a DataFrame.

pandas moves the money here; canonical output has amount < 0 for expenses,
amount > 0 for income (ARCHITECTURE §5). No LLM touches these rows.
"""

from __future__ import annotations

import re

import pandas as pd

from src.ingest.mapper import ColumnMapping

_WS = re.compile(r"\s+")
# Trailing reference/card noise often tacked onto descriptions.
_NOISE_TAIL = re.compile(r"\b([A-Z]{2,}\d{3,}|\d{4,}|REF[:#]?\w+)\s*$", re.IGNORECASE)


def clean_merchant(raw: str | None) -> str | None:
    if not raw:
        return None
    text = _WS.sub(" ", str(raw)).strip()
    text = _NOISE_TAIL.sub("", text).strip(" -*")
    return text or None


def _to_float(val) -> float:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        return 0.0
    # strip currency symbols / thousands separators; keep sign, digits, dot
    s = re.sub(r"[^\d.\-]", "", s.replace(",", ""))
    try:
        return float(s)
    except ValueError:
        return 0.0


def normalize(df: pd.DataFrame, mapping: ColumnMapping) -> list[dict]:
    """Return canonical row dicts: {type, date, amount, description, merchant}."""
    rows: list[dict] = []
    for _, r in df.iterrows():
        # amount, with sign convention applied so negative = expense
        if mapping.sign_convention == "debit_credit":
            debit = _to_float(r.get(mapping.debit_col)) if mapping.debit_col else 0.0
            credit = _to_float(r.get(mapping.credit_col)) if mapping.credit_col else 0.0
            amount = credit - abs(debit)
        else:
            raw_amount = _to_float(r.get(mapping.amount_col)) if mapping.amount_col else 0.0
            amount = -raw_amount if mapping.sign_convention == "expense_positive" else raw_amount

        date = pd.to_datetime(
            r.get(mapping.date_col), format=mapping.date_format, errors="coerce", dayfirst=False
        )
        if pd.isna(date):
            date = pd.to_datetime(r.get(mapping.date_col), errors="coerce", dayfirst=True)
        if pd.isna(date):
            continue  # unparseable date → skip the row rather than store garbage

        description = r.get(mapping.description_col) if mapping.description_col else None
        merchant_raw = r.get(mapping.merchant_col) if mapping.merchant_col else description
        tx_type = r.get(mapping.type_col) if mapping.type_col else None

        rows.append(
            {
                "type": str(tx_type).strip() if tx_type is not None and not pd.isna(tx_type) else None,
                "date": date.to_pydatetime(),
                "amount": round(amount, 2),
                "description": str(description).strip() if description is not None and not pd.isna(description) else None,
                "merchant": clean_merchant(merchant_raw),
            }
        )
    return rows


def looks_suspicious(rows: list[dict]) -> bool:
    """Sanity check: if every amount shares one sign, the convention is likely wrong."""
    signs = {(_r["amount"] > 0) for _r in rows if _r["amount"] != 0}
    return len(signs) == 1
