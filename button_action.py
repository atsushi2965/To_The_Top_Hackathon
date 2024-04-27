from numpy import sign
import os
import pyaudio
import sounddevice as sd
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


# 音声処理 (試聴)
def preview_action(key_var, own_interface_var, audio_path):
    print("test")

#音声処理
def play_action(delay_entry, own_key_var, stream_key_var, own_interface_var, stream_interface_var, audio_path):
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

    print("終了しました。")
