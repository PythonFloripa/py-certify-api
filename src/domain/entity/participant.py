from pydantic import BaseModel, Field
import uuid

class Participant(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    first_name: str
    last_name: str
    email: str