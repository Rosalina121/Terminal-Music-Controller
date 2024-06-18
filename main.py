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
import textwrap
import subprocess
import time
from urllib.request import urlopen
from colorthief import ColorThief
import sys
import io


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

    curses.init_color(1, 0, 0, 0)  # white for progress
    curses.init_color(2, int(245 / 0.255), int(169 / 0.255), int(184 / 0.255))  # pink
    curses.init_color(3, int(91 / 0.255), int(206 / 0.255), int(250 / 0.255))  # blue

    curses.init_pair(1, 1, 0)  # white
    curses.init_pair(2, 2, 0)  # pink
    curses.init_pair(3, 3, 0)  # blue

    # # set default colors
    # curses.use_default_colors()
    # for i in range(0, curses.COLORS):
    #     curses.init_pair(i + 1, i, -1)


def scroll_string(string):
    new_string = string[1:] + string[0]
    return new_string


def get_color_from_percentage(base, percentage):
    return base + int(percentage / 20) % 6


screen = curses.initscr()
screen.immedok(True)
screen.border(0)
screen.nodelay(1)

init_color()


def draw_progress_bar(box, pos_str, length_str, max_x, base_rgb, target_rgb):
    cur_pos = sum(int(x) * 60**i for i, x in enumerate(pos_str.split(":")[::-1]))
    cur_length = sum(int(x) * 60**i for i, x in enumerate(length_str.split(":")[::-1]))

    percentage = cur_pos / cur_length * 100
    percentage = int(percentage)

    progress_bar = (max_x - 4) * "━"
    box.addnstr(6, 2, progress_bar, max_x - 4)
    progress_bar_length = int(percentage / 100 * (max_x - 4))
    if progress_bar_length != 0:
        box.addnstr(6, 2, progress_bar, progress_bar_length, curses.color_pair(3))
    

    box.addstr(5, 2, pos_str, curses.color_pair(1))

    box.addstr(5, max_x - 2 - len(length_str), length_str, curses.color_pair(3))

    blend_and_init_color(base_rgb, target_rgb, percentage)


def blend_and_init_color(base, target, percentage):
    r_base, g_base, b_base = base
    r_target, g_target, b_target = target

    r = int(r_base + percentage / 100 * (r_target - r_base))
    g = int(g_base + percentage / 100 * (g_target - g_base))
    b = int(b_base + percentage / 100 * (b_target - b_base))

    curses.init_color(1, min(int(r / 0.255), 1000), min(int(g / 0.255), 1000), min(int(b / 0.255), 1000))

def set_colors_from_album_art(cover_art_url_url):
    fd = urlopen(cover_art_url_url)
    img = io.BytesIO(fd.read())
    color_thief = ColorThief(img)
    palette = color_thief.get_palette(quality=1, color_count=3)
    c = 1
    for color in palette:
        curses.init_color(c, int(color[0]/.255), int(color[1]/.255), int(color[2]/.255))
        c += 1
    return palette

def main_screen():
    try:
        lines, cols = screen.getmaxyx()

        half_cols = int(cols / 2)
        half_lines = int(lines / 2)

        box1 = curses.newwin(lines, half_cols, 0, 0)
        box2 = curses.newwin(lines, half_cols, 0, half_cols)

        box1.border(0)
        box2.border(0)

        box1.immedok(True)
        box2.immedok(True)

        # image art shit
        box2.box()
        image_size_and_pos = f"{half_cols-2}x{half_cols-2}@{half_cols+1}x1"

        # metdata
        old_title = ""
        old_title_scrolled = ""
        old_album_scrolled = ""
        old_artist_scrolled = ""

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

                old_title_scrolled = title.stdout[:-1].decode("utf-8") + " "
                old_album_scrolled = album.stdout[:-1].decode("utf-8") + " "
                old_artist_scrolled = artist.stdout[:-1].decode("utf-8") + " "

            if len(old_title_scrolled) > half_cols - 11:
                old_title_scrolled = scroll_string(old_title_scrolled)
            if len(old_album_scrolled) > half_cols - 11:
                old_album_scrolled = scroll_string(old_album_scrolled)
            if len(old_artist_scrolled) > half_cols - 11:
                old_artist_scrolled = scroll_string(old_artist_scrolled)
            position = subprocess.run(
                'playerctl position --format "{{ duration(position) }}"',
                shell=True,
                stdout=subprocess.PIPE,
            )
            position_str = position.stdout[:-1].decode("utf-8")
            length_str = length.stdout[:-1].decode("utf-8")

            box1.addstr(1, 2, " " * (half_cols - 2), curses.A_NORMAL)
            box1.addstr(2, 2, " " * (half_cols - 2), curses.A_NORMAL)
            box1.addstr(3, 2, " " * (half_cols - 2), curses.A_NORMAL)

            box1.addnstr(1, 2, "Title:  ", half_cols - 10, curses.color_pair(2))
            box1.addnstr(1, 10, old_title_scrolled, half_cols - 11)

            box1.addnstr(2, 2, "Album:  ", half_cols - 10, curses.color_pair(2))
            box1.addnstr(2, 10, old_album_scrolled, half_cols - 11)

            box1.addnstr(3, 2, "Artist: ", half_cols - 10, curses.color_pair(2))
            box1.addnstr(3, 10, old_artist_scrolled, half_cols - 11)
            if palette:
                draw_progress_bar(box1, position_str, length_str, half_cols, palette[1], palette[2])

            screen.refresh()
            screen.getch()
            time.sleep(1)
    finally:
        curses.endwin()


main_screen()
