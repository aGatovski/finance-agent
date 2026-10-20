from fastapi import APIRouter

from src.ingest.categorize import CATEGORY_ENUM

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("")
def list_categories() -> dict:
    """The fixed category vocabulary. Single source of truth for the import LLM and
    the frontend's inline category dropdown — defined once in ingest/categorize.py."""
    return {"items": CATEGORY_ENUM}
