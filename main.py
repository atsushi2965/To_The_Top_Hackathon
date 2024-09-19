import os
import sounddevice as sd
from tkinter import ACTIVE, LEFT, RIGHT, W, BooleanVar, Button, Frame, IntVar, Label, Listbox, OptionMenu, Radiobutton, Spinbox, StringVar, Tk  # Entry (& some of OptionMenu) -> Spinbox

from button_action import add_file, key_radio_toggle, pause_toggle, play_action, preview_action, stop_audio, update_radio_buttons
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


settings = load_settings('settings.txt')


def main():
    root = Tk()
    root.title(settings['title'])

    audio_interfaces = list_audio_interfaces()

    # vcmd = (root.register(validate_input), '%P')

    file_frame = Frame(root)
    file_frame.pack(side=LEFT, padx=10, pady=10)
    file_label = Label(file_frame, text=settings['file_label'])
    file_label.pack()
    file_list = Listbox(file_frame)
    file_list.pack()
    file_add = Button(file_frame, text=settings['file_add'], command=lambda: add_file(file_list))
    file_add.pack()

    delay_frame = Frame(root)
    delay_frame.pack(pady=10)
    delay_label = Label(delay_frame, text=settings['delay_label'])
    delay_label.pack(side=LEFT)
    delay_var = IntVar(int(settings['delay_entry_default']))
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

    own_key_frame = Frame(root)
    own_key_frame.pack(anchor=W)
    own_key_label = Radiobutton(own_key_frame, text=settings['own_key_label'], variable=key_radio, value=False)
    own_key_label.pack(side=LEFT)
    own_key_var = IntVar(int(settings['own_key_default']))
    own_key_menu = Spinbox(own_key_frame, textvariable=own_key_var, from_=-12, to=12, increment=1, format='%+1.0f', width=4, wrap=True)
    own_key_radio1 = Radiobutton(own_key_frame, variable=own_key_var)
    own_key_radio2 = Radiobutton(own_key_frame, variable=own_key_var)
    own_key_preview = Button(own_key_frame, text=settings['preview_button'], command=lambda: preview_action(own_key_var,  own_interface_var, file_list.get(ACTIVE), play_button, pause_button, stop_button))
    own_key_preview.pack(side=RIGHT)

    stream_key_frame = Frame(root)
    stream_key_frame.pack(anchor=W)
    stream_key_label = Radiobutton(stream_key_frame, text=settings['stream_key_label'], variable=key_radio, value=True)
    stream_key_label.pack(side=LEFT)
    stream_key_var = IntVar(int(settings['stream_key_default']))
    stream_key_menu = Spinbox(stream_key_frame, textvariable=stream_key_var, from_=-12, to=12, increment=1, format='%+1.0f', width=4, wrap=True)
    stream_key_radio1 = Radiobutton(stream_key_frame, variable=stream_key_var)
    stream_key_radio2 = Radiobutton(stream_key_frame, variable=stream_key_var)
    stream_key_preview = Button(stream_key_frame, text=settings['preview_button'], command=lambda: preview_action(stream_key_var,  own_interface_var, file_list.get(ACTIVE), play_button, pause_button, stop_button))
    stream_key_preview.pack(side=RIGHT)

    toggles = [key_radio, own_key_menu, own_key_radio2, own_key_radio1, stream_key_menu, stream_key_radio2, stream_key_radio1]
    own_key_label.config(command=lambda: key_radio_toggle(*toggles))
    stream_key_label.config(command=lambda: key_radio_toggle(*toggles))

    updates = [stream_key_var, pitch_var, own_key_var, own_key_radio1, own_key_radio2, stream_key_radio1, stream_key_radio2]
    own_key_var.trace('w', lambda *args: update_radio_buttons(*updates))
    stream_key_var.trace('w', lambda *args: update_radio_buttons(*updates))
    pitch_var.trace('w', lambda *args: update_radio_buttons(*updates))
    
    update_radio_buttons(*updates)
    key_radio_toggle(*toggles)

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

    button_frame = Frame(root)
    button_frame.pack()
    play_button = Button(button_frame, text=settings['play_button'], command=lambda: play_action(delay_entry, own_key_var, stream_key_var, own_interface_var, stream_interface_var, file_list.get(ACTIVE), play_button, pause_button, stop_button))
    play_button.pack(side=LEFT)
    pause_button = Button(button_frame, text=settings['pause_button'], state='disabled', command=lambda: pause_toggle(stop_button))
    pause_button.pack(side=LEFT)
    stop_button = Button(button_frame, text=settings['stop_button'], state='disabled', command=lambda: stop_audio(play_button, pause_button, stop_button))
    stop_button.pack(side=LEFT)

    root.mainloop()


if __name__ == '__main__':
    main()
