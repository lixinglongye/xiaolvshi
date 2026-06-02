from models.review_reports import Review_reports
from services.base_crud import BaseCrudService


class Review_reportsService(BaseCrudService[Review_reports]):
    model = Review_reports
    entity_name = "review_reports"
