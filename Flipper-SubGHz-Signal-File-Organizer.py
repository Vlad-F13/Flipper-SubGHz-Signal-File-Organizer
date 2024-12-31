import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
import re

# Function to check if a file contains the specified text
def contains_text(file_path, texts):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            frequencies = [text for text in texts if text.startswith("Frequency:")]
            protocols = [text for text in texts if text.startswith("Protocol:")]

            # Ensure frequencies are checked first
            return any(re.search(rf"^\s*{re.escape(freq)}\s*$", content, re.MULTILINE) for freq in frequencies) and \
                   any(re.search(rf"^\s*{re.escape(proto)}\s*$", content, re.MULTILINE) for proto in protocols)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False

def scan_files(input_folder, selected_frequencies, selected_protocols):
    total_files = 0
    for root_dir, dirs, files in os.walk(input_folder):
        for file in files:
            file_path = os.path.join(root_dir, file)
            if file.endswith(".sub") and any(contains_text(file_path, [f"Frequency: {frequency}", f"Protocol: {protocol}"]) for frequency in selected_frequencies for protocol in selected_protocols):
                total_files += 1
    return total_files

def start_sorting():
    # Reset progress bar and labels
    progress_bar["value"] = 0
    progress_label_progress.config(text="")
    progress_label_status.config(text="                      ")

    input_folder = input_folder_var.get()
    output_folder = output_folder_var.get()

    selected_frequencies = [frequency for frequency, var in frequency_vars.items() if var.get()]
    selected_protocols = [protocol for protocol, var in protocol_vars.items() if var.get()]

    if not input_folder or not output_folder:
        messagebox.showerror("Error", "Please select input and output folders.")
        return

    if not selected_frequencies or not selected_protocols:
        messagebox.showerror("Error", "Please select at least one frequency and one protocol to filter.")
        return

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Scan files to determine total count
    progress_label_status.config(text="Scanning files...")
    root.update_idletasks()
    total_files = scan_files(input_folder, selected_frequencies, selected_protocols)
    progress_label_status.config(text="                      ")  # Clear scanning label
    progress_bar["maximum"] = total_files

    if total_files == 0:
        progress_label_progress.config(text="                      ")  # Clear previous progress text
        progress_label_status.config(text="No files to process.")
        return

    found_files = []
    processed = 0

    for protocol in selected_protocols:
        protocol_folder = os.path.join(output_folder, protocol)

        for frequency in selected_frequencies:
            formatted_frequency = format_frequency(frequency)
            frequency_folder = os.path.join(protocol_folder, f"{formatted_frequency} MHz")

            for root_dir, dirs, files in os.walk(input_folder):
                relative_root = os.path.relpath(root_dir, input_folder)
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    if file.endswith(".sub") and contains_text(file_path, [f"Frequency: {frequency}", f"Protocol: {protocol}"]):
                        if not os.path.exists(protocol_folder):
                            os.makedirs(protocol_folder)
                        if not os.path.exists(frequency_folder):
                            os.makedirs(frequency_folder)

                        destination_folder = os.path.join(frequency_folder, relative_root)
                        if not os.path.exists(destination_folder):
                            os.makedirs(destination_folder)

                        destination_file = os.path.join(destination_folder, file)
                        shutil.copy2(file_path, destination_file)
                        found_files.append(f"{file_path} -> {destination_file}")

                        processed += 1
                        progress_bar["value"] = processed
                        progress_label_progress.config(text=f"Files processed: {processed}/{total_files}")
                        root.update_idletasks()

    # Remove empty folders
    for root_dir, dirs, _ in os.walk(output_folder, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root_dir, dir)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)

    progress_bar["value"] = total_files
    progress_label_progress.config(text=f"Files processed: {processed}/{total_files}")
    progress_label_status.config(text="Sorting complete.")

    # Write log file if enabled
    if log_var.get():
        with open(os.path.join(output_folder, "sort_log.txt"), "w", encoding="utf-8") as log:
            log.write("Copied files:\n")
            log.write("\n".join(found_files))

    messagebox.showinfo("Finished", "Sorting completed." + (" Log saved in the output folder." if log_var.get() else ""))

def select_input_folder():
    folder = filedialog.askdirectory(title="Select Input Folder")
    if folder:
        input_folder_var.set(folder)

def select_output_folder():
    folder = filedialog.askdirectory(title="Select Output Folder")
    if folder:
        output_folder_var.set(folder)

def format_frequency(frequency):
    return f"{int(frequency) / 1_000_000:.2f} Mhz"

# GUI
root = tk.Tk()
root.title("Flipper SubGHz Signal File Organizer - V1.0")
root.geometry("560x620")

input_folder_var = tk.StringVar()
output_folder_var = tk.StringVar()
log_var = tk.BooleanVar(value=False)

protocols = [
    "Alutech AT-4N", "BETT", "CAME", "CAME Atomo", "CAME TWEE", "Faac SLH",
    "GangQi", "GateTX", "Hollarm", "KeeLoq", "Linear", "Marantec24",
    "Nice FLO", "Nice FloR-S", "Princeton", "RAW", "Security+ 1.0", "Security+ 2.0", "Somfy Telis"
]

frequencies = [
    "300000000", "310000000", "315000000", "390000000", "433420000",
    "433920000", "434420000", "868350000", "868800000"
]

protocol_vars = {protocol: tk.BooleanVar() for protocol in protocols}
frequency_vars = {frequency: tk.BooleanVar() for frequency in frequencies}

# GUI Elements
tk.Label(root, text="Input Folder:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
tk.Entry(root, textvariable=input_folder_var, width=60).grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=select_input_folder).grid(row=0, column=2, padx=5, pady=5)

tk.Label(root, text="Output Folder:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
tk.Entry(root, textvariable=output_folder_var, width=60).grid(row=1, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=select_output_folder).grid(row=1, column=2, padx=5, pady=5)

tk.Label(root, text="1. Filter Frequencies:").grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")

frequency_frame = tk.Frame(root)
frequency_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

for i, frequency in enumerate(frequencies):
    formatted_frequency = format_frequency(frequency)
    tk.Checkbutton(frequency_frame, text=formatted_frequency, variable=frequency_vars[frequency]).grid(row=i // 3, column=i % 3, sticky="w", padx=5, pady=2)

tk.Label(root, text="2. Filter Protocols:").grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="w")

protocol_frame = tk.Frame(root)
protocol_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5)

for i, protocol in enumerate(protocols):
    tk.Checkbutton(protocol_frame, text=protocol, variable=protocol_vars[protocol]).grid(row=i // 3, column=i % 3, sticky="w", padx=5, pady=2)

progress_bar = Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.grid(row=6, column=0, columnspan=3, pady=10)

tk.Checkbutton(root, text="Enable Log", variable=log_var).grid(row=7, column=0, columnspan=3, pady=5)

progress_label_progress = tk.Label(root, text="")
progress_label_progress.grid(row=8, column=0, columnspan=3)

progress_label_status = tk.Label(root, text="")
progress_label_status.grid(row=9, column=0, columnspan=3)

tk.Button(root, text="Start Sorting", command=start_sorting).grid(row=10, column=0, columnspan=3, pady=10)

root.mainloop()
