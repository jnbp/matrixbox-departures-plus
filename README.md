# Departures Plus for MatrixBOX

<p align="center">
  <img src="docs/rotation.gif" alt="Departures Plus rotating through three stations" width="760">
</p>

A departure board app for [MatrixBOX](https://github.com/MatrixBOX-dev/matrixbox), the open firmware of the T-Skylt LED boards. It is a rebuild of the stock *Departures* app with a different focus: several stations in rotation at full text size, line signets in the operator's colors, and a status row with clock and ticker that Home Assistant can write to.

This is a community project and not affiliated with T-Skylt Sweden AB. It gets its departures from the same data server as the stock app.

## What it does

* **Station rotation.** Up to ten stations with up to five pages each, each with a title showing its lines and your walking time. Or one mixed list of all stations.
* **Line colors.** Filled signets, white signets with the name in the line's color, colored text or plain. The line colors of about 30 networks are built in, among them Berlin, Hamburg, Frankfurt, Vienna, Stockholm, Copenhagen, Paris, London and New York.
* **Status row.** Clock, date and a ticker for your own text, messages from Home Assistant and the operator's service notices. The ticker runs as an endless belt or one round at a time, with a divider of your choice. The row sits at the top or the bottom, the clock left, centered or right, and three icon places show symbols or letters that Home Assistant sets, such as a red WC while the bathroom is taken.
* **Real-time mark.** Tells live departures from timetable ones, where the operator's data says so.
* **Station row:** the station's name above or below the departures, with its lines and the time if you like. It stays still while a station's pages turn.
* **Per station:** walking time, lines to show or to hide (also per direction), a filter by direction and vehicle type, and a fallback data source that steps in when the main one has no departures.
* **Colors:** destinations, times, line names, station title, station row, clock, date, ticker and page indicator can each have their own color.
* **Display:** three text sizes, ten LED tones or your own, brightness, margins, 180° rotation, an inverted look, a schedule per weekday, sleep while nothing departs.
* **Movement:** stations and pages can slide in from any side, dissolve in small tiles, open like blinds or wipe in. Departures that move up can roll into place.
* **Home Assistant:** power, brightness, shown station, next departures and ticker messages through the [T-Skylt integration](https://github.com/jnbp/t-skylt). A ticker message can light up just the ticker while the display is off.

![The display in eight settings](docs/display.png)

## Install

You need a board running MatrixBOX and about 110 KB of free storage. The board must not be connected to a computer by USB while you install, because its storage is read-only to its own code then.

**Windows:** download `departuresplus-install.bat` from the [latest release](https://github.com/jnbp/matrixbox-departures-plus/releases/latest), double-click it and enter the board's IP address.

**macOS and Linux:** download the zip from the latest release, unpack it and run

```sh
python3 install.py 192.168.1.50
```

Both copy the app over Wi-Fi into `/departuresplus` on the board and start it. Updating works the same way: the installer removes the previous version first and keeps your stations and settings.

**By hand:** copy the folder `departuresplus` to the root of the board with the board's own file manager and start the app from the home screen.

## Settings

Open `http://<board ip>/` while the app is running. Changes apply immediately and are saved on the board. Under *Advanced* you can export the settings to a file, import them again and reset everything to the defaults.

<p align="center">
  <img src="docs/settings.png" alt="The settings page" width="560">
</p>

## Home Assistant

Install the [T-Skylt integration](https://github.com/jnbp/t-skylt) (0.3.1 or newer) and add the board while Departures Plus is running. Sending a ticker message is then a standard notify action:

```yaml
action: notify.send_message
target:
  entity_id: notify.t_skylt_ticker
data:
  message: "Door opened"
```

Anything else can use the app's API directly:

| Call | Effect |
| :--- | :--- |
| `GET /api/state` | Current station, next departures per station, temperature, uptime |
| `GET /api/set?power=0` | Display off (`1` = on) |
| `GET /api/set?next=1` | Next station |
| `GET /api/set?pin=1` | Hold station 1 (`-1` = rotate again) |
| `GET /api/set?brightness=3` | Change any setting. Add `&save=1` to keep it after a restart. |
| `GET /api/set?icon1=wc&icon1_c=red` | Icon place 1 to 3: a symbol (`wc`, `door`, `window`, `light`, `power`, `house`, `key`, `bell`, `washer`, `dishes`, `dryer`, `coffee`, `trash`, `water`, `battery`, `temp`, `heart`, `mail`, `sun`, `cloud`, `rain`, `snow`, `storm`, `moon`, `dot`) or up to two letters; a leading `/` shows letters instead of a symbol (`/wc`). The color is empty for the LED tone, a name or `#RRGGBB`. An empty value clears the place. |
| `GET /api/message?text=Door%20opened&ttl=60&id=door` | Ticker message for 60 seconds. Several messages take turns on the ticker, each until its own time is up. `ttl=0` keeps it until cleared, `wake=1` shows it even while the display is off. |
| `GET /api/message?clear=1` | Clear the ticker messages (`&id=door` clears one) |
| `GET /api/config`, `POST /api/config` | Read, or write and save, all settings as JSON |
| `GET /api/debug` | Last request to the data server, memory, errors |

## Good to know

* **Data.** Departures come from T-Skylt's data server, like in the stock app. Which operators exist and how good their data is depends on that server.
* **Delays.** Most operators, Berlin included, deliver times that already contain the delay. The `+3` style only shows something where an operator sends the delay separately.
* **Line colors.** They are in `departuresplus/colors.txt`, one row per network, and only the rows of your own stations are loaded. Where a network is missing, the signet is drawn in the board's LED tone. Additions are welcome.
* **Lines field.** Entries are separated by a space or a comma. `U2 S7` shows only these lines, `-M4 -100` hides two, `-U7:2` hides U7 in direction 2 only. The small i next to the field on the settings page has more examples.
* **Station titles.** A title shows the station's name exactly as it stands in the settings, so edit the name there to change it.
* **Real-time mark.** Not every operator marks timetable-only departures. Berlin's *VBB/BVG* source does, *Berlin (Unofficial API)* does not.
* **Tested on** a T-Skylt X (128×32) with MatrixBOX v0.97. The other sizes (XS, XL, 2X) and newer firmware are tested in the simulator only.

## Try it without a board

```sh
git clone https://github.com/MatrixBOX-dev/matrixbox
git clone https://github.com/jnbp/matrixbox-departures-plus
pip install git+https://github.com/MatrixBOX-dev/simulator
python3 matrixbox-departures-plus/tools/simulate.py matrixbox --size X     # or XS, XL, 2X
```

This starts made-up departures for three Berlin stations, the app and the simulator window. The settings page is at `http://127.0.0.1:8080/`. Ctrl+C ends everything.

The pictures on this page are rendered from the app by `tools/render_docs.py`, and `tools/build_installers.py` builds the release files.

## License

MIT, like MatrixBOX. See [LICENSE](LICENSE).
