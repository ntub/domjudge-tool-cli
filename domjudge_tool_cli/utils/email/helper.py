import os
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, getaddresses, make_msgid
from enum import Enum
from io import TextIOWrapper
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional, Tuple, Union


class FileType(str, Enum):
    TEXT = ".txt"
    HTML = ".html"


def load_template(
    path: Union[str, TextIOWrapper, Path],
) -> Optional[Tuple[Template, str]]:
    file_name = os.path.basename(path)
    _, extension = os.path.splitext(file_name)

    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
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

        assert path.exists() and path.is_dir(), f"No such directory {template_dir}."

        subject_templates = list(path.glob("subject.txt"))
        assert subject_templates, f"No such file subject.txt in {template_dir}."
        self.subject_template, _ = load_template(subject_templates[0])

        body_templates = list(path.glob("body.html")) + list(path.glob("body.txt"))
        assert (
            body_templates
        ), f"No such file subject.html or subject.txt in {template_dir}."
        self.body_template, self.body_file_type = load_template(body_templates[0])

    def render_subject(self, **kwargs) -> str:
        return self.subject_template.substitute(**kwargs)

    def render_body(self, **kwargs) -> str:
        return self.body_template.substitute(**kwargs)

    def mime(
        self,
        from_email: str,
        to_address: List[str],
        **kwargs: Dict[str, Any],
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
