from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class BuildOrderResponse(BaseModel):
    certificate_quantity: int
    existing_orders: List[int]
    new_orders: List[int]
    processing_date: datetime = Field(
        default_factory=datetime.now, description="Data de processamento da resposta"
    )
