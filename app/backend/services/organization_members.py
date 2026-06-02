from models.organization_members import Organization_members
from services.base_crud import BaseCrudService


class Organization_membersService(BaseCrudService[Organization_members]):
    model = Organization_members
    entity_name = "organization_members"
