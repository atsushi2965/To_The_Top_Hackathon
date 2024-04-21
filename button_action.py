import os

def play_action(delay_entry, pitch_var, own_key_var, stream_key_var, own_interface_var, stream_interface_var):
    print(f"Delay set to: {delay_entry.get()}")
    print(f"Pitch set to: {pitch_var.get()}")
    print(f"Own Key set to: {own_key_var.get()}")
    print(f"Stream Key set to: {stream_key_var.get()}")
    print(f"Own Output Interface: {own_interface_var.get()}")
    print(f"Stream Output Interface: {stream_interface_var.get()}")