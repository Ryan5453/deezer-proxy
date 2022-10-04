from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse

from deezer.core.auth import get_api_key
from deezer.routers.v1 import router as v1_router

app = FastAPI(
    redoc_url=None,
    dependencies=[Depends(get_api_key)],
    title="Deezer Proxy",
    version="1.0.3",
    description="A proxy for the Deezer API. It handles decryption, authentication, and documentation.",
)

app.include_router(v1_router, prefix="/v1")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


from deezer.core.exceptions import *
