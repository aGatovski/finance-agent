from pydantic import BaseModel


class MerchantOut(BaseModel):
    id: int
    merchant_name: str
    category: str
    is_internal: bool
    tx_count: int


class MerchantUpdate(BaseModel):
    category: str | None = None
    is_internal: bool | None = None
    apply_to_existing: bool = False


class MerchantUpdateResult(BaseModel):
    merchant: MerchantOut
    updated_transactions: int
