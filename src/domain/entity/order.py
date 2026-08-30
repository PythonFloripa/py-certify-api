from pydantic import BaseModel

class Order(BaseModel):
    order_id: int
    order_date: str
    product_id: int
    product_name: str
    certificate_details: str
    certificate_logo: str
    certificate_background: str
    time_checkin: str
    participant_email: str
    participant_first_name: str
    participant_last_name: str

