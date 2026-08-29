from pydantic import BaseModel, Field
from typing import Optional

class Product(BaseModel):
    product_id: int
    product_name: str
    certificate_details: str
    certificate_logo: Optional[str] = None
    certificate_background: Optional[str] = None

    