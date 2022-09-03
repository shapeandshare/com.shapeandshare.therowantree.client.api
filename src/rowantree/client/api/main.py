import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, status
from mysql.connector.pooling import MySQLConnectionPool
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware

from .config.server import ServerConfig
from .contracts.dto.user_feature import UserFeature
from .contracts.dto.user_income import UserIncome
from .contracts.dto.user_state import UserState
from .contracts.requests.merchant_transform_request import MerchantTransformRequest
from .contracts.requests.user_active_set_request import UserActiveSetRequest
from .contracts.requests.user_income_set_request import UserIncomeSetRequest
from .contracts.requests.user_transport_request import UserTransportRequest
from .contracts.responses.user_active_get_response import UserActiveGetResponse
from .contracts.responses.user_create_response import UserCreateResponse
from .contracts.responses.user_features_get_response import UserFeaturesGetResponse
from .contracts.responses.user_income_get_response import UserIncomeGetResponse
from .contracts.responses.user_population_get_response import UserPopulationGetResponse
from .controllers.merchant_transforms_perform import MerchantTransformPerformController
from .controllers.user_active_get import UserActiveGetController
from .controllers.user_active_set import UserActiveSetController
from .controllers.user_create import UserCreateController
from .controllers.user_delete import UserDeleteController
from .controllers.user_features_active_get import UserFeaturesActiveGetController
from .controllers.user_features_get import UserFeaturesGetController
from .controllers.user_income_get import UserIncomeGetController
from .controllers.user_income_set import UserIncomeSetController
from .controllers.user_merchant_transforms_get import UserMerchantTransformsGetController
from .controllers.user_population_get import UserPopulationGetController
from .controllers.user_state_get import UserStateGetController
from .controllers.user_stores_get import UserStoresGetController
from .controllers.user_transport import UserTransportController
from .db.dao import DBDAO
from .db.utils import get_connect_pool

# Generating server configuration
config: ServerConfig = ServerConfig()

# Setup logging
Path(config.log_dir).mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.DEBUG,
    filemode="w",
    filename=f"{config.log_dir}/{os.uname()[1]}.therowantree.client.api.log",
)

logging.debug("Starting server")

logging.debug(config.json(by_alias=True, exclude_unset=True))

# Creating database connection pool, and DAO
cnxpool: MySQLConnectionPool = get_connect_pool(config=config)
dao: DBDAO = DBDAO(cnxpool=cnxpool)

# Create controllers
merchant_transforms_perform_controller = MerchantTransformPerformController(dao=dao)
user_active_get_controller = UserActiveGetController(dao=dao)
user_active_set_controller = UserActiveSetController(dao=dao)
user_create_controller = UserCreateController(dao=dao)
user_delete_controller = UserDeleteController(dao=dao)
user_features_get_controller = UserFeaturesGetController(dao=dao)
user_features_active_get_controller = UserFeaturesActiveGetController(dao=dao)
user_income_get_controller = UserIncomeGetController(dao=dao)
user_income_set_controller = UserIncomeSetController(dao=dao)
user_merchant_transforms_get_controller = UserMerchantTransformsGetController(dao=dao)
user_population_get_controller = UserPopulationGetController(dao=dao)
user_transport_controller = UserTransportController(dao=dao)
user_state_get_controller = UserStateGetController(dao=dao)
user_stores_get_controller = UserStoresGetController(dao=dao)

# Create the FastAPI application
app = FastAPI()

