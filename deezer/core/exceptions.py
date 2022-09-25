from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from deezer.server import app


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exception: HTTPException) -> JSONResponse:
    if type(exception.detail) is str:
        return JSONResponse(
            status_code=exception.status_code,
            content={"error": exception.detail},
        )
    return JSONResponse(
        status_code=exception.status_code,
        content=exception.detail,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exception: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "Your request is invalid. Please make sure you are providing all the required fields."
        },
    )


@app.exception_handler(Exception)
async def main_exception_handler(_: Request, exception: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": "Something went wrong. This is an issue on our end and should hopefully be fixed soon."
        },
    )
