from models.documents import Documents
from services.base_crud import BaseCrudService


class DocumentsService(BaseCrudService[Documents]):
    model = Documents
    entity_name = "documents"
