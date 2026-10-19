from fastapi.templating import Jinja2Templates

from app.core.config import APP_DIR
class CompatibleTemplates(Jinja2Templates):
    # Keep the existing views compatible with the explicit-request template API.
    def TemplateResponse(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            name, context = args[:2]
            return super().TemplateResponse(request=context["request"], name=name, context=context, **kwargs)
        return super().TemplateResponse(*args, **kwargs)
templates = CompatibleTemplates(directory=str(APP_DIR / "templates"))


def format_datetime(value):
    if not value:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


templates.env.filters["datetime"] = format_datetime