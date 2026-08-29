from pydantic import BaseModel, Field
from typing import Optional
import uuid

class Certificate(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    success: Optional[bool] = Field(default=False)
    certificate_key: Optional[str] = None
    certificate_url: Optional[str] = None
    generated_date: Optional[str] = None
    order_id: int
    order_date: str
    product_id: int
    product_name: str
    certificate_details: str
    certificate_logo: str
    certificate_background: str
    participant_email: Optional[str]
    participant_first_name: Optional[str]
    participant_last_name: Optional[str]
