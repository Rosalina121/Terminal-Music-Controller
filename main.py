#    cur_title=`playerctl metadata title`
#     cur_album=`playerctl metadata album`
#     cur_artist=`playerctl metadata artist`

#     #basic information, hostname, date, ...
#     window "Now Playing..." "red" "50%"
#         append_tabbed "Title:$cur_title" 2
#         append "\e[38;5;33mAlbum\e[0m $cur_album"
#         append "\e[38;5;33mArtist\e[0m $cur_artist"
#         addsep
#         append "`playerctl position --format "{{ duration(position) }}"` - `playerctl metadata length --format "{{ duration(mpris:length) }}"`"
#     endwin


import curses
import math

import subprocess
import time
import io
import sys

from urllib.request import urlopen
from colorthief import ColorThief
from wcwidth import wcswidth




def init_color():
    # curses is truly terminal independent and has r/g/b between 0 and 1000
    # this is a bit cumbersome if you're used to 0...255
    # so we need to convert them
    # r - 0...255
    # R - 0...1000
    # Equation:
    # r = R * .255
    # R = r / .255

    curses.start_color()
    curses.use_default_colors()

    # Primary colors
    curses.init_pair(1, 1, -1)
    curses.init_pair(2, 2, -1)
    curses.init_pair(3, 3, -1)
    # Inverted
    curses.init_pair(4, -1, 1)
    curses.init_pair(5, -1, 2)
    curses.init_pair(6, -1, 3)
    # Special pair for player color
    curses.init_pair(99, 4, -1)


def scroll_string(string):
    # if wcswidth(string[0]) < 2:  
        new_string = string[1:] + string[0]
        return new_string
    # else:
    #     return string


def get_color_from_percentage(base, percentage):
    return base + int(percentage / 20) % 6


if any(arg in ["-h", "--help"] for arg in sys.argv):
    print("Usage: python3 ./main.py [options]")
    print("Options:")
    print("    -c, --cava       Update cava config with colors from album art")
    print(
        '                     Be cure to point cava to "cava-config" configuration file'
    )
    print('                     i.e. "cava -p cava-config"')
    print("    -h, --help       Print this help message")
    sys.exit(0)

# init curses
screen = curses.initscr()
screen.immedok(True)
screen.nodelay(1)
screen.keypad(1)

curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
curses.flushinp()
curses.noecho()
curses.curs_set(0)

init_color()


def draw_progress_bar(box, pos_str, length_str, max_x, base_rgb, target_rgb):
    cur_pos = sum(int(x) * 60**i for i, x in enumerate(pos_str.split(":")[::-1]))
    cur_length = sum(int(x) * 60**i for i, x in enumerate(length_str.split(":")[::-1]))

    percentage = cur_pos / cur_length * 100
    percentage = int(percentage)

    progress_bar = (max_x - 4) * "·"
    progress_bar_filled = (max_x - 4) * "━"
    box.addnstr(6, 2, progress_bar, max_x - 4, curses.color_pair(3))
    progress_bar_length = int(percentage / 100 * (max_x - 4))
    if progress_bar_length != 0:
        box.addnstr(
            6, 2, progress_bar_filled, progress_bar_length, curses.color_pair(1)
        )
        if progress_bar_length < max_x - 4:
            box.addstr(6, 1 + progress_bar_length, "━", curses.color_pair(2))

    box.addstr(5, 2, pos_str, curses.color_pair(1))

    box.addstr(5, max_x - 2 - len(length_str), length_str, curses.color_pair(3))

    blend_and_init_color(base_rgb, target_rgb, percentage)


def blend_and_init_color(base, target, percentage):
    r_base, g_base, b_base = base
    r_target, g_target, b_target = target

    r = int(r_base + percentage / 100 * (r_target - r_base))
    g = int(g_base + percentage / 100 * (g_target - g_base))
    b = int(b_base + percentage / 100 * (b_target - b_base))

    curses.init_color(
        1,
        min(max(int(r / 0.255), 0), 1000),
        min(max(int(g / 0.255), 0), 1000),
        min(max(int(b / 0.255), 0), 1000),
    )


def set_colors_from_album_art(cover_art_url_url):
    fd = urlopen(cover_art_url_url)
    img = io.BytesIO(fd.read())
    color_thief = ColorThief(img)

    palette = color_thief.get_palette(
        quality=1, color_count=2
    )  # for some reason color_count is 0 indexed? Here returns 3

    c = 1
    for color in palette:
        [r, g, b] = color
        hsp = math.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))
        if hsp > 127.5:
            curses.init_color(
                c, int(color[0] / 0.255), int(color[1] / 0.255), int(color[2] / 0.255)
            )
        else:
            factor = 3.5
            # Normalize the RGB values to the range [0, 1]
            normalized_rgb = [component / 255.0 for component in color]

            # Increase the brightness by multiplying by the factor
            brighter_rgb = [component * factor for component in normalized_rgb]

            # Clip the values to the range [0, 1]
            clipped_rgb = [min(1.0, component) for component in brighter_rgb]

            # Denormalize the values back to the range [0, 255]
            final_rgb = [int(component * 255) for component in clipped_rgb]

            curses.init_color(
                c,
                int(final_rgb[0] / 0.255),
                int(final_rgb[1] / 0.255),
                int(final_rgb[2] / 0.255),
            )

        c += 1
    return palette


