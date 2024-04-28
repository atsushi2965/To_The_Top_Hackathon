import librosa
from numpy import arange, round, sign
import os
# import pyaudio
import sounddevice as sd
import soundfile as sf
from threading import Thread
import time
from tkinter import END, LEFT, filedialog


# GUI更新 (ラジオボタンに依る構成の変更)
def key_radio_toggle(key_radio, own_key_menu, own_key_radio2, own_key_radio1, stream_key_menu, stream_key_radio2, stream_key_radio1):
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

# GUI更新 (ｷｰ変更に依るテキストの変更)
def update_radio_buttons(stream_key_var, pitch_var, own_key_var, own_key_radio1, own_key_radio2, stream_key_radio1, stream_key_radio2):
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

# GUI更新 (ﾊﾟｽ追加)
def add_file(file_list):
    file_path = filedialog.askopenfilename(filetypes=[("libsndfile対応フォーマット", '*.wav;*.aiff;*.au;*.raw;*.paf;*.8svx;*.nist;*.sf;*.voc;*.w64;*.pvf;*.xi;*.caf;*.sd2;*.flac;*.ogg')])
    if file_path:
        file_list.insert(END, file_path)


# 音声処理 (波形ｷｰ変更)
def pitch_shift(audio_path, semitones):
    y, sr = librosa.load(audio_path, sr=None)
    y_shifted = librosa.effects.pitch_shift(y, sr, n_steps=semitones)
    print("shifted")
    return y_shifted, sr

# 音声処理 (再生部)
def play_audio(audio, fs, interface):
    def play():
        sd.default.device = interface
        sd.play(audio, fs)
        sd.wait()
    thread = Thread(target=play)
    thread.start()
    return thread

# 音声処理 (試聴)
def preview_action(key_var, own_interface_var, audio_path):
    data, fs = sf.read(audio_path)
    key_data = change_key(data, key_var.get())
    play_audio(key_data, fs, own_interface_var.get())

# デバイス検出
def find_device_id(device_name, api_name):
    devices = sd.query_devices()
    for device in devices:
        if device_name in device['name'] and api_name in device['hostapi']:
            return device['index']
    return None

#音声処理
def play_action(delay_entry, own_key_var, stream_key_var, own_interface_var, stream_interface_var, audio_path):
    print(f"Delay set to: {delay_entry.get()}")
    # print(f"Pitch set to: {pitch_var.get()}")
    print(f"Own Key set to: {own_key_var.get()}")
    print(f"Stream Key set to: {stream_key_var.get()}")
    print(f"Stream Output Interface: {stream_interface_var.get()}")

    own_shifted, own_sr = pitch_shift(audio_path, own_key_var.get())
    stream_shifted, stream_sr = pitch_shift(audio_path, stream_key_var.get())

    own_device_id = find_device_id(own_interface_var.get(), 'Windows DirectSound')
    stream_device_id = find_device_id(stream_interface_var.get(), 'Windows DirectSound')

    try:
        own_thread = play_audio(own_shifted, own_sr, own_device_id)
        time.sleep(int(delay_entry.get()) / 1000)
        stream_thread = play_audio(stream_shifted, stream_sr, stream_device_id)

        # own_thread.join()
        # stream_thread.join()
    except Exception as e:
        print(f"{e}")

    print("終了しました。")
