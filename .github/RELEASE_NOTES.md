# 0.12.0 - Presets, departures right away after the night, smoother ticker

**Fixed**

* **The first round after the night was empty:** with the display off overnight, the first round in the morning showed "No departures" at every station, because the stations still held the evening's list while their first answer of the day was on its way. A list older than ten minutes now counts as gone: the station shows its title with the loading mark until fresh departures are in, and all stations are loaded during the first minute.
* **Smoother ticker:** while the board waits for the data server to answer, the ticker keeps moving instead of standing still. Each request also skips a full memory clean-up the board does not need, and the settings page asks the board less often, and not at all while it is in a background tab. `/api/debug` lists everything that took longer than 0.2 seconds since the last look, so a remaining stutter can be traced.
* **Ticker divider:** the divider only appears between two texts, so the last round of a message ends without it.
* **Clock flush with the lines:** a clock starting with 1 sat one column further right than the line column, as the 1 has an empty column on its left. It now lines up.

**New**

* **Presets:** save all settings under a name, e.g. "Day" and "Evening", and switch between them on the settings page. A preset keeps everything except the stations and the data source. Home Assistant switches with `/api/set?preset=Evening`.
* More characters on the display and in the ticker: ↑ ↓ € ° • … = @ $ ;, a visible comma, brackets, and typographic quotes, dashes and « » are shown with the nearest character the fonts have.

**Update**

Run the installer again. It removes the previous version first and keeps your stations and settings.

* Windows: download `departuresplus-install.bat`, double-click it and enter the board's IP address.
* macOS / Linux: download the zip, unpack it and run `python3 install.py <board ip>`.

The board must not be connected to a computer by USB while you install. Details are in the [README](https://github.com/jnbp/matrixbox-departures-plus#install).
