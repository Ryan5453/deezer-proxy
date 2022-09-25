from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    error: str = Field(
        ...,
        example="Your request is invalid. Please make sure you are providing all the required fields.",
    )


class NoAuthorizationHeaderError(BaseModel):
    error: str = Field(
        ...,
        example="You are missing the Authorization header.",
    )


class InvalidAuthorizationHeaderError(BaseModel):
    error: str = Field(
        ...,
        example="The API key in the 'Authorization' header is invalid.",
    )
