from __future__ import annotations

# Types that are unambiguously internal on their own (account funding / FX).
_INTERNAL_TYPE_HINTS = ("exchange", "top-up", "top up", "topup")


def _matches(row: dict, needles: tuple[str, ...]) -> bool:
    # The `type` column is the authoritative signal when present (e.g. Revolut
    # 'Exchange'/'Topup'). Only fall back to free-text description for banks that
    # export no type — otherwise a "Reward: Exchange fee refund" row would be
    # misread as an exchange.
    typ = row.get("type")
    if typ:
        return any(n in typ.lower() for n in needles)
    desc = row.get("description")
    return bool(desc and any(n in desc.lower() for n in needles))


def flag_internal(rows: list[dict]) -> int:
    """Set `is_internal` on each row in place. Returns the count flagged.

    Account-funding / FX types only; learned per-merchant internals are applied
    later in `categorize_rows`.
    """
    flagged = 0
    for row in rows:
        row.setdefault("is_internal", False)
        if not row["is_internal"] and _matches(row, _INTERNAL_TYPE_HINTS):
            row["is_internal"] = True
            flagged += 1
    return flagged