def update_cava_config(palette):
    f = open("cava-config", "w+")
    f.write(
        """
[color]

gradient = 1
gradient_count = 3
gradient_color_1 = {0}
gradient_color_2 = {1}
gradient_color_3 = {2}
        """.format(
            "'#{:02x}{:02x}{:02x}'".format(palette[0][0], palette[0][1], palette[0][2]),
            "'#{:02x}{:02x}{:02x}'".format(palette[1][0], palette[1][1], palette[1][2]),
            "'#{:02x}{:02x}{:02x}'".format(palette[2][0], palette[2][1], palette[2][2]),
        )
    )
    f.close()
    subprocess.run(["pkill", "-USR2", "cava"])


def main_screen():
    try:
        lines, cols = screen.getmaxyx()

        half_cols = int(cols / 2)
        half_lines = int(lines / 2)

        if half_cols > lines * 2:
            box1 = curses.newwin(lines, cols - lines * 2, 0, 0)
            box2 = curses.newwin(lines, lines * 2, 0, cols - lines * 2)
            safe_line_width = cols - lines * 2

        else:
            box1 = curses.newwin(lines, half_cols, 0, 0)
            box2 = curses.newwin(lines, half_cols, 0, half_cols)
            safe_line_width = half_cols

        # metdata
        old_title = ""
        old_title_scrolled = ""
        old_album_scrolled = ""
        old_artist_scrolled = ""

        max_text_len = safe_line_width - 12

        box1.immedok(True)
        box2.immedok(True)

        # Debug:
        # box1.addstr(8, 2, f"Lines: {lines}, Columns: {cols}, 2xLines: {2*lines}, half_cols: {half_cols}", curses.color_pair(1))

        # Media logos
        current_media_app = subprocess.run(
            "playerctl -l", shell=True, stdout=subprocess.PIPE
        )
        if "cider" in current_media_app.stdout[:-1].decode("utf-8"):
            curses.init_color(4, int(250 / 0.255), int(45 / 0.255), int(72 / 0.255))
            box1.addstr(lines - 2, 2, "\ue711 Music", curses.color_pair(99))
        elif "vlc" in current_media_app.stdout[:-1].decode("utf-8"):
            curses.init_color(4, int(232 / 0.255), int(94 / 0.255), int(0 / 0.255))
            box1.addstr(lines - 2, 2, "󰕼 VLC", curses.color_pair(99))
        else:
            curses.init_color(4, int(250 / 0.255), int(45 / 0.255), int(72 / 0.255))
            box1.addstr(lines - 2, 2, "♫ Unknown", curses.color_pair(1))
        # TODO: Add more

        # image art prep
        box2.box()
        if half_cols > lines * 2:
            image_size_and_pos = f"{2*lines - 2}x{2*lines - 2}@{cols - lines * 2 + 1}x1"
        else:
            image_size_and_pos = f"{half_cols-2}x{half_cols-2}@{half_cols+1}x1"



        # palette
        palette = []
        while True:
            title = subprocess.run(
                "playerctl metadata title", shell=True, stdout=subprocess.PIPE
            )
            if title.stdout[:-1].decode("utf-8") != old_title:
                old_title = title.stdout[:-1].decode("utf-8")

                cover_art_url = subprocess.run(
                    "playerctl metadata mpris:artUrl",
                    shell=True,
                    stdout=subprocess.PIPE,
                )
                cover_art_url_url = cover_art_url.stdout[:-1].decode("utf-8")
                palette = set_colors_from_album_art(cover_art_url_url)

                # cava
                if any(arg in ["-c", "--cava"] for arg in sys.argv):
                    update_cava_config(palette)

                subprocess.run(["/home/rosalina/.local/bin/kitty", "icat", "--clear"])
                subprocess.run(
                    [
                        "/home/rosalina/.local/bin/kitty",
                        "icat",
                        "--scale-up",
                        "--place",
                        image_size_and_pos,
                        cover_art_url.stdout[:-1],
                    ],
                    shell=False,
                )

                album = subprocess.run(
                    "playerctl metadata album", shell=True, stdout=subprocess.PIPE
                )
                artist = subprocess.run(
                    "playerctl metadata artist", shell=True, stdout=subprocess.PIPE
                )
                length = subprocess.run(
                    'playerctl metadata length --format "{{ duration(mpris:length) }}"',
                    shell=True,
                    stdout=subprocess.PIPE,
                )

                old_title_scrolled = title.stdout[:-1].decode("utf-8") + "    "
                old_album_scrolled = album.stdout[:-1].decode("utf-8") + "    "
                old_artist_scrolled = artist.stdout[:-1].decode("utf-8") + "    "

                # clean time, usually not needed, but some songs are longer than 10 mins ;)
                box1.addstr(5, 2, " " * (safe_line_width - 4), curses.A_NORMAL)

            # check if playing
            status = subprocess.run(
                "playerctl status", shell=True, stdout=subprocess.PIPE
            )

            # play/pause button, and scrolling text
            box1.addstr(7, 2, "P", curses.color_pair(2) | curses.A_UNDERLINE)
            if status.stdout[:-1].decode("utf-8") == "Playing":
                box1.addstr(7, 3, "ause", curses.color_pair(2))

                if wcswidth(old_title_scrolled) > max_text_len:
                    old_title_scrolled = scroll_string(old_title_scrolled)
                if wcswidth(old_album_scrolled) > max_text_len:
                    old_album_scrolled = scroll_string(old_album_scrolled)
                if wcswidth(old_artist_scrolled) > max_text_len:
                    old_artist_scrolled = scroll_string(old_artist_scrolled)
            else:
                box1.addstr(7, 3, "lay ", curses.color_pair(2))

            wc_title_offset = wcswidth(old_title_scrolled) - len(old_title_scrolled)
            wc_album_offset = wcswidth(old_album_scrolled) - len(old_album_scrolled)
            wc_artist_offset = wcswidth(old_artist_scrolled) -len(old_artist_scrolled)

            # debug offsets for wide characters
            # box1.addstr(9, 5, "wctitleoffset: " + str(wc_title_offset), curses.A_NORMAL)
            # box1.addstr(10, 5, "wcalbumoffset: " + str(wc_album_offset), curses.A_NORMAL)
            # box1.addstr(11, 5, "wcartistoffset: " + str(wc_artist_offset), curses.A_NORMAL)

            position = subprocess.run(
                'playerctl position --format "{{ duration(position) }}"',
                shell=True,
                stdout=subprocess.PIPE,
            )
            position_str = position.stdout[:-1].decode("utf-8")
            length_str = length.stdout[:-1].decode("utf-8")

            box1.addstr(1, 2, " " * (safe_line_width - 4), curses.A_NORMAL)
            box1.addstr(2, 2, " " * (safe_line_width - 4), curses.A_NORMAL)
            box1.addstr(3, 2, " " * (safe_line_width - 4), curses.A_NORMAL)

            box1.addnstr(1, 2, "Title:  ", max_text_len, curses.color_pair(2))
            box1.addnstr(1, 10, old_title_scrolled, max_text_len - wc_title_offset)

            box1.addnstr(2, 2, "Album:  ", max_text_len, curses.color_pair(2))
            box1.addnstr(2, 10, old_album_scrolled, max_text_len - wc_album_offset)

            box1.addnstr(3, 2, "Artist: ", max_text_len, curses.color_pair(2))
            box1.addnstr(3, 10, old_artist_scrolled, max_text_len - wc_artist_offset)

            if palette:
                draw_progress_bar(
                    box1,
                    position_str,
                    length_str,
                    safe_line_width,
                    palette[0],
                    palette[2],
                )

            # Next/Previous
            box1.addstr(7, 8, "N", curses.color_pair(3) | curses.A_UNDERLINE)
            box1.addstr(7, 9, "ext", curses.color_pair(3))
            box1.addstr(7, 13, "P", curses.color_pair(3))
            box1.addstr(7, 14, "r", curses.color_pair(3) | curses.A_UNDERLINE)
            box1.addstr(7, 15, "evious", curses.color_pair(3))

            key = screen.getch()
            if key == curses.KEY_RESIZE:
                curses.endwin()
                main_screen()
            if key == ord("q"):
                curses.endwin()
                quit()

            if key == curses.KEY_MOUSE:
                _, x, y, _, _ = curses.getmouse()
                # Play/Pause
                if y == 7 and x >= 2 and x <= 6:
                    subprocess.run(["playerctl", "play-pause"])
                # Next
                if y == 7 and x >= 8 and x <= 11:
                    subprocess.run(["playerctl", "next"])
                # Previous
                if y == 7 and x >= 13 and x <= 20:
                    subprocess.run(["playerctl", "previous"])
            if key == ord("p"):
                subprocess.run(["playerctl", "play-pause"])
            if key == ord("n"):
                subprocess.run(["playerctl", "next"])
            if key == ord("r"):
                subprocess.run(["playerctl", "previous"])

            box1.border(0)
            box2.border(0)

            screen.refresh()
            time.sleep(0.5)
    finally:
        curses.endwin()

# uncomment for shitty error handling
# try:
main_screen()
# except:
#     # lol no
#     curses.endwin()
#     screen = curses.initscr()
#     screen.immedok(True)
#     screen.nodelay(1)
#     screen.keypad(1)

#     curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
#     curses.flushinp()
#     curses.noecho()
#     curses.curs_set(0)

#     init_color()
#     main_screen()