#  Apply COR Configuration | https://fastapi.tiangolo.com/tutorial/cors/
origins = ["http://localhost", "http://localhost:8080", "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Naive auth system until idp can be introduced
def authorize(api_access_key: str):
    if api_access_key != config.access_key:
        logging.debug("bad access key")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad Access Key")


# Define our handlers

# Application Health Endpoint
@app.get("/health/plain", status_code=status.HTTP_200_OK)
async def health_plain() -> bool:
    return True


# Request Merchant Exchange (transform) For User
@app.post("/v1/user/{user_guid}/merchant", status_code=status.HTTP_201_CREATED)
async def merchant_transforms_perform_handler(
    user_guid: str, request: MerchantTransformRequest, api_access_key: str = Header(default=None)
) -> None:
    authorize(api_access_key=api_access_key)
    merchant_transforms_perform_controller.execute(user_guid=user_guid, request=request)


# Get User's Active State
@app.get("/v1/user/{user_guid}/active", status_code=status.HTTP_200_OK)
async def user_active_get_handler(user_guid: str, api_access_key: str = Header(default=None)) -> UserActiveGetResponse:
    authorize(api_access_key=api_access_key)
    return user_active_get_controller.execute(user_guid=user_guid)


# Set User's Active State
@app.post("/v1/user/{user_guid}/active", status_code=status.HTTP_200_OK)
async def user_active_set_handler(
    user_guid: str, request: UserActiveSetRequest, api_access_key: str = Header(default=None)
) -> UserActiveSetRequest:
    authorize(api_access_key=api_access_key)
    return user_active_set_controller.execute(user_guid=user_guid, request=request)


# Create User
@app.post("/v1/user", status_code=status.HTTP_201_CREATED)
async def user_create_handler(api_access_key: str = Header(default=None)) -> UserCreateResponse:
    authorize(api_access_key=api_access_key)
    return user_create_controller.execute()


# Delete User
@app.delete("/v1/user/{user_guid}", status_code=status.HTTP_200_OK)
async def user_delete_handler(user_guid: str, api_access_key: str = Header(default=None)) -> None:
    authorize(api_access_key=api_access_key)
    user_delete_controller.execute(user_guid=user_guid)


@app.get("/v1/user/{user_guid}/features", status_code=status.HTTP_200_OK)
async def user_features_get_handler(
    user_guid: str, api_access_key: str = Header(default=None)
) -> UserFeaturesGetResponse:
    authorize(api_access_key=api_access_key)
    return user_features_get_controller.execute(user_guid=user_guid)


@app.get("/v1/user/{user_guid}/features/active", status_code=status.HTTP_200_OK)
async def user_features_active_get_handler(
    user_guid: str, api_access_key: str = Header(default=None), details: bool = False
) -> UserFeature:
    authorize(api_access_key=api_access_key)
    return user_features_active_get_controller.execute(user_guid=user_guid, details=details)


@app.get("/v1/user/{user_guid}/income", status_code=status.HTTP_200_OK)
async def user_income_get_handler(user_guid: str, api_access_key: str = Header(default=None)) -> UserIncomeGetResponse:
    authorize(api_access_key=api_access_key)
    return user_income_get_controller.execute(user_guid=user_guid)


@app.post("/v1/user/{user_guid}/income", status_code=status.HTTP_200_OK)
async def user_income_set_handler(
    user_guid: str, request: UserIncomeSetRequest, api_access_key: str = Header(default=None)
) -> None:
    authorize(api_access_key=api_access_key)
    user_income_set_controller.execute(user_guid=user_guid, request=request)


@app.get("/v1/user/{user_id}/merchant", status_code=status.HTTP_200_OK)
async def user_merchant_transforms_get_handler(user_guid: str, api_access_key: str = Header(default=None)) -> Any:
    authorize(api_access_key=api_access_key)
    return user_merchant_transforms_get_controller.execute(user_guid=user_guid)


@app.get("/v1/user/{user_guid}/population", status_code=status.HTTP_200_OK)
async def user_population_get_handler(
    user_guid: str, api_access_key: str = Header(default=None)
) -> UserPopulationGetResponse:
    authorize(api_access_key=api_access_key)
    return user_population_get_controller.execute(user_guid=user_guid)


@app.post("/v1/user/{user_guid}/transport", status_code=status.HTTP_200_OK)
async def user_transport_handler(
    user_guid: str, request: UserTransportRequest, api_access_key: str = Header(default=None)
) -> UserFeature:
    authorize(api_access_key=api_access_key)
    return user_transport_controller.execute(user_guid=user_guid, request=request)


@app.get("/v1/user/{user_guid}/state", status_code=status.HTTP_200_OK)
async def user_state_get_handler(user_guid: str, api_access_key: str = Header(default=None)) -> UserState:
    authorize(api_access_key=api_access_key)
    return user_state_get_controller.execute(user_guid=user_guid)


@app.get("/v1/user/{user_guid}/stores", status_code=status.HTTP_200_OK)
async def user_stores_get_handler(user_guid: str, api_access_key: str = Header(default=None)) -> Any:
    authorize(api_access_key=api_access_key)
    return user_stores_get_controller.execute(user_guid=user_guid)
