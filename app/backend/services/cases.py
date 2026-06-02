from models.cases import Cases
from services.base_crud import BaseCrudService


class CasesService(BaseCrudService[Cases]):
    model = Cases
    entity_name = "cases"
