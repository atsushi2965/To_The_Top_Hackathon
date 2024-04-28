import librosa
from numpy import arange, round, sign
import os
# import pyaudio
import sounddevice as sd
import soundfile as sf
from threading import Event, Thread
# import time
from tkinter import END, LEFT, Label, Listbox, StringVar, Toplevel, filedialog


pause_event = Event()
pause_event.set()
stop_event = Event()
threads = []


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
    own_key2 = own_key1 - 12*sign(own_key1) if own_key1 != 0 else 12 * sign(pitch_var.get())
    stream_key1 = (own_key_var.get() + pitch_var.get()) % 12
    stream_key2 = stream_key1 - 12*sign(stream_key1) if stream_key1 != 0 else 12 * sign(pitch_var.get())
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

# GUI更新 (ﾎｽﾄ選択)
def sub(which: str, hosts):
    def on_select(evt):
        w = evt.widget
        index = int(w.curselection()[0])
        value = w.get(index)
        selected_host.set(value)
        top.destroy()

    top = Toplevel()
    top.title("Select Host")

    selected_host = StringVar(top)
    Label(top, text=f"Multiple devices found.\nSelect {which} host:").pack(padx=10, pady=10)
    lb = Listbox(top)
    lb.pack()

    for host in hosts:
        lb.insert(END, host)

    lb.bind('<<ListboxSelect>>', on_select)

    top.wait_window()

    return selected_host.get()

# GUI更新 (ﾎﾞﾀﾝ群制御)
def toggle_button_state(is_playing: bool, play_button, pause_button, stop_button):
    if is_playing:
        play_button.config(state='disabled')
        pause_button.config(state='normal')
        stop_button.config(state='normal')
    else:
        play_button.config(state='normal')
        pause_button.config(state='disabled')
        stop_button.config(state='disabled')

# デバイス検出
def find_host_id(device_name):
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    hosts = []
    for device in devices:
        if device_name in device['name']:
            hosts.append(hostapis[device['hostapi']]['name'])
    api_name = sub(device_name, hosts) if len(hosts) > 1 else hosts[0]
    for device in devices:
        if device_name in device['name'] and api_name in hostapis[device['hostapi']]['name']:
            return device['index']
    return None

# 音声処理 (波形ｷｰ変更)
def pitch_shift(audio_path, semitones):
    y, sr = librosa.load(audio_path, sr=None)
    y_shifted = librosa.effects.pitch_shift(y, sr, n_steps=semitones)
    return y_shifted, sr

# 再生部 (ぱうせ)
def pause_toggle(stop_button):
    if pause_event.is_set():
        pause_event.clear()
        stop_button.config(state='disabled')
    else:
        pause_event.set()
        stop_button.config(state='normal')

# 再生部 (停止)
def stop_audio(play_button, pause_button, stop_button):
    stop_event.set()
    for thread in threads:
        thread.join()
    stop_event.clear()
    toggle_button_state(False, play_button, pause_button, stop_button)
    threads.clear()

# 再生部 (中枢)
def play_audio(audio, fs, interface):
    channels = audio.shape[1] if audio.ndim > 1 else 1
    with sd.OutputStream(device=interface, samplerate=fs, channels=channels) as stream:
        for sample in audio:
            if stop_event.is_set():
                break
            pause_event.wait()
            stream.write(sample)

# 音声処理 (試聴)
def preview_action(key_var, own_interface_var, audio_path, play_button, pause_button, stop_button):
    print("preview pushed")
    print("preview shifting...", end=' ')
    y_shifted, sr = pitch_shift(audio_path, key_var.get())
    print("shifted")
    thread = Thread(target=play_audio, args=(y_shifted, sr, find_host_id(own_interface_var.get())))
    toggle_button_state(True, play_button, pause_button, stop_button)
    thread.start()
    threads.append(thread)
    print("preview action finished")

# 音声処理 (中枢)
def play_action(delay_entry, own_key_var, stream_key_var, own_interface_var, stream_interface_var, audio_path, play_button, pause_button, stop_button):
    print("play pushed")
    print("own shifting...", end=' ')
    own_shifted, own_sr = pitch_shift(audio_path, own_key_var.get())
    print("shifted")
    print("stream shifting...", end=' ')
    stream_shifted, stream_sr = pitch_shift(audio_path, stream_key_var.get())
    print("shifted")

    own_host_id = find_host_id(own_interface_var.get())
    stream_host_id = find_host_id(stream_interface_var.get())

    own_thread = Thread(target=play_audio, args=(own_shifted, own_sr, own_host_id))
    stream_thread = Thread(target=play_audio, args=(stream_shifted, stream_sr, stream_host_id))

    toggle_button_state(True, play_button, pause_button, stop_button)
    own_thread.start()
    sd.sleep(int(delay_entry.get()))
    stream_thread.start()

    # try:
    #     own_thread.join()
    #     stream_thread.join()
    # except Exception as e:
    #     print(f"{e}")

    '''
    print(f"Delay set to: {delay_entry.get()}")
    # print(f"Pitch set to: {pitch_var.get()}")
    print(f"Own Key set to: {own_key_var.get()}")
    print(f"Stream Key set to: {stream_key_var.get()}")
    print(f"Stream Output Interface: {stream_interface_var.get()}")

    #入出力インターフェース設定未
    #遅延処理未
    #OBS関連チェック未

    # ストリーム設定
    chunk = 1024  # フレームあたりのサンプル数
    format = pyaudio.paInt16  # サンプルフォーマット
    channels = 1  # チャンネル数
    rate = 44100  # サンプリングレート (Hz)

    # PyAudioオブジェクトの作成
    audio = pyaudio.PyAudio()

    # マイクストリームの開始
    stream_in = audio.open(input=True,
                     format=format,
                     channels=channels,
                     rate=rate,
                     frames_per_buffer=chunk)

    # スピーカーストリームの開始
    stream_out = audio.open(output=True,
                      format=format,
                      channels=channels,
                      rate=rate,
                      frames_per_buffer=chunk)

    try:
        while True:
            # マイクからデータを読み込む
            data = stream_in.read(chunk)

            # スピーカーに出力
            stream_out.write(data)
    except KeyboardInterrupt:
        # 終了処理
        stream_in.stop_stream()
        stream_out.stop_stream()
        stream_in.close()
        stream_out.close()
        audio.terminate()
    '''

    threads.extend([own_thread, stream_thread])
    print("play action finished")
