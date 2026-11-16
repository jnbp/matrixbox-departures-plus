# 0.12.3 - No more frozen board

**Fixed**

* **The board froze after a day or more** and only came back after unplugging it. Two places could keep it waiting without end: a request that the network did not take, and looking up the data server's address, which the board did for every request. A request now gives up after a short while, and the address is looked up once every half hour.
* **Watchdog:** should the app still stop for a whole minute, the board restarts by itself instead of staying dark (Advanced, on by default). With Departures Plus set to start by itself in the MatrixBOX settings, it is back a few seconds later.

**New**

* **Any letter shows up:** letters the board's fonts do not have, such as in Kraków, São Paulo, İstanbul or Beyoncé, now show as their plain letter instead of a gap, in the ticker as well as in destinations. Emojis, for example in calendar entries, are left out.
* `/api/debug` says why the board last started (`started_by`, e.g. `WATCHDOG` after such a restart, `POWER_ON` after plugging it in) and which pause was the longest since then.

**Update**

Run the installer again. It removes the previous version first and keeps your stations and settings.

* Windows: download `departuresplus-install.bat`, double-click it and enter the board's IP address.
* macOS / Linux: download the zip, unpack it and run `python3 install.py <board ip>`.

The board must not be connected to a computer by USB while you install. Details are in the [README](https://github.com/jnbp/matrixbox-departures-plus#install).
