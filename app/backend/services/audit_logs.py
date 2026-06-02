from models.audit_logs import Audit_logs
from services.base_crud import BaseCrudService


class Audit_logsService(BaseCrudService[Audit_logs]):
    model = Audit_logs
    entity_name = "audit_logs"
