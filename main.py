"""
Add Cover Art:
This application will find the .mp3 files in your computer.
Then it will automatically scrape a suitable cover from google images and apply
it as a cover art to the mp3 file.
"""

import argparse
import eyed3
import logging
import os
import re
import tkinter as tk
from PIL import ImageTk, Image
from urllib.error import HTTPError, URLError

from scrape_image_from_google_images import scrape_google_image

logging.basicConfig(level=logging.VERBOSE, format='%(message)s')
logging.getLogger().setLevel(logging.VERBOSE)

__all__ = ('add_cover_art','add_image')

class tkinter_window:
    is_cancelled = False

    def __init__(self, art_filename, song_filename):
        self.song_filename = song_filename
        self.art_filename = art_filename

        self.window = tk.Tk()
        self.window.title("Add cover art")
        self.window.geometry("300x210")
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)

        heading = tk.Label(self.window,
                           text='Do you want this image as cover art?\n' + os.path.split(self.song_filename)[-1])
        self.image_panel = tk.Label(self.window)
        self.update_image()

        song_query_question = tk.Label(self.window, text='Enter text to search')
        self.song_query = tk.Entry(self.window)

        self.search_button = tk.Button(self.window, text="  Search  ", command=self.on_search)
        apply_button = tk.Button(self.window, text="Apply", command=self.on_apply)
        next_button = tk.Button(self.window, text="Next", command=self.on_next)
        cancel_button = tk.Button(self.window, text="Cancel", command=self.on_cancel)

        heading.grid(column=0, row=0, columnspan=6, rowspan=2)
        self.image_panel.grid(column=0, row=3, columnspan=3, rowspan=3)
        song_query_question.grid(column=3, row=3, columnspan=4, rowspan=1)
        self.song_query.grid(column=3, row=4, columnspan=4, rowspan=1)

        self.search_button.grid(column=4, row=5, columnspan=4, rowspan=1)
        apply_button.grid(column=1, row=6, columnspan=1)
        next_button.grid(column=4, row=6)
        cancel_button.grid(column=5, row=6)

        self.window.mainloop()

    def update_image(self):
        image = ImageTk.PhotoImage(Image.open(self.art_filename).resize((150, 150), Image.ANTIALIAS))
        self.image_panel.configure(image=image)
        self.image_panel.image = image

    def on_search(self):
        self.search_button.configure(state='disabled', text='Searching..')
        self.window.update()
        song_query = self.song_query.get()
        art_directory = scrape_google_image(song_query + " song cover art", name=song_query, max_num=1)
        self.art_filename = os.path.join(art_directory, os.listdir(art_directory)[0])
        self.update_image()
        self.search_button.configure(state='normal', text='Search')

    def on_cancel(self):
        self.is_cancelled = True
        self.window.destroy()

    def on_apply(self):
        add_image(self.art_filename, self.song_filename)

    def on_next(self):
        self.window.destroy()


def add_image(art_filename, song_filename):
    logging.log(logging.VERBOSE, "Adding cover art: %s", song_filename)
    audiofile = eyed3.load(song_filename)
    if audiofile.tag is None:
        audiofile.initTag()
    elif audiofile.tag.album_artist:
        logging.log(logging.VERBOSE, 'Artist: %s', audiofile.tag.album_artist)
    audiofile.tag.images.set(3, open(art_filename, 'rb').read(), 'image/jpeg')
    audiofile.tag.save()


def extract_query(file_path):
    song_name = os.path.split(file_path)[-1]  # Get songs name from file path
    song_name = song_name.lstrip("0123456789.- ")  # Strip track no and numbers from the song names using lstrip
    song_name = "".join(song_name.split('.')[:-1])  # Remove extension from song names
    song_name = song_name.replace("-", " ").replace("_", " ")
    song_name = re.sub(r"\d\d\d\s*kbps", " ", song_name, flags=re.I)
    song_name = re.sub(r"[\(\[].*?[\)\]]", "", song_name)  # Replace '-','_','320','Kbps','kbps' sign with ' '
    song_name = re.sub(" +", " ", song_name)  # Remove anything in between (),[],{} and replace multiple spaces
    return song_name


def add_cover_art(path='.', no_gui=False, max_num=1):
    song_filenames = []
    if os.path.isdir(path):
        logging.log(logging.VERBOSE, "Finding all .mp3 files in: %s", path)
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.mp3'):
                    song_filenames.append(os.path.join(root, file))
    elif os.path.isfile(path) and args.file.endswith('.mp3'):
        logging.log(logging.VERBOSE, "Finding: %s", path)
        song_filenames.append(os.path.abspath(path))

    for song_filename in song_filenames:
        logging.log(logging.VERBOSE, "Processing file: %s", song_filename)
        song_query = extract_query(song_filename)
        try:
            art_directory = scrape_google_image(song_query + " song cover art", name=song_query, max_num=1)
            art_filename = os.path.join(art_directory, os.listdir(art_directory)[0])
            if not no_gui:
                window = tkinter_window(art_filename, song_filename)
                if window.is_cancelled:
                    exit()
            else:
                add_image(art_filename, song_filename)
        except (HTTPError, URLError, ValueError) as e:
            logging.warning('Unable to download images: %s', e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', default=os.getcwd(),
                        help='file or directory to be processed (default: current directory)')
    parser.add_argument('--no-gui', action='store_true', help="don't use a gui, automatically add cover art")
    parser.add_argument('--silent', action='store_true', help="don't show console output")
    args = parser.parse_args()

    if args.silent:
        logging.disable()
    add_cover_art(path=args.path, no_gui=args.no_gui)
