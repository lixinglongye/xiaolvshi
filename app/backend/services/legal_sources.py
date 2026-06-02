from models.legal_sources import Legal_sources
from services.base_crud import BaseCrudService


class Legal_sourcesService(BaseCrudService[Legal_sources]):
    model = Legal_sources
    entity_name = "legal_sources"
