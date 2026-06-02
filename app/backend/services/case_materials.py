from models.case_materials import Case_materials
from services.base_crud import BaseCrudService


class Case_materialsService(BaseCrudService[Case_materials]):
    model = Case_materials
    entity_name = "case_materials"
