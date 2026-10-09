# 0.8.0 - Hide lines, an endless ticker, more movement

**New**

* Lines per station can be hidden as well as picked: `U2,S7` shows only these, `-M4` hides one. With a direction it applies to that direction only: `U7:1` shows U7 in direction 1, `-U7:2` hides U7 in direction 2. Entries are separated by a space or a comma.
* The ticker is an endless belt: texts follow each other from right to left without a gap and without starting over. A message that ends just does not come round again, a new one joins the round. It can be switched back to one round at a time, and the divider between two texts (`+++`) can be changed.
* White signets: a white box with the line's name in the line's color.
* Up to three pages of departures per station, set for all stations or for each one, with their own page turn (sideways by default). The current station's dot shows one mark per page.
* Page changes can move up, down, left or right, or swap the picture in tiles (dissolve), stripes (blinds) or as a curtain (wipe).
* The whole display can be inverted: dark text on a lit panel.
* When a departure has left and the others take its place, the rows can roll up or come in like a page change.
* The station title can be as short as half a second.

**Changed**

* Ten stations are the limit (it was twelve).
* A change to a station's lines or direction shows at once.
* The text shown when nothing departs can be up to 60 characters long and wraps onto several lines.

**Update**

Run the installer again. It removes the previous version first and keeps your stations and settings.

* Windows: download `departuresplus-install.bat`, double-click it and enter the board's IP address.
* macOS / Linux: download the zip, unpack it and run `python3 install.py <board ip>`.

The board must not be connected to a computer by USB while you install. Details are in the [README](https://github.com/jnbp/matrixbox-departures-plus#install).
