from models.generated_documents import Generated_documents
from services.base_crud import BaseCrudService


class Generated_documentsService(BaseCrudService[Generated_documents]):
    model = Generated_documents
    entity_name = "generated_documents"
