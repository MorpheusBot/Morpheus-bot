"""
Helper functions for nameday cog.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from discord import app_commands

from .messages import NameDayMess

if TYPE_CHECKING:
    pass


def build_name_indexes(namedays: dict) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Build reverse indexes mapping names to their celebration dates.

    Args:
        namedays: Dictionary with date keys (MM-DD) and nameday data

    Returns:
        Tuple of (cz_name_index, sk_name_index)
    """
    cz_name_index: dict[str, list[str]] = {}
    sk_name_index: dict[str, list[str]] = {}

    for date_key, data in namedays.items():
        # Index Czech names
        cz_data = data.get("cz", {})
        cz_name = cz_data.get("name", "")
        if cz_name and not cz_data.get("holiday"):
            # Split comma-separated names
            for name in cz_name.split(","):
                name = name.strip()
                name_lower = name.lower()
                if name_lower not in cz_name_index:
                    cz_name_index[name_lower] = []
                cz_name_index[name_lower].append(date_key)

        # Index Slovak names
        sk_data = data.get("sk", {})
        sk_name = sk_data.get("name", "")
        if sk_name and not sk_data.get("holiday"):
            # Split comma-separated names
            for name in sk_name.split(","):
                name = name.strip()
                name_lower = name.lower()
                if name_lower not in sk_name_index:
                    sk_name_index[name_lower] = []
                sk_name_index[name_lower].append(date_key)

    return cz_name_index, sk_name_index


def get_nameday_data(namedays: dict, day: date | None = None) -> dict:
    """Get nameday data for a specific date.

    Args:
        namedays: Dictionary with date keys (MM-DD) and nameday data
        day: Date to query, defaults to today

    Returns:
        Dictionary with nameday data for the given date
    """
    if day is None:
        day = date.today()
    date_key = day.strftime("%m-%d")
    return namedays.get(date_key, {})


def get_name_day(namedays: dict, locale: str, day: date | None = None) -> str:
    """Get nameday for a specific date and locale.

    Args:
        namedays: Dictionary with date keys (MM-DD) and nameday data
        locale: Locale code ("cz" for Czech, "sk" for Slovak)
        day: Date to query, defaults to today

    Returns:
        Formatted string with nameday
    """
    data = get_nameday_data(namedays, day)
    locale_data = data.get(locale, {})
    name = locale_data.get("name", "")
    holiday = locale_data.get("holiday", "")

    # Map locale to appropriate message strings
    messages = {
        "cz": {"holiday": NameDayMess.holiday_cz, "name_day": NameDayMess.name_day_cz},
        "sk": {"holiday": NameDayMess.holiday_sk, "name_day": NameDayMess.name_day_sk},
    }

    locale_messages = messages[locale]

    if holiday and name:
        return f"{locale_messages['holiday'].format(holiday=holiday)} {locale_messages['name_day'].format(name=name)}"
    else:
        return locale_messages["name_day"].format(name=name)


def search_name(name_index: dict[str, list[str]], name: str) -> list[str]:
    """Search for dates when a name has their nameday.

    Args:
        name_index: Reverse index mapping names to dates (Czech or Slovak)
        name: Name to search for

    Returns:
        List of date keys when the name has their nameday
    """
    name_lower = name.lower()
    return name_index.get(name_lower, [])


def autocomplete_name(
    name_index: dict[str, list[str]],
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete for names (Czech or Slovak).

    Args:
        name_index: Reverse index mapping names to dates
        current: Current user input

    Returns:
        List of autocomplete choices
    """
    current_lower = current.lower()
    matches = [
        app_commands.Choice(name=name.capitalize(), value=name) for name in name_index.keys() if current_lower in name
    ]
    # Sort by whether the name starts with the current input, then alphabetically
    matches.sort(key=lambda x: (not x.value.startswith(current_lower), x.value))
    return matches[:25]  # Discord limit
