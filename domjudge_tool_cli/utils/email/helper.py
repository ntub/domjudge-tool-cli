from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from enum import StrEnum
from pathlib import Path
from string import Template
from typing import Any


class FileType(StrEnum):
    TEXT = ".txt"
    HTML = ".html"


def load_template(
    path: str | Path,
) -> tuple[Template, str]:
    path_obj = Path(path)
    extension = path_obj.suffix

    txt = path_obj.read_text(encoding="utf-8")
    template = Template(txt)
    return template, extension


class EmailContext:
    subject_template: Template
    body_template: Template
    body_file_type: FileType

    def __init__(
        self,
        template_dir: str,
    ):
        path = Path(template_dir)

        if not (path.exists() and path.is_dir()):
            raise FileNotFoundError(f"No such directory {template_dir}.")

        subject_templates = list(path.glob("subject.txt"))
        if not subject_templates:
            raise FileNotFoundError(f"No such file subject.txt in {template_dir}.")
        self.subject_template, _ = load_template(subject_templates[0])

        body_templates = list(path.glob("body.html")) + list(path.glob("body.txt"))
        if not body_templates:
            raise FileNotFoundError(
                f"No such file body.html or body.txt in {template_dir}."
            )
        template, ext = load_template(body_templates[0])
        self.body_template = template
        self.body_file_type = FileType.HTML if ext == ".html" else FileType.TEXT

    def render_subject(self, **kwargs: Any) -> str:
        return self.subject_template.substitute(**kwargs)

    def render_body(self, **kwargs: Any) -> str:
        return self.body_template.substitute(**kwargs)

    def mime(
        self,
        from_email: str,
        to_address: list[str],
        **kwargs: Any,
    ) -> MIMEText:
        _, domain = from_email.split("@")
        mail_content_type = "html" if self.body_file_type == FileType.HTML else "plain"
        subject = self.render_subject(**kwargs)
        content = self.render_body(**kwargs)
        mime = MIMEText(content, mail_content_type, "utf-8")
        mime["Subject"] = subject
        mime["From"] = from_email
        mime["Date"] = formatdate(localtime=True)
        mime["Message-ID"] = make_msgid(domain=domain)
        mime["To"] = ",".join(to_address)

        return mime
