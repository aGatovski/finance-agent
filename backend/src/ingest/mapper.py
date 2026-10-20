"""LLM schema-mapper: infer which CSV columns mean what, once per format.

The LLM only picks columns and the sign convention (fuzzy structure inference);
pandas then moves the money deterministically in normalize.py (ARCHITECTURE §6.2).
The result is cached per header-fingerprint, so a known bank format costs zero
LLM calls on subsequent imports.
"""

from __future__ import annotations

import hashlib
from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from src.config import settings

SignConvention = Literal["signed", "expense_positive", "debit_credit"]


class ColumnMapping(BaseModel):
    """How to read one CSV format into canonical transaction rows."""

    date_col: str = Field(description="Column holding the transaction date.")
    amount_col: str | None = Field(
        default=None,
        description="Single signed/unsigned amount column. Null when the file uses "
        "separate debit and credit columns.",
    )
    description_col: str | None = Field(
        default=None, description="Free-text description / narrative column."
    )
    merchant_col: str | None = Field(
        default=None, description="Dedicated merchant/payee column, if any."
    )
    type_col: str | None = Field(
        default=None, description="Transaction type/category column (e.g. Revolut 'Type')."
    )
    debit_col: str | None = Field(
        default=None, description="Debit (money out) column, when amounts are split."
    )
    credit_col: str | None = Field(
        default=None, description="Credit (money in) column, when amounts are split."
    )
    date_format: str | None = Field(
        default=None,
        description="strptime format for date_col (e.g. '%Y-%m-%d'). Null to auto-detect.",
    )
    sign_convention: SignConvention = Field(
        description=(
            "'signed' = amount_col already negative for expenses; "
            "'expense_positive' = amount_col lists expenses as positive magnitudes "
            "(flip the sign); 'debit_credit' = use debit_col/credit_col."
        )
    )


_CACHE: dict[str, ColumnMapping] = {}

_PROMPT = """You map a bank-statement CSV to a canonical schema. Given the header \
columns and a few sample rows, decide which column is the date, the amount (or the \
debit/credit pair), the description, the merchant, and the transaction type.

Then choose sign_convention:
- "signed": there is one amount column already negative for money-out / expenses.
- "expense_positive": one amount column where spending is a POSITIVE number.
- "debit_credit": money-out and money-in live in two separate columns.

Columns: {columns}
Sample rows:
{samples}
"""


def fingerprint(columns: list[str]) -> str:
    key = "|".join(sorted(c.strip().lower() for c in columns))
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def infer_mapping(columns: list[str], sample_rows: list[dict]) -> tuple[ColumnMapping, bool]:
    """Return (mapping, from_cache). One structured LLM call per unseen format."""
    fp = fingerprint(columns)
    if fp in _CACHE:
        return _CACHE[fp], True

    model = ChatGoogleGenerativeAI(
        model=settings.gemini_model, temperature=0, google_api_key=settings.gemini_api_key
    ).with_structured_output(ColumnMapping)

    samples = "\n".join(str(r) for r in sample_rows[:5])
    mapping: ColumnMapping = model.invoke(_PROMPT.format(columns=columns, samples=samples))
    _CACHE[fp] = mapping
    return mapping, False
