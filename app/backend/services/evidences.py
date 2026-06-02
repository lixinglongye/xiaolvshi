from models.evidences import Evidences
from services.base_crud import BaseCrudService


class EvidencesService(BaseCrudService[Evidences]):
    model = Evidences
    entity_name = "evidences"
