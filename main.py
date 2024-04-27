from numpy import sign
import os
import sounddevice as sd
import tkinter as tk
from tkinter import LEFT, RIGHT, W, BooleanVar, Button, Frame, IntVar, Label, OptionMenu, Radiobutton, Spinbox, StringVar  # Entry (& some of OptionMenu) -> Spinbox

from button_action import play_action
from settings import load_settings


# def validate_input(P):
#     return P.isdigit() or P == ""


def list_audio_interfaces():
    #
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

    # vcmd = (root.register(validate_input), '%P')

    delay_frame = Frame(root)
    delay_frame.pack(padx=10, pady=10)
    delay_label = Label(delay_frame, text=settings['delay_label'])
    delay_label.pack(side=LEFT)
    delay_var = IntVar(value=int(settings['delay_entry_default']))
    delay_entry = Spinbox(delay_frame, textvariable=delay_var, from_=0, to=8191, increment=1, width=4, justify=RIGHT)
    # delay_entry.insert(0, settings['delay_entry_default'])
    delay_entry.pack(side=LEFT)
    ms_label = Label(delay_frame, text="ms")
    ms_label.pack(side=LEFT)

    pitch_frame = Frame(root)
    pitch_frame.pack()
    pitch_label = Label(pitch_frame, text=settings['pitch_label'])
    pitch_label.pack(side=LEFT)
    # key_options = [f"{i:+}" if i != 0 else "±0" for i in range(-12, 13)]
    pitch_var = IntVar(int(settings['pitch_default']))
    # pitch_var.set(settings['pitch_default'])
    pitch_menu = Spinbox(pitch_frame, textvariable=pitch_var, from_=-12, to=12, increment=1, format='%+1.0f', width=4, wrap=True)
    pitch_menu.pack(side=LEFT)

    # own_key_label = Label(root, text=settings['own_key_label'])
    # own_key_label.pack()
    # own_key_var = StringVar(root)
    # own_key_var.set(settings['own_key_default'])
    # own_key_menu = OptionMenu(root, own_key_var, *key_options)
    # own_key_menu.pack()

    # stream_key_label = Label(root, text=settings['stream_key_label'])
    # stream_key_label.pack()
    # stream_key_var = StringVar(root)
    # stream_key_var.set(settings['stream_key_default'])
    # stream_key_menu = OptionMenu(root, stream_key_var, *key_options)
    # stream_key_menu.pack()

    key_radio = BooleanVar()

    def key_radio_toggle():
        if key_radio.get():  # True: stream
            own_key_menu.pack_forget()
            own_key_radio2.pack(side=LEFT)
            own_key_radio1.pack(side=LEFT)  # less on left
            stream_key_menu.pack(side=LEFT)
            stream_key_radio2.pack_forget()
            stream_key_radio1.pack_forget()
        else:  # False: own
            own_key_menu.pack(side=LEFT)
            own_key_radio2.pack_forget()
            own_key_radio1.pack_forget()
            stream_key_menu.pack_forget()
            stream_key_radio2.pack(side=LEFT)
            stream_key_radio1.pack(side=LEFT)  # less on left

    def update_radio_buttons():
        own_key1 = (stream_key_var.get() - pitch_var.get()) % 12
        own_key2 = own_key1 - 12*sign(own_key1) if own_key1 != 0 else 12*sign(pitch_var.get())
        stream_key1 = (own_key_var.get() + pitch_var.get()) % 12
        stream_key2 = stream_key1 - 12*sign(stream_key1) if stream_key1 != 0 else 12*sign(pitch_var.get())
        own_key_radio1.config(text=f"{own_key1:+}")
        own_key_radio2.config(text=f"{own_key2:+}")
        stream_key_radio1.config(text=f"{stream_key1:+}")
        stream_key_radio2.config(text=f"{stream_key2:+}")
        own_key_radio1['value'] = own_key1
        own_key_radio2['value'] = own_key2
        stream_key_radio1['value'] = stream_key1
        stream_key_radio2['value'] = stream_key2

    own_key_frame = Frame(root)
    own_key_frame.pack(anchor=W)
    own_key_label = Radiobutton(own_key_frame, text=settings['own_key_label'], variable=key_radio, value=False, command=key_radio_toggle)
    own_key_label.pack(side=LEFT)
    own_key_var = IntVar(int(settings['own_key_default']))
    own_key_menu = Spinbox(own_key_frame, textvariable=own_key_var, from_=-12, to=12, increment=1, format='%+1.0f', width=4, wrap=True)
    own_key_radio1 = Radiobutton(own_key_frame, variable=own_key_var)
    own_key_radio2 = Radiobutton(own_key_frame, variable=own_key_var)

    stream_key_frame = Frame(root)
    stream_key_frame.pack(anchor=W)
    stream_key_label = Radiobutton(stream_key_frame, text=settings['stream_key_label'], variable=key_radio, value=True, command=key_radio_toggle)
    stream_key_label.pack(side=LEFT)
    stream_key_var = IntVar(int(settings['stream_key_default']))
    stream_key_menu = Spinbox(stream_key_frame, textvariable=stream_key_var, from_=-12, to=12, increment=1, format='%+1.0f', width=4, wrap=True)
    stream_key_radio1 = Radiobutton(stream_key_frame, variable=stream_key_var)
    stream_key_radio2 = Radiobutton(stream_key_frame, variable=stream_key_var)

    own_key_var.trace('w', lambda *args: update_radio_buttons())
    stream_key_var.trace('w', lambda *args: update_radio_buttons())
    pitch_var.trace('w', lambda *args: update_radio_buttons())
    
    update_radio_buttons()
    key_radio_toggle()

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
