# Terminal-Music-Controller

Monitor *and* control your music from the terminal, with curses!

![Example view](example.png)
![Example view](example2.png)
![Example view](example3.png)

## Requirements
- Installed [playerctl](https://github.com/altdesktop/playerctl)
- Python 3 (any version compatible with `curses`)
  - `colorthief 0.2.1`
  - `pillow 10.3.0`
- Terminal that supports images, `kitty icat` is used for album art here though
  - Tested with Konsole and [Kitty](https://github.com/kovidgoyal/kitty). Works best with Kitty, Konsole needs some work...
- Nerd Font (optional, used only for player logos). I use [MesloLGS NF](https://github.com/romkatv/dotfiles-public/tree/master/.local/share/fonts/NerdFonts)

## Usage
Install reqs and just run:
```bash
python3 main.py
```
Add `-h`/`--help` for options.  
Use `-c`/`--cava` to colorize [cava](https://github.com/karlstav/cava) with colors from the current album art.  
Note: Be sure to point cava to `cava-config` configuration file like `cava -p cava-config`.

## Features
- Scrollable text if longer than window
- Album art!
- Moving progress bar
- Colors taken from the album art
- Colors of active position (current time) and progress bar blend seamlessly to colors of total time
- Buttons for playback control (+ keyboard keys)
- *Almost* detects current player
  - Cider and VLC are coded, others WIP
- Updates `cava` colors
## Known issues
- Will crash on start with `ValueError: invalid literal for int() with base 10: ''`
  - This is happening when more players are active and `playerctl` gets metadata from the wrong one.
  - May address it in the future, currently I have little knowledge of `playerctl` internals
- Sometimes image will pop-up and disappear
  - Resizing by any amount fixes this though
  - I'm debugging to see what causes this
## Roadmap
- ~~buttons for playback control~~ ✅
- ~~resizing?~~ ✅
- ~~better album art scaling~~ ✅
- ~~colors from album art~~ ✅
- ~~detect player and change the text accordingly~~ 🤏
  - If you use Spotify or Youtube Music... what are you doing here? There is `spotify-tui` and `ytermusic`!
- ~~don't destroy `cava` config on colors update~~ ✅
- seek support?