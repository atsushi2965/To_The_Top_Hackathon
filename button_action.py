from collections import defaultdict
# from functools import cache
import librosa
from numpy import ascontiguousarray, ndarray, newaxis
from pathlib import Path
# import pyaudio
from sounddevice import OutputStream, query_devices, query_hostapis, sleep
from soundfile import available_formats
from threading import Event, Thread
from tkinter import DISABLED, END, LEFT, NORMAL, Button, Event as tkEvent, Label, Listbox, Radiobutton, Spinbox, Toplevel
from tkinter.filedialog import askopenfilename
from typing import Union
from weakref import WeakSet

from librosa_tqdm import RESOLUTION, tqrs  # tqdming librosa here
from settings import SETTINGS


DEVICES: defaultdict[str, dict[int, tuple[int, float]]] = defaultdict(dict)
for device in query_devices():
    if device['max_output_channels'] > 0:
        DEVICES[device['name']][device['hostapi']] = (
            device['index'],
            device['default_high_output_latency']
        )
HOSTAPIS = [api['name'] for api in query_hostapis()]

filepaths: list[str] = []
pause_event = Event()
pause_event.set()
stop_event = Event()
threads: WeakSet[Thread] = WeakSet()
RES_TYPE = 'sinc_best'
INT_RESOLUTION = round(1000*RESOLUTION)


def key_radio_toggle(
        key_radio: bool,
        own_key_spin: Spinbox,
        own_key_radio1: Radiobutton,
        own_key_radio2: Radiobutton,
        stream_key_spin: Spinbox,
        stream_key_radio1: Radiobutton,
        stream_key_radio2: Radiobutton
):
    '''GUI更新 (ﾗｼﾞｵﾎﾞﾀﾝによる構成の変更)'''
    # !key_radio: own -> spin, stream -> radio
    widgets2forget = stream_key_spin, own_key_radio2, own_key_radio1  # less on left
    widgets2pack = own_key_spin, stream_key_radio2, stream_key_radio1  # less on left
    if key_radio:  # stream -> spin, own -> radio
        widgets2forget, widgets2pack = widgets2pack, widgets2forget

    for widget in widgets2forget:
        widget.pack_forget()
    for widget in widgets2pack:
        widget.pack(side=LEFT)


def sign(val: int):
    '''Returns the sign of a number.'''
    return (val > 0) - (val < 0)


# @cache
# def keyf(val: int):
#     '''ｷｰ ﾌｫｰﾏｯﾄ'''
#     return '±0' if val == 0 else f'{val:+}'


# def update_spinbox(spinbox: Spinbox, val: int):
#     '''GUI更新 (ｷｰ変更によるｽﾋﾟﾝﾎﾞｯｸｽの変更)'''
#     valf = keyf(val)
#     if spinbox.get() != valf:
#         spinbox.delete(0, END)
#         spinbox.insert(0, valf)


def update_keyf(
        pitch: int,
        # pitch_spin: Spinbox,
        own_key: int,
        # own_key_spin: Spinbox,
        own_key_radio1: Radiobutton,
        own_key_radio2: Radiobutton,
        stream_key: int,
        # stream_key_spin: Spinbox,
        stream_key_radio1: Radiobutton,
        stream_key_radio2: Radiobutton
):
    '''GUI更新 (ｷｰ変更によるﾃｷｽﾄの変更)'''
    sign_pitch = sign(pitch)
    own_key1 = (stream_key - pitch)%12
    own_key2 = 12*sign_pitch if own_key1 == 0 else own_key1 - 12*sign(own_key1)
    stream_key1 = (own_key + pitch)%12
    stream_key2 = 12*sign_pitch if stream_key1 == 0 else stream_key1 - 12*sign(stream_key1)

    # update_spinbox(pitch_spin, pitch)
    # update_spinbox(own_key_spin, own_key)
    own_key_radio1.config(text=f'{own_key1:+}', val=own_key1)
    own_key_radio2.config(text=f'{own_key2:+}', val=own_key2)
    # update_spinbox(stream_key_spin, stream_key)
    stream_key_radio1.config(text=f'{stream_key1:+}', val=stream_key1)
    stream_key_radio2.config(text=f'{stream_key2:+}', val=stream_key2)


def add_file(file_list: Listbox):
    '''GUI更新 (ﾊﾟｽ追加)'''
    filepath = askopenfilename(
        filetypes=(
            ('soundfile' + SETTINGS['file_format'], ['.' + ext.lower() for ext in available_formats()]),
            (SETTINGS['file_all'], '*')
        ),
        title=SETTINGS['file_add']
    )
    if filepath:
        file_list.insert(END, Path(filepath).name)
        filepaths.append(filepath)


