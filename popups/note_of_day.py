import tkinter as tk
from tkinter import font
import webbrowser
import requests
from bs4 import BeautifulSoup
import re

from art_db import ARTDatabase


class NoteOfDay(tk.Toplevel):
    """Popup window to display Note of the Day."""
    return_info = False

    def __init__(self, parent, art_db: ARTDatabase):
        """Init function. Open a popup window

        :param parent: main ART GUI window
        :param art_db: ART database
        """

        # get note of the day
        art_blog_url = art_db.get_configs(conf_key="art_blog_link")["art_blog_link"]["conf_value"]
        response = requests.get(art_blog_url)

        if response.status_code == 200:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            latest_blog = next(
                (a for a in soup.find_all('a') if re.search(r"\[\d{1,2}/\d{1,2}/\d{4}]\s+.+$", a.get_text())),
                None
            )
            self.latest_blog_link = latest_blog.get("href")
            title = re.search(r"\[\d{1,2}/\d{1,2}/\d{4}]\s+(?P<title>.+)$", latest_blog.get_text()).group("title")

            soup = BeautifulSoup(requests.get(self.latest_blog_link).text, 'html.parser')
            context = soup.find("div", class_="post-body").text.strip()[:150]

            super(NoteOfDay, self).__init__(parent)
            self.title("Note of the Day")

            title_font = font.Font(family="Helvetica", size=16)
            title_label = tk.Label(self, text=title, font=title_font)
            title_label.pack(padx=10, pady=5)
            context_label = tk.Label(self,
                                     text=f"{context}...",
                                     font=("Helvetica", 12),
                                     justify='left',
                                     wraplength=title_font.measure(title)+40)
            context_label.pack(padx=10, pady=5, anchor='w')

            read_more_label = tk.Label(self, text=f"read more..", font=("Helvetica", 10), fg="blue", cursor="hand2")
            read_more_label.pack(padx=10, pady=5, anchor='e')
            read_more_label.bind("<Button-1>", self.open_blog)

            # Create the Close button
            close_button = tk.Button(self, text="Close", command=self.destroy)
            close_button.pack(padx=10, pady=5, anchor='e')

        else:
            raise RuntimeError("Could not open ART Blog.")

    def open_blog(self, event) -> None:
        """Event when "read more" label clicked

        :param event: event (not in use)
        """
        webbrowser.open_new(self.latest_blog_link)
        self.destroy()
