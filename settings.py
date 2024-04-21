import os

def load_settings(filename):
    default_settings = {
        'title': 'Audio Settings',
        'delay_label': 'Voice changer delay (ms):',
        'delay_entry_default': '0',
        'pitch_label': 'Voice changer pitch:',
        'pitch_default': '±0',
        'own_key_label': 'Select own music key:',
        'own_key_default': '±0',
        'stream_key_label': 'Select stream music key:',
        'stream_key_default': '±0',
        'own_interface_label': 'Select own output interface:',
        'stream_interface_label': 'Select stream output interface:',
        'play_button': 'Play'
    }
    
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as file:
            for key, value in default_settings.items():
                file.write(f"{key}={value}\n")
        return default_settings

    settings = {}
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            key, value = line.strip().split('=', 1)
            settings[key] = value
    return settings
