from pydantic import BaseModel, Field
import uuid


class DownloadCertificateRequest(BaseModel):
    id: uuid.UUID = Field(..., description="UUID do certificado")


class DownloadCertificateResponse(BaseModel):
    certificate_url: str
    email: str
    product_id: int
    success: bool
