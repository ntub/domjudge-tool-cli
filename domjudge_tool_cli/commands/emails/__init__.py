from typing import Optional

import typer
from tablib import Dataset

from domjudge_tool_cli.commands.general import general_state, get_or_ask_config
from domjudge_tool_cli.models import CreateUser
from domjudge_tool_cli.utils.email import helper, smtp

app = typer.Typer()


@app.command()
def send_user_accounts(
    file: typer.FileText = typer.Argument(...),
    template_dir: str = typer.Argument(...),
    host: Optional[str] = typer.Option("localhost"),
    port: Optional[int] = typer.Option(25),
    from_email: Optional[str] = typer.Option("noreply@localhost"),
    use_ssl: Optional[bool] = typer.Option(False),
    format: Optional[str] = typer.Option("csv"),
    timeout: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
):
    input_file = file
    if format == "csv":
        input_file = file.read().replace("\ufeff", "")

    client = get_or_ask_config(general_state["config"])
    dataset = Dataset().load(input_file, format=format)
    context = helper.EmailContext(template_dir)
    _, domain = from_email.split("@")
    connection = smtp.SMTP(
        host,
        port,
        use_ssl,
        timeout,
        username,
        password,
    )
    connection.open()
    with typer.progressbar(dataset.dict) as progress:
        for item in progress:
            item["email"] = None if not item.get("email") else item["email"]
            item.pop("is_exist", None)
            user = CreateUser(**item)
            to_email = f"{user.username}@{domain}" if not user.email else user.email
            connection.send_message(
                from_email,
                [to_email],
                context,
                server_host=client.host,
                **item,
            )

    connection.close()
