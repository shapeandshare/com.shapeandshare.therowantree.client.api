from ..contracts.requests.user_income_set_request import UserIncomeSetRequest
from ..controllers.abstract_controller import AbstractController


class UserIncomeSetController(AbstractController):
    def execute(self, user_guid: str, request: UserIncomeSetRequest):
        return self.dao.user_income_set(user_guid=user_guid, transaction=request)