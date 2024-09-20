from fastapi import APIRouter, Security

from deezer.core.auth import get_api_key

router = APIRouter(tags=["V1 API"], dependencies=[Security(get_api_key)])

from deezer.routers.v1.endpoints import *
