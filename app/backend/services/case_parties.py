from models.case_parties import Case_parties
from services.base_crud import BaseCrudService


class Case_partiesService(BaseCrudService[Case_parties]):
    model = Case_parties
    entity_name = "case_parties"
