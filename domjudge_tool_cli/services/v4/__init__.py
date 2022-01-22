from .general import GeneralAPI
from .problems import ProblemsAPI
from .submissions import SubmissionsAPI
from .teams import TeamsAPI
from .users import UsersAPI
from .web import DomServerWeb

__all__ = (
    "GeneralAPI",
    "UsersAPI",
    "DomServerWeb",
    "SubmissionsAPI",
    "TeamsAPI",
    "ProblemsAPI",
)
