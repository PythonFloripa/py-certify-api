from pydantic import BaseModel, Field
import uuid


class DownloadCertificateRequestDto(BaseModel):
    id: uuid.UUID = Field(..., description="UUID do certificado")


class DownloadCertificateResponseDto(BaseModel):
    certificate_url: str
    email: str
    product_id: int
    success: bool
