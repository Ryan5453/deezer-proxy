from fastapi import APIRouter, Security

from deezer.core.auth import get_api_key

router = APIRouter(tags=["V1 API"])
# router = APIRouter(dependencies=[Security(get_api_key)])

from deezer.routers.v1.endpoints import *
