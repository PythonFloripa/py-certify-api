from pydantic import BaseModel


class FailedResponse(BaseModel):
    status: int
    message: str
    details: str

    def __str__(self) -> str:
        return f"FailedResponse(status={self.status}, message={self.message}, details={self.details})"
