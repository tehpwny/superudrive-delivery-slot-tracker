# coding: utf-8

# Simple GUI that will wait for a slot delivery in a given super-u drive stores

# sources:
# https://stackoverflow.com/questions/47627900/how-to-bind-async-method-to-a-keystroke-in-tkinter
# https://freres.peyronnet.eu/scraping-en-python-pour-etre-alerte-des-nouveaux-creneaux-drive-chez-super-u/

import requests
import urllib

from asyncio import ensure_future, get_event_loop, sleep as asleep
from tkinter import Label, Entry, Button, Tk, StringVar, TclError

from bs4 import BeautifulSoup
from lxml import html

from PIL import ImageTk, Image



class App(Tk):
    def __init__(self):
        super().__init__()
        self._configure()

    def _configure(self):
        self.title("drive-u delivery slot tracker")
        self.geometry('450x240')

        self.icon_size_x = 64
        self.icon_size_y = 64

        self.failed_icon = ImageTk.PhotoImage(Image.open("images/failed.png").resize((self.icon_size_x, self.icon_size_y)))
        self.success_icon = ImageTk.PhotoImage(Image.open("images/success.png").resize((self.icon_size_x, self.icon_size_y)))
        self.wait_icon = ImageTk.PhotoImage(Image.open("images/waiting.png").resize((self.icon_size_x, self.icon_size_y)))

        self.status_label = Label(self, image=self.wait_icon)
        self.status_label.grid(column=0, row=0)

        self.url_label = Label(self, text="URL du magasin:")
        self.url_label.grid(column=0, row=1)

        self.url_entry = Entry(self, width=50)
        self.url_entry.insert(0, "https://www.coursesu.com/drive-superu-montpellier")
        self.url_entry.grid(column=0, row=2)


        self.refresh_label = Label(self, text="Rafraichir toutes les (minutes): ")
        self.refresh_label.grid(column=0, row=3)

        self.refresh_entry = Entry(self, width=4, text='1')
        self.refresh_entry.insert(0, '1')
        self.refresh_entry.grid(column=0, row=4)

        self.slot_string_var = StringVar(value="Créneau disponible: ")
        self.slot_label = Label(self, textvariable=self.slot_string_var)
        self.slot_label.grid(column=0, row=5)

        # self.status_label.pack(side = "right", fill = "both", expand = "yes")

        self.search_button = Button(self, text="Rechercher", command=lambda: ensure_future(self.search(self.slot_string_var,
                                                                                                       self.status_label,
                                                                                                       self.url_entry,
                                                                                                       self.refresh_entry)))
        self.search_button.grid(column=0, row=6)

        self.close_button = Button(self, text="Fermer", command=self.close)
        self.close_button.grid(column=0, row=7)

        self.bind('<Return>', lambda _: ensure_future(self.search(self.slot_string_var,
                                                                  self.status_label,
                                                                  self.url_entry,
                                                                  self.refresh_entry)))



    def close(self):
        self.destroy()

    async def search(self, slot_string_var, status_label, url_entry, refresh):
        # print('%s executed!' % self.search.__name__)
        slot_string_var.set("Créneau disponible: (recherche en cours...)")
        status_label.configure(image=self.wait_icon)
        while True:
            try:
                urllib.request.urlopen(url_entry.get()).getcode()
            except urllib.error.HTTPError:
                slot_string_var.set("Créneau disponible: (Erreur: l'URL du magasin est invalide)")
                status_label.configure(image=self.failed_icon)
                break

            resp = requests.get(url_entry.get())
            data = resp.content
            soup = BeautifulSoup(data, "lxml")
            tree = html.fromstring(data)
            isit = tree.xpath('//a[@class="store__content-delivery hidden"]/text()')
            if not isit or isit[0] == "Information momentanément indisponible":
                slot_string_var.set(
                    'Créneau disponible: Information momentanément indisponible, nouvelle tentative dans {} minute(s)'.format(refresh.get())
                )
                status_label.configure(image=self.wait_icon)
                print("Pas d'information, nouvelle tentative dans {} minute(s)".format(refresh.get()))
                await asleep(int(refresh.get())*60)
                continue
            else:
                slot_string_var.set('Créneau disponible: {}'.format(isit[0]))
                status_label.configure(image=self.success_icon)
                print('Créneau disponible: {}'.format(isit[0]))
                break


async def run_tk(root):
    try:
        while True:
            root.update()
            await asleep(.01)
    except TclError as e:
        if "application has been destroyed" not in e.args[0]:
            raise

if __name__ == '__main__':
    app = App()
    get_event_loop().run_until_complete(run_tk(app))
