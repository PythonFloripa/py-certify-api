from typing import Optional


class CertificateNotFound(Exception):
    def __init__(
        self,
        order_id: Optional[int] = None,
        product_id: Optional[int] = None,
        email: Optional[str] = None,
    ):
        self.message = "Certificate not found"
        self.order_id = order_id
        self.product_id = product_id
        self.email = email
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.order_id:
            return f"Certificate not found for order_id: {self.order_id}"
        elif self.product_id:
            return f"Certificate not found for product_id: {self.product_id}"
        elif self.email:
            return f"Certificate not found for email: {self.email}"
        else:
            return self.message
