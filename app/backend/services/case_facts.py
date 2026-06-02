from models.case_facts import Case_facts
from services.base_crud import BaseCrudService


class Case_factsService(BaseCrudService[Case_facts]):
    model = Case_facts
    entity_name = "case_facts"
