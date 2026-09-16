"""Exceptions raised by the DOMjudge web gateways.

The web gateways drive DOMjudge's jury forms, which report most failures by
re-rendering the submitted page with a flash message instead of returning an
HTTP error. These exceptions carry that message so callers do not have to
guess why a write failed.
"""


class DomServerWebError(Exception):
    """A DOMjudge web form write was rejected."""


class FormSubmitError(DomServerWebError):
    """DOMjudge re-rendered the submitted form, so the write did not apply."""

    def __init__(self, message: str, *, path: str, details: list[str] | None = None):
        self.path = path
        self.details = details or []
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            return f"{super().__str__()}: {'; '.join(self.details)}"
        return super().__str__()
