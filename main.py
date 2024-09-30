import sys
sys.stderr = sys.stdout
from importlib.abc import MetaPathFinder
class ImportLogger(MetaPathFinder):
    def __init__(self):
        self.loaded_modules = set()
    def find_spec(self, fullname, path, target=None):
        if fullname not in self.loaded_modules:
            print('Importing:', fullname)
            self.loaded_modules.add(fullname)
        return None
sys.meta_path.insert(0, ImportLogger())

from tkinter import DISABLED, LEFT, RIGHT, W, BooleanVar, Button, Frame, IntVar, Label, Listbox, OptionMenu, Radiobutton, Spinbox, StringVar, Tk

from button_action import DEVICES, add_file, key_radio_toggle, pause_toggle, play_action, preview_action, stop_audio, update_keyf
from settings import SETTINGS


def main():
    device_names = list(DEVICES)

    root = Tk()
    root.title(SETTINGS['title'])

    file_frame = Frame(root)
    file_frame.pack(side=LEFT, padx=10, pady=10)
    Label(file_frame, text=SETTINGS['file_label']).pack()
    file_list = Listbox(file_frame)
    file_list.pack()
    Button(file_frame, text=SETTINGS['file_add'], command=lambda: add_file(file_list)).pack()

    delay_frame = Frame(root)
    delay_frame.pack(pady=10)
    Label(delay_frame, text=SETTINGS['delay_label']).pack(side=LEFT)
    delay_var = IntVar(int(SETTINGS['delay_entry_default']))
    Spinbox(
        delay_frame,
        justify=RIGHT,
        textvariable=delay_var,
        from_=0,
        to=8191,
        width=4
    ).pack(side=LEFT)
    Label(delay_frame, text='ms').pack(side=LEFT)

    pitch_frame = Frame(root)
    pitch_frame.pack()
    Label(pitch_frame, text=SETTINGS['pitch_label']).pack(side=LEFT)
    pitch_var = IntVar(int(SETTINGS['pitch_default']))
    pitch_spin = Spinbox(
        pitch_frame,
        textvariable=pitch_var,
        format='%+0.0f',
        from_=-12,
        to=12,
        width=4,
        wrap=True
    )
    pitch_spin.pack(side=LEFT)

    key_radio_var = BooleanVar()

    def toggles():
        '''現在の値を取得しkey_radio_toggleを呼出'''
        key_radio_toggle(
            key_radio_var.get(),
            own_key_spin,
            own_key_radio1,
            own_key_radio2,
            stream_key_spin,
            stream_key_radio1,
            stream_key_radio2
        )

    own_key_frame = Frame(root)
    own_key_frame.pack(anchor=W)
    Radiobutton(
        own_key_frame,
        command=toggles,
        text=SETTINGS['own_key_label'],
        value=False,
        variable=key_radio_var
    ).pack(side=LEFT)
    own_key_var = IntVar(int(SETTINGS['own_key_default']))
    own_key_spin = Spinbox(
        own_key_frame,
        textvariable=own_key_var,
        format='%+0.0f',
        from_=-12,
        to=12,
        width=4,
        wrap=True
    )
    own_key_radio1 = Radiobutton(own_key_frame, variable=own_key_var)
    own_key_radio2 = Radiobutton(own_key_frame, variable=own_key_var)
    Button(
        own_key_frame,
        text=SETTINGS['preview_button'],
        command=lambda: preview_action(
            select[0] if (select := file_list.curselection()) else 0,
            own_key_var.get(),
            own_device_var.get(),
            play_button,
            pause_button,
            stop_button
        )
    ).pack(side=RIGHT)

    stream_key_frame = Frame(root)
    stream_key_frame.pack(anchor=W)
    Radiobutton(
        stream_key_frame,
        command=toggles,
        text=SETTINGS['stream_key_label'],
        value=True,
        variable=key_radio_var
    ).pack(side=LEFT)
    stream_key_var = IntVar(int(SETTINGS['stream_key_default']))
    stream_key_spin = Spinbox(
        stream_key_frame,
        textvariable=stream_key_var,
        format='%+0.0f',
        from_=-12,
        to=12,
        width=4,
        wrap=True
    )
    stream_key_radio1 = Radiobutton(stream_key_frame, variable=stream_key_var)
    stream_key_radio2 = Radiobutton(stream_key_frame, variable=stream_key_var)
    Button(
        stream_key_frame,
        text=SETTINGS['preview_button'],
        command=lambda: preview_action(
            select[0] if (select := file_list.curselection()) else 0,
            stream_key_var.get(),
            own_device_var.get(),
            play_button,
            pause_button,
            stop_button
        )
    ).pack(side=RIGHT)

    def updates(*unused: tuple[str, str, str]):
        '''現在の値を取得しupdate_keyfを呼出'''
        update_keyf(
            pitch_var.get(),
            # pitch_spin,
            own_key_var.get(),
            # own_key_spin,
            own_key_radio1,
            own_key_radio2,
            stream_key_var.get(),
            # stream_key_spin,
            stream_key_radio1,
            stream_key_radio2
        )

    pitch_var.trace_add('write', updates)
    own_key_var.trace_add('write', updates)
    stream_key_var.trace_add('write', updates)
    updates()
    toggles()

    Label(root, text=SETTINGS['own_device_label']).pack()
    own_device_var = StringVar(value=device_names[0])
    OptionMenu(root, own_device_var, *device_names).pack()

    Label(root, text=SETTINGS['stream_device_label']).pack()
    stream_device_var = StringVar(value=device_names[0])
    OptionMenu(root, stream_device_var, *device_names).pack()

    button_frame = Frame(root)
    button_frame.pack()
    play_button = Button(
        button_frame,
        text=SETTINGS['play_button'],
        command=lambda: play_action(
            select[0] if (select := file_list.curselection()) else 0,
            delay_var.get(),
            own_key_var.get(),
            stream_key_var.get(),
            own_device_var.get(),
            stream_device_var.get(),
            play_button,
            pause_button,
            stop_button
        )
    )
    play_button.pack(side=LEFT)
    pause_button = Button(
        button_frame,
        text=SETTINGS['pause_button'],
        command=lambda: pause_toggle(stop_button),
        state=DISABLED
    )
    pause_button.pack(side=LEFT)
    stop_button = Button(
        button_frame,
        text=SETTINGS['stop_button'],
        command=stop_audio,
        state=DISABLED
    )
    stop_button.pack(side=LEFT)

    root.mainloop()


if __name__ == '__main__':
    main()