def sub(device_name: str):
    '''GUI更新 (ﾎｽﾄ選択)'''
    device_list = list(DEVICES[device_name])

    if len(device_list) <= 1:
        return DEVICES[device_name][device_list[0]]

    top = Toplevel()
    top.title(SETTINGS['sub_title'])
    Label(top, text=SETTINGS['sub_label'].format(device_name)).pack(padx=10, pady=10)
    api_list = Listbox(top)
    api_list.pack()

    api_list.insert(END, *(HOSTAPIS[api] for api in device_list))

    def on_select(evt: tkEvent):
        '''選択時処理'''
        w: Listbox = evt.widget
        top.api_idx = w.curselection()[0]
        top.destroy()

    api_list.bind('<<ListboxSelect>>', on_select)
    top.wait_window()

    return DEVICES[device_name][device_list[top.api_idx]]


def toggle_buttons(playing: bool, play_button: Button, pause_button: Button, stop_button: Button):
    '''GUI更新 (ﾎﾞﾀﾝ群制御)'''
    play_state, pause_stop_state = (DISABLED, NORMAL) if playing else (NORMAL, DISABLED)

    play_button.config(state=play_state)
    for button in pause_button, stop_button:
        button.config(state=pause_stop_state)


def audio_load(audio_idx: int):
    '''音声読込'''
    return librosa.load(filepaths[audio_idx], sr=None, mono=False, res_type=RES_TYPE)


def pitch_shift(y: ndarray, sr: int, semitones: int):
    '''音声処理 (波形ｷｰ変更)'''
    return librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones, res_type=RES_TYPE) if semitones else y


def pause_toggle(stop_button: Button):
    '''再生部 (ﾊﾟｳｾ)'''
    if pause_event.is_set():
        pause_event.clear()
        stop_button.config(state=DISABLED)
    else:
        pause_event.set()
        stop_button.config(state=NORMAL)


def stop_audio():
    '''再生部 (停止)'''
    stop_event.set()
    for thread in threads:
        thread.join()
    stop_event.clear()


def play_ready(sr: Union[int, float], device: int, audioT: ndarray):
    '''再生準備'''
    return OutputStream(
        samplerate=sr,
        device=device,
        channels=1 if audioT.ndim == 1 else audioT.shape[1]
    ), audioT if audioT.flags.c_contiguous else ascontiguousarray(audioT)


def play_audio(stream: OutputStream, audio: ndarray):
    '''再生部 (中枢) + 進捗表示 (`tqdm`)'''
    with stream:
        if audio.ndim == 1:
            for sample in tqrs(
                audio,
                'mono',
                leave=False,
                mininterval=RESOLUTION,
                unit='point',
                sr=stream.samplerate
            ):
                if stop_event.is_set():
                    break
                pause_event.wait()
                stream.write(sample)
        else:
            for sample in tqrs(
                audio,
                'ster',
                leave=False,
                mininterval=RESOLUTION,
                unit='point',
                sr=stream.samplerate
            ):
                if stop_event.is_set():
                    break
                pause_event.wait()
                stream.write(sample[newaxis, :])


def monitor_threads(play_button: Button, pause_button: Button, stop_button: Button):
    '''終了監視 (ﾎﾞﾀﾝﾄｸﾞﾙ)'''
    while threads:
        sleep(INT_RESOLUTION)
    toggle_buttons(False, play_button, pause_button, stop_button)


def preview_action(
        audio_idx: int,
        key: int,
        own_device: str,
        play_button: Button,
        pause_button: Button,
        stop_button: Button
):
    '''音声処理 (試聴)'''
    y, sr = audio_load(audio_idx)
    thread = Thread(None, play_audio, 'Prvw', play_ready(
        sr,
        sub(own_device)[0],
        pitch_shift(y, sr, key).T
    ))

    thread.start()

    toggle_buttons(True, play_button, pause_button, stop_button)
    threads.add(thread)
    Thread(None, monitor_threads, 'Mntr', (play_button, pause_button, stop_button)).start()


def play_action(
        audio_idx: int,
        delay: int,
        own_key: int,
        stream_key: int,
        own_device: str,
        stream_device: str,
        play_button: Button,
        pause_button: Button,
        stop_button: Button
):
    '''音声処理 (中枢)'''
    y, sr = audio_load(audio_idx)
    own_device_id, own_latency = sub(own_device)
    stream_device_id, stream_latency = sub(stream_device)
    own_thread = Thread(None, play_audio, 'ownP', play_ready(
        sr,
        own_device_id,
        pitch_shift(y, sr, own_key).T
    ))
    stream_thread = Thread(None, play_audio, 'strP', play_ready(
        sr,
        stream_device_id,
        pitch_shift(y, sr, stream_key).T
    ))
    true_delay = round(delay - (own_latency + stream_latency)*1000)

    own_thread.start()
    sleep(true_delay)
    stream_thread.start()

    toggle_buttons(True, play_button, pause_button, stop_button)
    threads.update((own_thread, stream_thread))
    Thread(None, monitor_threads, 'Mntr', (play_button, pause_button, stop_button)).start()
