from json import JSONDecodeError, dump, load
from os.path import abspath, dirname, join


def load_settings(filename):
    """言語設定読込"""
    filepath = join(dirname(abspath(__file__)), filename)
    print(filepath)
    defaults = {
        "title": "Accompaniment Settings",
        "delay_label": "Voice changer delay [ms]:",
        "delay_entry_default": "0",
        "pitch_label": "Voice changer pitch:",
        "pitch_default": "0",
        "own_key_label": "Own music key:",
        "own_key_default": "0",
        "stream_key_label": "Stream music key:",
        "stream_key_default": "0",
        "own_interface_label": "Own output interface:",
        "stream_interface_label": "Stream output interface:",
        "play_button": "Play",
        "pause_button": "Pause",
        "stop_button": "Stop",
        "preview_button": "Preview",
        "file_label": "Select an audio source:",
        "file_add": "Add files",
        "title_sub": "Select Host"
    }

    try:
        # 設定ファイル読込
        with open(filepath) as file:
            settings: dict[str, str] = load(file)
        # デフォルトで不足キー補填
        for key, value in defaults.items():
            settings.setdefault(key, value)

        return settings
    except (FileNotFoundError, JSONDecodeError) as e:
        print(f'Error loading settings, using defaults: {e}')
        with open(filepath, 'w') as file:
            dump(defaults, file, indent='\t')
        return defaults


settings = load_settings('settings.json')
