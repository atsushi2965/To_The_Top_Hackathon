import json
from pathlib import Path
from sys import argv


def load_settings(filename):
    '''言語設定読込'''
    filepath = Path(argv[0]).with_name(filename)
    defaults = {
        'title': 'Accompaniment Settings',
        'delay_label': 'Voice changer delay [ms]:',
        'delay_entry_default': '0',
        'pitch_label': 'Voice changer pitch:',
        'pitch_default': '0',
        'own_key_label': 'Own music key:',
        'own_key_default': '0',
        'stream_key_label': 'Stream music key:',
        'stream_key_default': '0',
        'own_device_label': 'Own output device:',
        'stream_device_label': 'Stream output device:',
        'play_button': 'Play',
        'pause_button': 'Pause',
        'stop_button': 'Stop',
        'preview_button': 'Preview',
        'file_label': 'Select an audio source:',
        'file_add': 'Add files',
        'file_format': ' formats',
        'file_all': 'All files',
        'sub_title': 'Select Host',
        'sub_label': "Multiple devices found.\nSelect {}'s host API:"
    }

    try:
        # 設定ファイル読込
        with open(filepath) as file:
            settings: dict[str, str] = json.load(file)
        # # デフォルトで不足キー補填
        # settings.update({k: v for k, v in defaults.items() if k not in settings})
        return settings
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print('Error loading settings, using defaults:', e)
        with open(filepath, 'w') as file:
            json.dump(defaults, file, ensure_ascii=False, indent='\t')
        return defaults


SETTINGS = load_settings('settings.json')
