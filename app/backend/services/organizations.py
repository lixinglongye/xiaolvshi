from models.organizations import Organizations
from services.base_crud import BaseCrudService


class OrganizationsService(BaseCrudService[Organizations]):
    model = Organizations
    entity_name = "organizations"
