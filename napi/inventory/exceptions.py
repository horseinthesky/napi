class InventoryException(Exception):
    def __init__(self, message: str, *, element: str):
        self.message = message
        self.element = element
        super().__init__(message)

    def __str__(self):
        return f"{self.element} -> {self.message}"


inventory_http_code_map: dict[str, int] = {
    "connect": 523,
    "inventory": 501,
    "switch": 404,
    "interface": 404,
}
