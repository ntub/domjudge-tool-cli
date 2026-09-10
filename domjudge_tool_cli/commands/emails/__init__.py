from typing import Annotated

import typer
from tablib import Dataset

from domjudge_tool_cli.commands.general import general_state, get_or_ask_config
from domjudge_tool_cli.models import CreateUser
from domjudge_tool_cli.utils.email import helper, smtp

app = typer.Typer()


@app.command()
def send_user_accounts(
    file: Annotated[typer.FileText, typer.Argument(help="Accounts input file.")],
    template_dir: Annotated[str, typer.Argument(help="Email templates directory.")],
    host: Annotated[str, typer.Option(help="SMTP host.")] = "localhost",
    port: Annotated[int, typer.Option(help="SMTP port.")] = 25,
    from_email: Annotated[
        str, typer.Option(help="Sender email.")
    ] = "noreply@localhost",
    use_ssl: Annotated[bool, typer.Option(help="Use SSL?")] = False,
    format: Annotated[str, typer.Option(help="File format (csv/json).")] = "csv",
    timeout: Annotated[int | None, typer.Option(help="SMTP timeout.")] = None,
    username: Annotated[str | None, typer.Option(help="SMTP username.")] = None,
    password: Annotated[str | None, typer.Option(help="SMTP password.")] = None,
) -> None:
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
