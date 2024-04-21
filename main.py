import os
import tkinter as tk
from tkinter import Label, Entry, Button, OptionMenu, StringVar, Frame
from settings import load_settings
from button_action import play_action
import sounddevice as sd

def validate_input(P):
    return P.isdigit() or P == ""

def list_audio_interfaces():
    interfaces = sd.query_devices()
    unique_devices = set()
    for device in interfaces:
        if device['max_output_channels'] > 0:
            unique_devices.add(device['name'])
    return list(unique_devices)

settings = load_settings("settings.txt")

def main():
    root = tk.Tk()
    root.title(settings['title'])

    audio_interfaces = list_audio_interfaces()

    vcmd = (root.register(validate_input), '%P')

    delay_frame = Frame(root)
    delay_frame.pack(padx=10, pady=10)

    delay_label = Label(delay_frame, text=settings['delay_label'])
    delay_label.pack(side=tk.LEFT)
    delay_entry = Entry(delay_frame, validate="key", validatecommand=vcmd, width=10, justify=tk.RIGHT)
    delay_entry.insert(0, settings['delay_entry_default'])
    delay_entry.pack(side=tk.LEFT)
    ms_label = Label(delay_frame, text="ms")
    ms_label.pack(side=tk.LEFT)

    pitch_label = Label(root, text=settings['pitch_label'])
    pitch_label.pack()
    key_options = [f"+{i}" if i > 0 else ("±0" if i == 0 else str(i)) for i in range(10, -11, -1)]
    pitch_var = StringVar(root)
    pitch_var.set(settings['pitch_default'])
    pitch_menu = OptionMenu(root, pitch_var, *key_options)
    pitch_menu.pack()

    own_key_label = Label(root, text=settings['own_key_label'])
    own_key_label.pack()
    own_key_var = StringVar(root)
    own_key_var.set(settings['own_key_default'])
    own_key_menu = OptionMenu(root, own_key_var, *key_options)
    own_key_menu.pack()

    stream_key_label = Label(root, text=settings['stream_key_label'])
    stream_key_label.pack()
    stream_key_var = StringVar(root)
    stream_key_var.set(settings['stream_key_default'])
    stream_key_menu = OptionMenu(root, stream_key_var, *key_options)
    stream_key_menu.pack()

    own_interface_label = Label(root, text=settings['own_interface_label'])
    own_interface_label.pack()
    own_interface_var = StringVar(root)
    own_interface_var.set(audio_interfaces[0])
    own_interface_menu = OptionMenu(root, own_interface_var, *audio_interfaces)
    own_interface_menu.pack()

    stream_interface_label = Label(root, text=settings['stream_interface_label'])
    stream_interface_label.pack()
    stream_interface_var = StringVar(root)
    stream_interface_var.set(audio_interfaces[0])
    stream_interface_menu = OptionMenu(root, stream_interface_var, *audio_interfaces)
    stream_interface_menu.pack()

    play_button = Button(root, text=settings['play_button'], command=lambda: play_action(delay_entry, pitch_var, own_key_var, stream_key_var, own_interface_var, stream_interface_var))
    play_button.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
