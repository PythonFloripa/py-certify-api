from pydantic import BaseModel


class CreateCertificateRequest(BaseModel):
    product_id: str
