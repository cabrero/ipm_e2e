#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

w = Gtk.Window(title= "Contador")
w.connect('delete-event', Gtk.main_quit)

vbox = Gtk.Box(orientation= Gtk.Orientation.VERTICAL)

label1 = Gtk.Label(label= "Has pulsado 0 veces")
label1.show()
vbox.pack_start(label1, expand= True, fill= True, padding= 8)

button = Gtk.Button(label= "Contar")
button.show()
vbox.pack_start(button, expand= False, fill= False, padding= 8)

w.add(vbox)
w.show_all()

count = 0

def on_contar_clicked(widget):
    global count, label1
    count = count + 1
    veces = "1 vez" if count == 1 else f"{count} veces"
    label1.set_label(f"Has pulsado {veces}")

button.connect('clicked', on_contar_clicked)

Gtk.main()
