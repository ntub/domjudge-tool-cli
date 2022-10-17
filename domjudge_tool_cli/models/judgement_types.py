from pydantic import BaseModel


class JudgementType(BaseModel):
    """
      {
      "id": "CE",
      "name": "compiler error",
      "penalty": false,
      "solved": false
    }
    """

    id: str
    name: str
    penalty: bool
    solved: bool
