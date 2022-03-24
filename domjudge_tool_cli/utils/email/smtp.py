import smtplib
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from domjudge_tool_cli.utils.email.helper import EmailContext


class SMTP:
    host: str = "localhost"
    port: int = 25
    use_ssl: bool = False
    timeout: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    connection: Optional[Union[smtplib.SMTP_SSL, smtplib.SMTP]]

    def __init__(
        self,
        host: str = "localhost",
        port: int = 25,
        use_ssl: bool = False,
        timeout: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.username = username
        self.password = password
        self.connection = None

    @property
    def connection_class(self) -> Union[Type[smtplib.SMTP_SSL], Type[smtplib.SMTP]]:
        return smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP

    def open(self):
        connection_params = dict()
        if self.timeout is not None:
            connection_params["timeout"] = self.timeout

        self.connection = self.connection_class(
            self.host, self.port, **connection_params
        )
        self.connection.ehlo()
        self.connection.starttls()

        if self.username and self.password:
            self.connection.login(self.username, self.password)

    def close(self):
        if self.connection is None:
            return
        try:
            try:
                self.connection.quit()
            except Exception:
                self.connection.close()
                raise
        finally:
            self.connection = None

    def send_message(
        self,
        from_email: str,
        to_address: List[str],
        message: EmailContext,
        **kwargs: Dict[str, Any],
    ) -> Dict[str, Tuple[int, bytes]]:
        msg = message.mime(from_email, to_address, **kwargs)
        return self.connection.sendmail(
            from_email,
            to_address,
            msg.as_string(),
        )
