#!/usr/bin/env python3
"""
Flipper SubGHz Signal File Organizer V2.0
A modern, user-friendly tool for organizing Flipper Zero .sub files
by frequency and protocol.
"""

import os
import re
import shutil
import threading
from pathlib import Path
from typing import Callable

try:
    import customtkinter as ctk
    from CTkToolTip import CTkToolTip
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(["pip", "install", "customtkinter", "CTkToolTip", "--break-system-packages"])
    import customtkinter as ctk
    from CTkToolTip import CTkToolTip

from tkinter import filedialog, messagebox


# ============================================================================
# Configuration
# ============================================================================

class AppConfig:
    """Application configuration and constants."""
    APP_NAME = "Flipper SubGHz Organizer"
    VERSION = "2.0"
    WINDOW_SIZE = (700, 750)
    
    PROTOCOLS = (
        "Alutech AT-4N", "BETT", "CAME", "CAME Atomo", "CAME TWEE",
        "Faac SLH", "GangQi", "GateTX", "Hollarm", "Honeywell",
        "KeeLoq", "Linear", "Marantec24", "Mastercode", "Nice FLO",
        "Nice FloR-S", "Princeton", "RAW", "Security+ 1.0",
        "Security+ 2.0", "SMC5326", "Somfy Keytis", "Somfy Telis"
    )
    
    FREQUENCIES = {
        "300000000": "300.00 MHz",
        "310000000": "310.00 MHz",
        "315000000": "315.00 MHz",
        "390000000": "390.00 MHz",
        "418000000": "418.00 MHz",
        "433420000": "433.42 MHz",
        "433920000": "433.92 MHz",
        "434420000": "434.42 MHz",
        "868350000": "868.35 MHz",
        "868800000": "868.80 MHz",
        "915000000": "915.00 MHz",
    }


# ============================================================================
# File Processing Logic
# ============================================================================

class SubGhzFileProcessor:
    """Handles scanning and organizing .sub files."""
    
    def __init__(self, progress_callback: Callable = None, status_callback: Callable = None):
        self.progress_callback = progress_callback or (lambda *args: None)
        self.status_callback = status_callback or (lambda *args: None)
        self._cancelled = False
    
    def cancel(self):
        """Cancel the current operation."""
        self._cancelled = True
    
    def _file_matches(self, file_path: Path, frequency: str, protocol: str) -> bool:
        """Check if a file matches the given frequency and protocol."""
        try:
            content = file_path.read_text(encoding='utf-8')
            freq_pattern = rf"^\s*Frequency:\s*{re.escape(frequency)}\s*$"
            proto_pattern = rf"^\s*Protocol:\s*{re.escape(protocol)}\s*$"
            
            return (re.search(freq_pattern, content, re.MULTILINE) is not None and
                    re.search(proto_pattern, content, re.MULTILINE) is not None)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return False
    
    def scan_files(self, input_folder: Path, frequencies: list, protocols: list) -> list:
        """Scan for matching .sub files and return list of (file, freq, proto) tuples."""
        matches = []
        self.status_callback("Scanning files...")
        
        all_files = list(input_folder.rglob("*.sub"))
        total = len(all_files)
        
        for i, file_path in enumerate(all_files):
            if self._cancelled:
                return []
            
            for freq in frequencies:
                for proto in protocols:
                    if self._file_matches(file_path, freq, proto):
                        matches.append((file_path, freq, proto))
            
            if i % 10 == 0:  # Update progress every 10 files
                self.progress_callback(i, total, "Scanning")
        
        return matches
    
    def organize_files(self, input_folder: Path, output_folder: Path,
                       frequencies: list, protocols: list,
                       create_log: bool = False) -> tuple:
        """
        Organize .sub files into protocol/frequency folder structure.
        Returns (processed_count, log_entries).
        """
        self._cancelled = False
        matches = self.scan_files(input_folder, frequencies, protocols)
        
        if not matches or self._cancelled:
            return 0, []
        
        total = len(matches)
        log_entries = []
        processed = 0
        
        self.status_callback("Organizing files...")
        
        for file_path, freq, proto in matches:
            if self._cancelled:
                break
            
            # Create destination path
            freq_label = f"{int(freq) / 1_000_000:.2f} MHz"
            relative_path = file_path.parent.relative_to(input_folder)
            dest_folder = output_folder / proto / freq_label / relative_path
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            dest_file = dest_folder / file_path.name
            shutil.copy2(file_path, dest_file)
            
            log_entries.append(f"{file_path} -> {dest_file}")
            processed += 1
            self.progress_callback(processed, total, "Organizing")
        
        # Clean up empty directories
        self._remove_empty_dirs(output_folder)
        
        # Write log if requested
        if create_log and log_entries:
            log_path = output_folder / "sort_log.txt"
            log_path.write_text("Copied files:\n" + "\n".join(log_entries), encoding='utf-8')
        
        self.status_callback("Complete!" if not self._cancelled else "Cancelled")
        return processed, log_entries
    
    def _remove_empty_dirs(self, folder: Path):
        """Remove empty directories recursively."""
        for dir_path in sorted(folder.rglob("*"), reverse=True):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                dir_path.rmdir()


