"""
WeatherCLI - A command-line weather dashboard.
Fetches live weather data and displays it with rich formatting.
"""

import sys
import json
import os
import argparse
from datetime import datetime

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

FAVORITES_FILE = os.path.expanduser("~/.weathercli_favorites.json")

WEATHER_ICONS = {
    "clear": "☀️",
    "sunny": "☀️",
    "partly cloudy": "⛅",
    "cloudy": "☁️",
    "overcast": "☁️",
    "mist": "🌫️",
    "fog": "🌫️",
    "rain": "🌧️",
    "drizzle": "🌦️",
    "snow": "❄️",
    "sleet": "🌨️",
    "thunder": "⛈️",
    "blizzard": "🌨️",
    "wind": "💨",
    "hail": "🌨️",
}


def get_weather(city: str) -> dict:
    """
    Fetch current weather data for a given city using the wttr.in API.

    Args:
        city: Name of the city to look up.

    Returns:
        A dictionary with weather data including temperature, condition,
        humidity, wind speed, and feels-like temperature.

    Raises:
        ValueError: If the city is empty or the API returns an error.
        requests.RequestException: If the network request fails.
    """
    if not city or not city.strip():
        raise ValueError("City name cannot be empty.")

    url = f"https://wttr.in/{requests.utils.quote(city.strip())}?format=j1"
    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        raise ValueError(f"Could not fetch weather for '{city}'. Check the city name.")

    data = response.json()

    # Validate that we got actual weather data
    if "current_condition" not in data or not data["current_condition"]:
        raise ValueError(f"No weather data found for '{city}'.")

    current = data["current_condition"][0]
    nearest = data.get("nearest_area", [{}])[0]
    area_name = nearest.get("areaName", [{}])[0].get("value", city)
    country = nearest.get("country", [{}])[0].get("value", "")

    return {
        "city": city.strip().title(),
        "display_name": f"{area_name}, {country}" if country else area_name,
        "temp_c": int(current["temp_C"]),
        "temp_f": int(current["temp_F"]),
        "feels_like_c": int(current["FeelsLikeC"]),
        "feels_like_f": int(current["FeelsLikeF"]),
        "humidity": int(current["humidity"]),
        "wind_kmph": int(current["windspeedKmph"]),
        "wind_dir": current["winddir16Point"],
        "condition": current["weatherDesc"][0]["value"],
        "visibility_km": int(current["visibility"]),
        "uv_index": int(current["uvIndex"]),
        "pressure_mb": int(current["pressure"]),
    }


def format_temperature(temp_c: float, unit: str = "C") -> str:
    """
    Format a temperature value with its unit symbol.

    Args:
        temp_c: Temperature in Celsius.
        unit: Display unit — 'C' for Celsius or 'F' for Fahrenheit.

    Returns:
        A formatted string like '23°C' or '73°F'.

    Raises:
        ValueError: If unit is not 'C' or 'F'.
    """
    unit = unit.upper()
    if unit not in ("C", "F"):
        raise ValueError(f"Invalid temperature unit '{unit}'. Use 'C' or 'F'.")

    if unit == "F":
        temp = round((temp_c * 9 / 5) + 32)
        return f"{temp}°F"
    return f"{temp_c}°C"


def get_weather_icon(condition: str) -> str:
    """
    Return an emoji icon matching the weather condition description.

    Args:
        condition: Weather condition string (e.g., 'Partly cloudy').

    Returns:
        A weather emoji string. Defaults to '🌡️' if no match is found.
    """
    if not condition:
        return "🌡️"

    condition_lower = condition.lower()
    for keyword, icon in WEATHER_ICONS.items():
        if keyword in condition_lower:
            return icon
    return "🌡️"


def load_favorites() -> list:
    """
    Load the list of favorite cities from the local favorites file.

    Returns:
        A list of city name strings. Returns an empty list if the file
        does not exist or cannot be parsed.
    """
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_favorite(city: str) -> bool:
    """
    Add a city to the favorites list if it isn't already saved.

    Args:
        city: Name of the city to save.

    Returns:
        True if the city was added, False if it was already in favorites.
    """
    if not city or not city.strip():
        return False

    favorites = load_favorites()
    city_clean = city.strip().title()

    if city_clean in favorites:
        return False

    favorites.append(city_clean)
    with open(FAVORITES_FILE, "w") as f:
        json.dump(favorites, f, indent=2)
    return True


