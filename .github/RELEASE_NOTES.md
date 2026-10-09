# 0.7.0 - Line colors for 30 networks, settings export, ticker queue

**New**

* Line colors for about 30 networks instead of two, among them Hamburg, Frankfurt, Karlsruhe, Rhein-Ruhr, Vienna, Prague, Budapest, Copenhagen, Gothenburg, Oslo, Paris, Brussels, London and New York. Colors an operator sends itself (Switzerland) are used as well.
* Export and import of all settings as a file, and a reset to the defaults that keeps your stations. All three are under *Advanced*.
* Ticker messages with a duration now queue up: each one gets the ticker to itself for its time, one after the other.

**Changed**

* A station's title shows its name exactly as it stands in the settings, including a leading "U" or "S". Edit the name there if you want it shorter.
* When the display is switched on again, it starts with the title of the first station.

**Update**

Run the installer again. It removes the previous version first and keeps your stations and settings.

* Windows: download `departuresplus-install.bat`, double-click it and enter the board's IP address.
* macOS / Linux: download the zip, unpack it and run `python3 install.py <board ip>`.

The board must not be connected to a computer by USB while you install. Details are in the [README](https://github.com/jnbp/matrixbox-departures-plus#install).
