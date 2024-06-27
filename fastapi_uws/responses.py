from pydantic import BaseModel


class ErrorMessage(BaseModel):
    """A message describing an error."""

    message: str = "An error occurred."