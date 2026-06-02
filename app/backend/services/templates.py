from models.templates import Templates
from services.base_crud import BaseCrudService


class TemplatesService(BaseCrudService[Templates]):
    model = Templates
    entity_name = "templates"