def remove_favorite(city: str) -> bool:
    """
    Remove a city from the favorites list.

    Args:
        city: Name of the city to remove.

    Returns:
        True if removed, False if not found.
    """
    favorites = load_favorites()
    city_clean = city.strip().title()
    if city_clean not in favorites:
        return False
    favorites.remove(city_clean)
    with open(FAVORITES_FILE, "w") as f:
        json.dump(favorites, f, indent=2)
    return True


def display_weather(weather: dict, unit: str = "C") -> None:
    """Render a rich weather panel in the terminal."""
    icon = get_weather_icon(weather["condition"])
    unit = unit.upper()

    temp = format_temperature(weather["temp_c"], unit)
    feels = format_temperature(weather["feels_like_c"], unit)

    title = Text()
    title.append(f"{icon}  {weather['display_name']}", style="bold cyan")

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Label", style="dim", width=20)
    table.add_column("Value", style="bold white")

    table.add_row("🌡️  Temperature", temp)
    table.add_row("🤔 Feels Like", feels)
    table.add_row("📋 Condition", f"{icon} {weather['condition']}")
    table.add_row("💧 Humidity", f"{weather['humidity']}%")
    table.add_row("💨 Wind", f"{weather['wind_kmph']} km/h {weather['wind_dir']}")
    table.add_row("👁️  Visibility", f"{weather['visibility_km']} km")
    table.add_row("🔆 UV Index", str(weather["uv_index"]))
    table.add_row("📊 Pressure", f"{weather['pressure_mb']} mb")

    timestamp = datetime.now().strftime("%H:%M, %d %b %Y")
    panel = Panel(
        table,
        title=title,
        subtitle=f"[dim]Updated: {timestamp}[/]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


def main():
    parser = argparse.ArgumentParser(
        description="WeatherCLI — A beautiful command-line weather dashboard.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python project.py London
  python project.py "New York" --unit F
  python project.py --favorites
  python project.py Tokyo --save
  python project.py --remove Tokyo
        """,
    )
    parser.add_argument("city", nargs="?", help="City name to look up.")
    parser.add_argument(
        "--unit", choices=["C", "F"], default="C", help="Temperature unit (default: C)."
    )
    parser.add_argument(
        "--save", action="store_true", help="Save the city to your favorites."
    )
    parser.add_argument(
        "--favorites", action="store_true", help="Show weather for all saved favorites."
    )
    parser.add_argument(
        "--remove", metavar="CITY", help="Remove a city from favorites."
    )

    args = parser.parse_args()

    # Handle --remove
    if args.remove:
        if remove_favorite(args.remove):
            console.print(f"[green]✓ Removed '{args.remove.title()}' from favorites.[/]")
        else:
            console.print(f"[yellow]'{args.remove.title()}' was not in your favorites.[/]")
        return

    # Handle --favorites
    if args.favorites:
        favs = load_favorites()
        if not favs:
            console.print("[yellow]No favorites saved yet. Use --save to add cities.[/]")
            return
        console.print(f"\n[bold cyan]⭐ Your Favorites ({len(favs)} cities)[/]\n")
        for fav in favs:
            try:
                weather = get_weather(fav)
                display_weather(weather, args.unit)
            except (ValueError, requests.RequestException) as e:
                console.print(f"[red]✗ {fav}: {e}[/]")
        return

    # Must have a city at this point
    if not args.city:
        parser.print_help()
        sys.exit(1)

    try:
        console.print(f"\n[dim]Fetching weather for [bold]{args.city}[/]...[/]\n")
        weather = get_weather(args.city)
        display_weather(weather, args.unit)

        if args.save:
            if save_favorite(args.city):
                console.print(f"\n[green]⭐ '{args.city.title()}' saved to favorites![/]")
            else:
                console.print(f"\n[yellow]'{args.city.title()}' is already in favorites.[/]")

    except ValueError as e:
        console.print(f"[red]✗ Error: {e}[/]")
        sys.exit(1)
    except requests.RequestException:
        console.print("[red]✗ Network error: Could not connect. Check your internet connection.[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
