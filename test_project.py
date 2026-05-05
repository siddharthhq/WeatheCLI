"""
Tests for WeatherCLI — project.py
Run with: pytest test_project.py -v
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock

from project import (
    format_temperature,
    get_weather_icon,
    save_favorite,
    load_favorites,
    remove_favorite,
    get_weather,
    FAVORITES_FILE,
)


# ──────────────────────────────────────────────
# format_temperature
# ──────────────────────────────────────────────

def test_format_temperature_celsius():
    assert format_temperature(25, "C") == "25°C"

def test_format_temperature_fahrenheit():
    assert format_temperature(0, "F") == "32°F"

def test_format_temperature_fahrenheit_boiling():
    assert format_temperature(100, "F") == "212°F"

def test_format_temperature_negative():
    assert format_temperature(-10, "C") == "-10°C"

def test_format_temperature_default_unit():
    # Default should be Celsius
    assert format_temperature(20) == "20°C"

def test_format_temperature_invalid_unit():
    with pytest.raises(ValueError):
        format_temperature(25, "K")

def test_format_temperature_invalid_unit_lowercase_k():
    with pytest.raises(ValueError):
        format_temperature(25, "X")


# ──────────────────────────────────────────────
# get_weather_icon
# ──────────────────────────────────────────────

def test_get_weather_icon_sunny():
    assert get_weather_icon("Sunny") == "☀️"

def test_get_weather_icon_rain():
    assert get_weather_icon("Heavy rain") == "🌧️"

def test_get_weather_icon_snow():
    assert get_weather_icon("Light snow") == "❄️"

def test_get_weather_icon_thunder():
    assert get_weather_icon("Thunderstorm") == "⛈️"

def test_get_weather_icon_partly_cloudy():
    assert get_weather_icon("Partly cloudy") == "⛅"

def test_get_weather_icon_unknown():
    # Unknown condition should return default icon
    assert get_weather_icon("Alien weather") == "🌡️"

def test_get_weather_icon_empty_string():
    assert get_weather_icon("") == "🌡️"

def test_get_weather_icon_case_insensitive():
    assert get_weather_icon("CLEAR") == "☀️"


# ──────────────────────────────────────────────
# save_favorite / load_favorites / remove_favorite
# ──────────────────────────────────────────────

@pytest.fixture(autouse=True)
def temp_favorites_file(tmp_path, monkeypatch):
    """Redirect the favorites file to a temp path for every test."""
    temp_file = tmp_path / "test_favorites.json"
    monkeypatch.setattr("project.FAVORITES_FILE", str(temp_file))
    yield str(temp_file)


def test_save_favorite_adds_city():
    result = save_favorite("London")
    assert result is True
    assert "London" in load_favorites()

def test_save_favorite_normalizes_case():
    save_favorite("paris")
    favs = load_favorites()
    assert "Paris" in favs

def test_save_favorite_no_duplicate():
    save_favorite("Tokyo")
    result = save_favorite("Tokyo")
    assert result is False
    assert load_favorites().count("Tokyo") == 1

def test_save_favorite_empty_string():
    result = save_favorite("")
    assert result is False

def test_load_favorites_empty():
    assert load_favorites() == []

def test_load_favorites_returns_list():
    save_favorite("Berlin")
    save_favorite("Sydney")
    favs = load_favorites()
    assert isinstance(favs, list)
    assert len(favs) == 2

def test_remove_favorite_existing():
    save_favorite("Madrid")
    result = remove_favorite("Madrid")
    assert result is True
    assert "Madrid" not in load_favorites()

def test_remove_favorite_nonexistent():
    result = remove_favorite("Atlantis")
    assert result is False

def test_remove_favorite_case_insensitive():
    save_favorite("Rome")
    result = remove_favorite("rome")
    assert result is True


# ──────────────────────────────────────────────
# get_weather (mocked network calls)
# ──────────────────────────────────────────────

MOCK_RESPONSE = {
    "current_condition": [
        {
            "temp_C": "22",
            "temp_F": "72",
            "FeelsLikeC": "21",
            "FeelsLikeF": "70",
            "humidity": "60",
            "windspeedKmph": "15",
            "winddir16Point": "NW",
            "weatherDesc": [{"value": "Partly cloudy"}],
            "visibility": "10",
            "uvIndex": "3",
            "pressure": "1012",
        }
    ],
    "nearest_area": [
        {
            "areaName": [{"value": "London"}],
            "country": [{"value": "United Kingdom"}],
        }
    ],
}


def test_get_weather_returns_dict():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_RESPONSE

    with patch("requests.get", return_value=mock_resp):
        result = get_weather("London")

    assert isinstance(result, dict)
    assert result["temp_c"] == 22
    assert result["condition"] == "Partly cloudy"
    assert result["humidity"] == 60

def test_get_weather_empty_city():
    with pytest.raises(ValueError):
        get_weather("")

def test_get_weather_whitespace_city():
    with pytest.raises(ValueError):
        get_weather("   ")

def test_get_weather_api_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 404

    with patch("requests.get", return_value=mock_resp):
        with pytest.raises(ValueError):
            get_weather("FakeCity12345")