# ============================================================================
# Modern GUI
# ============================================================================

class CheckboxGroup(ctk.CTkScrollableFrame):
    """A scrollable frame containing checkboxes with select all/none controls."""
    
    def __init__(self, master, title: str, items: list, columns: int = 3, **kwargs):
        super().__init__(master, **kwargs)
        
        self.checkboxes = {}
        self.items = items
        
        # Header with title and controls
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="All", width=50, height=24,
                      command=self.select_all).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="None", width=50, height=24,
                      command=self.select_none).pack(side="left", padx=2)
        
        # Checkbox grid
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        
        for i, item in enumerate(items):
            var = ctk.BooleanVar(value=False)
            display_text = item if isinstance(item, str) else item[1]
            key = item if isinstance(item, str) else item[0]
            
            cb = ctk.CTkCheckBox(grid_frame, text=display_text, variable=var,
                                 font=ctk.CTkFont(size=12))
            cb.grid(row=i // columns, column=i % columns, sticky="w", padx=10, pady=4)
            self.checkboxes[key] = var
    
    def select_all(self):
        for var in self.checkboxes.values():
            var.set(True)
    
    def select_none(self):
        for var in self.checkboxes.values():
            var.set(False)
    
    def get_selected(self) -> list:
        return [key for key, var in self.checkboxes.items() if var.get()]


class FlipperOrganizerApp(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.config = AppConfig()
        self.processor = None
        self._setup_window()
        self._create_widgets()
    
    def _setup_window(self):
        """Configure the main window."""
        self.title(f"{self.config.APP_NAME} v{self.config.VERSION}")
        self.geometry(f"{self.config.WINDOW_SIZE[0]}x{self.config.WINDOW_SIZE[1]}")
        self.minsize(600, 600)
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)
    
    def _create_widgets(self):
        """Create all GUI widgets."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        title_label = ctk.CTkLabel(
            header,
            text=f"🐬 {self.config.APP_NAME}",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        version_label = ctk.CTkLabel(
            header,
            text=f"v{self.config.VERSION}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        version_label.pack(side="left", padx=10, pady=(8, 0))
        
        # Folder selection
        folder_frame = ctk.CTkFrame(self)
        folder_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        folder_frame.grid_columnconfigure(1, weight=1)
        
        # Input folder
        ctk.CTkLabel(folder_frame, text="📁 Input Folder:",
                     font=ctk.CTkFont(size=13)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.input_entry = ctk.CTkEntry(folder_frame, placeholder_text="Select folder containing .sub files...")
        self.input_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        input_btn = ctk.CTkButton(folder_frame, text="Browse", width=80,
                                   command=self._select_input_folder)
        input_btn.grid(row=0, column=2, padx=10, pady=10)
        CTkToolTip(input_btn, "Select the folder containing your .sub files")
        
        # Output folder
        ctk.CTkLabel(folder_frame, text="📂 Output Folder:",
                     font=ctk.CTkFont(size=13)).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.output_entry = ctk.CTkEntry(folder_frame, placeholder_text="Select destination folder...")
        self.output_entry.grid(row=1, column=1, padx=5, pady=10, sticky="ew")
        
        output_btn = ctk.CTkButton(folder_frame, text="Browse", width=80,
                                    command=self._select_output_folder)
        output_btn.grid(row=1, column=2, padx=10, pady=10)
        CTkToolTip(output_btn, "Select where organized files will be saved")
        
        # Info label
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=2, column=0, padx=20, pady=(5, 10), sticky="ew")
        
        ctk.CTkLabel(
            info_frame,
            text="Select the frequencies and protocols you want to filter:",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w")
        
        # Frequencies
        freq_items = [(k, v) for k, v in self.config.FREQUENCIES.items()]
        self.freq_group = CheckboxGroup(
            self, title="📡 Frequencies", items=freq_items,
            columns=5, height=120
        )
        self.freq_group.grid(row=3, column=0, padx=20, pady=5, sticky="nsew")
        
        # Protocols
        self.proto_group = CheckboxGroup(
            self, title="🔐 Protocols", items=list(self.config.PROTOCOLS),
            columns=5, height=180
        )
        self.proto_group.grid(row=4, column=0, padx=20, pady=5, sticky="nsew")
        
        # Options and progress
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        
        # Options row
        options_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        options_frame.grid(row=0, column=0, sticky="ew", pady=(10, 5))
        
        self.log_var = ctk.BooleanVar(value=True)
        log_cb = ctk.CTkCheckBox(options_frame, text="📝 Create log file",
                                  variable=self.log_var)
        log_cb.pack(side="left", padx=10)
        CTkToolTip(log_cb, "Save a log of all copied files")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(bottom_frame)
        self.progress_bar.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.progress_bar.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            bottom_frame, text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=2, column=0, pady=(0, 10))
        
        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=6, column=0, padx=20, pady=(5, 20), sticky="ew")
        
        self.start_btn = ctk.CTkButton(
            btn_frame, text="🚀 Start Organizing", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_sorting
        )
        self.start_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.cancel_btn = ctk.CTkButton(
            btn_frame, text="❌ Cancel", height=40,
            font=ctk.CTkFont(size=14),
            fg_color="#8B0000", hover_color="#A52A2A",
            command=self._cancel_sorting, state="disabled"
        )
        self.cancel_btn.pack(side="right", padx=(5, 0))
    
    def _select_input_folder(self):
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, folder)
    
    def _select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, folder)
    
    def _update_progress(self, current: int, total: int, stage: str):
        """Update the progress bar and status label."""
        if total > 0:
            progress = current / total
            self.progress_bar.set(progress)
            self.status_label.configure(text=f"{stage}: {current}/{total} files ({progress*100:.1f}%)")
    
    def _update_status(self, message: str):
        """Update the status label."""
        self.status_label.configure(text=message)
    
    def _set_ui_state(self, processing: bool):
        """Enable/disable UI elements based on processing state."""
        state = "disabled" if processing else "normal"
        self.start_btn.configure(state=state)
        self.cancel_btn.configure(state="normal" if processing else "disabled")
    
    def _start_sorting(self):
        """Start the sorting process in a background thread."""
        input_folder = self.input_entry.get().strip()
        output_folder = self.output_entry.get().strip()
        
        if not input_folder or not output_folder:
            messagebox.showerror("Error", "Please select both input and output folders.")
            return
        
        if not os.path.isdir(input_folder):
            messagebox.showerror("Error", "Input folder does not exist.")
            return
        
        frequencies = self.freq_group.get_selected()
        protocols = self.proto_group.get_selected()
        
        if not frequencies:
            messagebox.showerror("Error", "Please select at least one frequency.")
            return
        
        if not protocols:
            messagebox.showerror("Error", "Please select at least one protocol.")
            return
        
        # Create output folder if needed
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        
        # Reset progress
        self.progress_bar.set(0)
        self._set_ui_state(True)
        
        # Create processor and start thread
        self.processor = SubGhzFileProcessor(
            progress_callback=lambda c, t, s: self.after(0, self._update_progress, c, t, s),
            status_callback=lambda m: self.after(0, self._update_status, m)
        )
        
        def run_sorting():
            try:
                processed, _ = self.processor.organize_files(
                    Path(input_folder),
                    Path(output_folder),
                    frequencies,
                    protocols,
                    create_log=self.log_var.get()
                )
                
                self.after(0, self._sorting_complete, processed)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
                self.after(0, lambda: self._set_ui_state(False))
        
        thread = threading.Thread(target=run_sorting, daemon=True)
        thread.start()
    
    def _cancel_sorting(self):
        """Cancel the current sorting operation."""
        if self.processor:
            self.processor.cancel()
            self._update_status("Cancelling...")
    
    def _sorting_complete(self, processed: int):
        """Handle sorting completion."""
        self._set_ui_state(False)
        self.progress_bar.set(1)
        
        if processed > 0:
            log_msg = " Log file saved." if self.log_var.get() else ""
            messagebox.showinfo(
                "Complete",
                f"Successfully organized {processed} file(s).{log_msg}"
            )
        else:
            messagebox.showinfo(
                "No Files Found",
                "No matching .sub files were found with the selected filters."
            )


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    app = FlipperOrganizerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
