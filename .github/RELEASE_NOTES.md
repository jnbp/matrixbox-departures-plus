# 0.6.3 - First public release

Departures Plus is a departure board app for MatrixBOX, the firmware of the T-Skylt LED boards.

**What it does**

* Rotates through any number of stations at full text size, with a title per station
* Line signets in the operator's colors, colored text or plain
* Status row with clock, date and a ticker
* Real-time mark, walking time, filters by line, direction and vehicle type
* A fallback data source per station
* JSON API for Home Assistant, used by the [T-Skylt integration](https://github.com/jnbp/t-skylt)

**Install**

* Windows: download `departuresplus-install.bat`, double-click it and enter the board's IP address.
* macOS / Linux: download the zip, unpack it and run `python3 install.py <board ip>`.

The board must not be connected to a computer by USB while you install. Details are in the [README](https://github.com/jnbp/matrixbox-departures-plus#install).
