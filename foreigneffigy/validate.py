import click
from datetime import datetime as dt


def validate_date(ctx, param, value):
    try:
        return dt.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise click.BadParameter("Date format needs to be YYYY-MM-DD.")
