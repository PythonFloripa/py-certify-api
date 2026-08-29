from typing import Optional
from pydantic import BaseModel
import uuid

class FetchCertificateRequestDto(BaseModel):

    order_id: Optional[int] = None
    email: Optional[str] = None
    product_id: Optional[int] = None
    
    def __str__(self) -> str:
        params = []
        if self.order_id:
            params.append(f"order_id={self.order_id}")
        if self.email:
            params.append(f"email={self.email}")
        if self.product_id:
            params.append(f"product_id={self.product_id}")
        return f"FetchCertificateRequestDto({', '.join(params)})"


class FetchCertificateResponseDto(BaseModel):
    id: Optional[str] = None  # Mudando de UUID para string para compatibilidade
    order_id: Optional[int] = None
    product_id: Optional[int] = None
    participant_name: Optional[str] = None
    participant_email: Optional[str] = None
    certificate_url: Optional[str] = None
    certificate_key: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    email: Optional[str] = None
    success: bool = True
    
    
    def __str__(self) -> str:
        if self.success and self.id:
            return f"FetchCertificateResponseDto(id={self.id}, order_id={self.order_id})"
        else:
            return f"FetchCertificateResponseDto(success={self.success})"
