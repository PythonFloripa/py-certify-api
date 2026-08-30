from typing import Optional

from pydantic import BaseModel


class ListUserCertificatesRequestDto(BaseModel):
    email: str
    success: Optional[bool] = None


class UserCertificateItemDto(BaseModel):
    id: Optional[str] = None
    order_id: Optional[int] = None
    product_id: Optional[int] = None
    participant_name: Optional[str] = None
    participant_email: Optional[str] = None
    certificate_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    success: Optional[bool] = None


class ListUserCertificatesResponseDto(BaseModel):
    email: str
    certificates: list[UserCertificateItemDto]
