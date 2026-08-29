from pydantic import BaseModel, Field
from typing import Optional
import uuid

class FetchCertificateRequest(BaseModel):
    order_id: Optional[int] = None
    product_id: Optional[int] = None
    email: Optional[str] = None


class FetchCertificateResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    order_id: Optional[int] = None
    product_id: Optional[int] = None
    participant_name: Optional[str] = None
    participant_email: Optional[str] = None
    certificate_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Status da operação
    success: Optional[bool] = Field(default=False)
    
    # Campos adicionais para compatibilidade
    email: Optional[str] = None
    product_name: Optional[str] = None
    generated_date: Optional[str] = None
    time_checkin: Optional[str] = None