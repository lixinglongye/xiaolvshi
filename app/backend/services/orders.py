from models.orders import Orders
from services.base_crud import BaseCrudService


class OrdersService(BaseCrudService[Orders]):
    model = Orders
    entity_name = "orders"
