from models.feedback_tickets import Feedback_tickets
from services.base_crud import BaseCrudService


class Feedback_ticketsService(BaseCrudService[Feedback_tickets]):
    model = Feedback_tickets
    entity_name = "feedback_tickets"
