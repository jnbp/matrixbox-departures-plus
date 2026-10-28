# 0.12.2 - Preset logos you can see, a complete settings export

**Fixed**

* **Saving a preset after picking a new logo:** the new picture was only a preview until you pressed Upload, so the preset kept the logo that was still on the board. Saving a preset now stores a logo that is still in preview first.

**New**

* **Each preset shows its logo:** the preset list on the settings page shows a small picture of the logo kept with each preset, or says that it has none.
* **Complete settings export:** Export settings now writes one file with the settings, all presets with their logos, and the current logo. Import settings puts them all back; presets with the same name are replaced, others stay.

**Update**

Run the installer again. It removes the previous version first and keeps your stations and settings.

* Windows: download `departuresplus-install.bat`, double-click it and enter the board's IP address.
* macOS / Linux: download the zip, unpack it and run `python3 install.py <board ip>`.

The board must not be connected to a computer by USB while you install. Details are in the [README](https://github.com/jnbp/matrixbox-departures-plus#install).
