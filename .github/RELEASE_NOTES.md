# 0.9.0 - Colors, icons, status row your way, station row

**New**

* The status row can sit at the top or the bottom. The clock goes left, center or right.
* Three icon places in the status row show one of 25 symbols (WC, door, window, light, power, washer, dishwasher, battery, water, weather symbols and more) or two letters, in the LED tone or any color. Home Assistant sets them, for example a red WC while the bathroom is taken.
* A station row shows the station's name above or below the departures, left, centered or right, with its lines and the time if you like. In the mixed list it shows a text of your own. It works together with the status row.
* When the display comes on, nothing old is shown: the station title waits with a loading mark until fresh departures are in. This can be switched off.
* Picking a fallback is easier: the search row is marked, the country is set and another operator is preselected.
* A new Colors section gives destinations, times, line names, the station title, the station row, clock, date, ticker and page indicator a color of their own.
* The clock symbol and the date can be as bright as the clock.
* The settings page shows all icons under the i next to Icons. A leading / shows letters that are also an icon name, e.g. /wc.
* While the pages of a station turn, the station row stays where it is.
* Optionally, a small dot in the corner shows that a station's departures come from its fallback source.
* `tools/simulate.py` starts the app with made-up departures in the simulator, in every board size.

**Changed**

* Nothing is fetched while the display is off, and a station's departures are fetched just before its turn instead of all the time. The ticker stops less often.
* A request to the data server gives up after 4 seconds instead of 6.
* A station whose first answer is empty is asked again after 4 seconds, twice, before "No departures" shows.
* Up to five pages per station instead of three. A page of departures can stay for as little as 1 second.

**Update**

Run the installer again. It removes the previous version first and keeps your stations and settings.

* Windows: download `departuresplus-install.bat`, double-click it and enter the board's IP address.
* macOS / Linux: download the zip, unpack it and run `python3 install.py <board ip>`.

The board must not be connected to a computer by USB while you install. Details are in the [README](https://github.com/jnbp/matrixbox-departures-plus#install).
