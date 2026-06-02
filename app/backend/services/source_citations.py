from models.source_citations import Source_citations
from services.base_crud import BaseCrudService


class Source_citationsService(BaseCrudService[Source_citations]):
    model = Source_citations
    entity_name = "source_citations"
