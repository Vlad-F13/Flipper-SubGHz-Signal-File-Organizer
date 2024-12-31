# Flipper SubGHz File Sorter GUI

**Flipper SubGHz File Sorter GUI** is a user-friendly tool designed to organize and sort `.sub` files used with the Flipper Zero device. This tool allows you to filter files by frequency and protocol, creating a structured and efficient way to manage your SubGHz files.

## Features
- **Filter by Frequency and Protocol**: Select specific frequencies and protocols to process `.sub` files.
- **Automated Sorting**: Automatically creates organized directories based on selected frequencies and protocols.
- **Pre-Sorting Scan**: Scans files beforehand to ensure accurate progress tracking during sorting.
- **Optional Logging**: Generates a log file of all copied files and their destinations.
- **Simple GUI**: An intuitive graphical interface powered by Python and Tkinter.
- **Flipper Zero Compatibility**: Designed specifically for Flipper Zero users and SubGHz enthusiasts.

## How It Works
1. Select the source folder containing `.sub` files.
2. Choose the destination folder where sorted files will be stored.
3. Check the desired frequencies and protocols.
4. Click **Start Sorting** to begin.

The application organizes the files into directories based on their frequency and protocol, ensuring easy access and management.

## Requirements
- Python 3.6 or later.
- Required Python Libraries:
  - `tkinter`
  - `shutil`
  - `os`
  - `re`

## Installation
1. Clone this repository:
   ```bash
   git clone [https://github.com/[your-username]/flipper-subghz-sorter.git](https://github.com/Vlad-F13/Flipper-SubGHz-Signal-File-Organizer)
   cd flipper-subghz-sorter
2. Run the application:
   ```bash
   python flipper-subghz-sorter.git
