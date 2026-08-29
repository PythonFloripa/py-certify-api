from typing import Optional
import uuid

from pydantic import BaseModel


class ListUserCertificatesRequest(BaseModel):
    email: str
    success: Optional[bool] = None


class UserCertificateItemResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    order_id: Optional[int] = None
    product_id: Optional[int] = None
    participant_name: Optional[str] = None
    participant_email: Optional[str] = None
    certificate_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    success: Optional[bool] = None


class ListUserCertificatesResponse(BaseModel):
    email: str
    certificates: list[UserCertificateItemResponse]
