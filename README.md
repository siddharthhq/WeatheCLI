# WeatherCLI



#### Description:

WeatherCLI is a command-line weather dashboard built entirely in Python. It lets you instantly look up live weather conditions for any city in the world, save your favourite locations, and view all of them at a glance — all from your terminal, with a clean, colour-coded display powered by the `rich` library.

---

## Why I Built This

I wanted to build something that I would actually use every day. Weather apps are everywhere, but they all require opening a browser or switching to a phone. As someone who spends most of the day in a terminal, I wanted weather to be one command away. WeatherCLI was the answer: fast, no-GUI, and genuinely useful.

---

## Project Files

### `project.py`

This is the heart of the application. It contains `main()` and all core functions:

- **`get_weather(city)`** — Sends an HTTP GET request to the free `wttr.in` JSON API and parses the response into a clean Python dictionary containing temperature, humidity, wind speed, UV index, visibility, pressure, and the textual weather condition. It raises a `ValueError` for empty city names or bad API responses, making it safe and predictable to test.

- **`format_temperature(temp_c, unit)`** — Converts a Celsius temperature value to the requested unit (`"C"` or `"F"`) and returns a formatted string like `"23°C"` or `"73°F"`. Raises `ValueError` for any unit other than `C` or `F`, keeping the interface strict and unambiguous.

- **`get_weather_icon(condition)`** — Maps a plain-text weather condition description (e.g. `"Partly cloudy"`) to a matching emoji using a keyword dictionary. The match is case-insensitive. If no keyword matches, it returns a neutral thermometer emoji as a fallback.

- **`save_favorite(city)`** — Persists a city name to a JSON file (`~/.weathercli_favorites.json`) in the user's home directory. It normalises the city name to title-case and silently prevents duplicates, returning `True` if added and `False` if already present.

- **`load_favorites()`** — Reads and returns the favorites list from disk. Returns an empty list if the file does not exist or is malformed — it never crashes on a missing or corrupted file.

- **`remove_favorite(city)`** — Removes a city from the favorites list if present, writing the updated list back to disk. Returns `True` on success, `False` if the city wasn't found.

- **`display_weather(weather, unit)`** — Renders a formatted `rich` panel in the terminal with all weather fields. Not directly tested (it only produces terminal output), but used by `main()`.

- **`main()`** — Parses command-line arguments using `argparse` and orchestrates the other functions. It handles four modes: single city lookup, lookup with Fahrenheit display, saving a favourite, viewing all favourites, and removing a favourite.

### `test_project.py`

Contains all pytest tests. The test file is organised into four clear sections:

1. **`format_temperature` tests** — covers Celsius, Fahrenheit, negative temperatures, the default unit, and invalid unit handling.
2. **`get_weather_icon` tests** — covers known conditions (sunny, rain, snow, thunder), unknown conditions, empty strings, and case-insensitivity.
3. **`save_favorite / load_favorites / remove_favorite` tests** — uses a `monkeypatch` pytest fixture to redirect the favorites file to a temporary path during tests so real user data is never touched.
4. **`get_weather` tests (mocked)** — uses `unittest.mock.patch` to mock `requests.get`, so tests run offline and deterministically without hitting the real API.

### `requirements.txt`

Lists the three external libraries:

- **`requests`** — for making HTTP calls to the wttr.in API.
- **`rich`** — for rendering the colourful terminal dashboard with panels and tables.
- **`pytest`** — for running the test suite.

---

## Design Choices

**Why `wttr.in`?** It requires zero API key registration, which makes the project immediately runnable by anyone without setup friction. The JSON format it returns is well-structured and reliable.

**Why `rich` instead of plain `print()`?** The goal was a dashboard feel, not just a wall of text. `rich`'s `Panel` and `Table` components let me present weather data in a scannable, visually clear way without writing a single line of terminal escape codes.

**Why store favourites as JSON in the home directory?** It's the simplest approach that survives across terminal sessions and doesn't require a database. Storing it in `~/.weathercli_favorites.json` follows the convention of dotfiles in the home directory, keeping the project folder clean.

**Why separate `format_temperature` and `get_weather_icon` from `display_weather`?** Because `display_weather` is a side-effect function (it prints to the terminal) that's difficult to test meaningfully. By extracting the pure logic — temperature conversion and icon selection — into their own functions, those become easy to unit-test with simple assertions.

**Why mock `requests.get` in the tests?** Live API tests are brittle: they fail if the user is offline, if the API changes, or if rate limits are hit. Mocking isolates the logic being tested and makes the suite fast and deterministic.

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Look up a city
python project.py London

# Use Fahrenheit
python project.py "New York" --unit F

# Save a city to favourites
python project.py Tokyo --save

# View all saved favourites
python project.py --favorites

# Remove a city from favourites
python project.py --remove Tokyo

# Run all tests
pytest test_project.py -v
```
