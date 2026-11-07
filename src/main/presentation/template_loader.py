from pathlib import Path


class TemplateLoader:
    def __init__(self):
        self.template_dir = Path(__file__).parent / "templates"

    def load_template(self, template_name: str, **kwargs) -> str:
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Template {template_name} não encontrado")

        with open(template_path, "r", encoding="utf-8") as file:
            content = file.read()

        return content.format(**kwargs)


template_loader = TemplateLoader()
