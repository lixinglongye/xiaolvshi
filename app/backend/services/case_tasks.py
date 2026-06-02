from models.case_tasks import Case_tasks
from services.base_crud import BaseCrudService


class Case_tasksService(BaseCrudService[Case_tasks]):
    model = Case_tasks
    entity_name = "case_tasks"
