from models.deletion_requests import Deletion_requests
from services.base_crud import BaseCrudService


class Deletion_requestsService(BaseCrudService[Deletion_requests]):
    model = Deletion_requests
    entity_name = "deletion_requests"
