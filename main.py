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

screen = curses.initscr()
screen.immedok(True)
screen.border(0)
screen.nodelay(1)

curses.start_color()
curses.use_default_colors()
for i in range(0, curses.COLORS):
    curses.init_pair(i + 1, i, -1)

def scroll_string(string):
    new_string = string[1:] + string[0]
    return new_string

def get_color_from_percentage(base, percentage):
    return base + int(percentage / 20) % 6


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
                    'playerctl metadata length --format "{{ duration(mpris:length) }}"', shell=True, stdout=subprocess.PIPE
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

            box1.addstr(1, 2, " " * (half_cols - 10), curses.A_NORMAL)
            box1.addstr(2, 2, " " * (half_cols - 10), curses.A_NORMAL)
            box1.addstr(3, 2, " " * (half_cols - 10), curses.A_NORMAL)
            
            box1.addnstr(1, 2, "Title:  ", half_cols - 10, curses.color_pair(218))
            box1.addnstr(1, 10, old_title_scrolled, half_cols - 11)

            box1.addnstr(2, 2, "Album:  ", half_cols - 10, curses.color_pair(118))
            box1.addnstr(2, 10, old_album_scrolled, half_cols - 11)

            box1.addnstr(3, 2, "Artist: ", half_cols - 10, curses.color_pair(220))
            box1.addnstr(3, 10, old_artist_scrolled, half_cols - 11)


            
            # progress bar
            pos_str = position.stdout[:-1].decode("utf-8")
            cur_pos = sum(int(x) * 60 ** i for i, x in enumerate(pos_str.split(":")[::-1]))

            length_str = length.stdout[:-1].decode("utf-8")
            cur_length = sum(int(x) * 60 ** i for i, x in enumerate(length_str.split(":")[::-1]))

            percentage = cur_pos / cur_length * 100
            percentage = int(percentage)
            progress_bar = (half_cols - 3) * "-"
            progress_bar = progress_bar[:int(percentage / 100 * (half_cols - 3))] + "⬤" + progress_bar[int(percentage / 100 * (half_cols - 3)) + 1:]
            box1.addstr(6, 2, progress_bar, curses.A_NORMAL)

            box1.addstr(5, 2, position_str, curses.color_pair(get_color_from_percentage(215, percentage)))
            box1.addstr(5, half_cols - 1 - len(length_str), length_str, curses.color_pair(131))

            screen.refresh()
            screen.getch()
            time.sleep(1)
    finally:
        curses.endwin()


main_screen()



