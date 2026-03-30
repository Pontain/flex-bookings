from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


def format_datetime(value):
    if not value:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


templates.env.filters["datetime"] = format_datetime