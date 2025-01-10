import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports

def refresh_ports():
    """Refresh the list of active USB ports."""
    ports = serial.tools.list_ports.comports()
    port_options.set("")  # Clear the selected option
    dropdown_menu['menu'].delete(0, 'end')  # Clear the dropdown menu
    for port in ports:
        dropdown_menu['menu'].add_command(label=f"{port.device} - {port.description}",
    command=tk._setit(port_options, f"{port.device} - {port.description}"))

def show_selected_port():
    """Display the selected port."""
    selected_port.set(f"Selected: {port_options.get()}")

# Create the main application window
root = tk.Tk()
root.title("Active USB Ports")

# Set the window size
root.geometry("400x300")

# Create a label
label = tk.Label(root, text="Active USB Ports:", font=("Arial", 14))
label.pack(pady=10)

# Dropdown menu for selecting ports
port_options = tk.StringVar()
port_options.set("")
dropdown_menu = ttk.OptionMenu(root, port_options, "")
dropdown_menu.pack(pady=10)

# Create a button to refresh ports
refresh_button = ttk.Button(root, text="Refresh", command=refresh_ports)
refresh_button.pack(pady=10)

# Display the selected port
selected_port = tk.StringVar()
selected_port_label = tk.Label(root, textvariable=selected_port, font=("Arial", 12))
selected_port_label.pack(pady=10)

# Button to show the selected port
show_button = ttk.Button(root, text="Show Selected Port", command=show_selected_port)
show_button.pack(pady=10)

# Initial refresh to populate the dropdown
refresh_ports()

# Start the main event loop
root.mainloop()