import os
import pyaudio
import sounddevice as sd
import time
import pyaudio
import sounddevice as sd
import time

#音声処理
#音声処理
def play_action(delay_entry, pitch_var, own_key_var, stream_key_var, own_interface_var, stream_interface_var):
    print(f"Delay set to: {delay_entry.get()}")
    print(f"Pitch set to: {pitch_var.get()}")
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
