import customtkinter as ctk
import json
import os
import ctypes
from datetime import datetime
import schedule
import time
import threading
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog
import sys
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import random
import shutil

# Configure logging
logging.basicConfig(
    filename='wallpaper_scheduler.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Set appearance mode and default color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class WallpaperScheduler(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Wallpaper Scheduler")
        self.geometry("1200x800")  # Increased width for better spacing
        self.minsize(1200, 800)

        # Set custom colors
        self.colors = {
            'primary': '#2B87D1',
            'success': '#2EA043',
            'danger': '#DA3633',
            'text_primary': '#E6EDF3',
            'text_secondary': '#7D8590',
            'border': '#30363D',
            'button_hover': '#1C6CB7'
        }

        # Default schedule structure
        self.DEFAULT_SCHEDULE = {
            'day': {
                'time': '08:00',
                'wallpaper': None,
                'wallpapers_folder': None,
                'random_rotation': False,
                'rotation_interval': 30,  # minutes
                'style': 'fill'
            },
            'night': {
                'time': '20:00',
                'wallpaper': None,
                'wallpapers_folder': None,
                'random_rotation': False,
                'rotation_interval': 30,  # minutes
                'style': 'fill'
            }
        }

        # Initialize variables
        self.schedules = self.DEFAULT_SCHEDULE.copy()
        self.scheduler_thread = None
        self.is_running = False
        self.current_theme = "dark"
        self.wallpaper_styles = ["fill", "fit", "stretch", "tile", "center", "span"]
        
        # Create settings
        self.settings = {
            'minimize_to_tray': True,
            'show_notifications': True,
            'auto_start': True,
            'theme': 'dark',
            'backup_wallpapers': True,
            'backup_folder': str(Path.home() / "WallpaperBackups")
        }

        # Load saved data
        self.load_schedules()
        self.load_settings()

        # Create UI
        self.create_menu()
        self.create_widgets()
        self.create_status_bar()

        # Start scheduler if auto-start is enabled
        if self.settings['auto_start']:
            self.start_scheduler()

    def create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import Settings...", command=self.import_settings)
        file_menu.add_command(label="Export Settings...", command=self.export_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)

        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        
        # Tools menu
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Backup Wallpapers", command=self.backup_wallpapers)
        tools_menu.add_command(label="Clean Backup Folder", command=self.clean_backups)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="View Logs", command=self.view_logs)
        help_menu.add_command(label="About", command=self.show_about)

    def create_widgets(self):
        # Create main container with tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)

        # Add tabs
        self.tabview.add("Schedules")
        self.tabview.add("Settings")
        self.tabview.add("Statistics")

        # Schedules tab
        self.create_schedules_tab()
        
        # Settings tab
        self.create_settings_tab()
        
        # Statistics tab
        self.create_statistics_tab()

    def create_schedules_tab(self):
        tab = self.tabview.tab("Schedules")
        
        # Header with subtle separator
        header_frame = ctk.CTkFrame(tab, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 20))
        
        header = ctk.CTkLabel(
            header_frame,
            text="Wallpaper Scheduler",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        header.pack(pady=(0, 5))
        
        subtitle = ctk.CTkLabel(
            header_frame,
            text="Configure your day and night wallpaper schedules",
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_secondary']
        )
        subtitle.pack()

        # Create schedule frames with better spacing
        schedules_frame = ctk.CTkFrame(tab, fg_color="transparent")
        schedules_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Grid layout for better organization
        schedules_frame.grid_columnconfigure(0, weight=1, pad=15)
        schedules_frame.grid_columnconfigure(1, weight=1, pad=15)

        # Day Schedule
        day_frame = self.create_schedule_frame(schedules_frame, "Day Schedule", "day")
        day_frame.grid(row=0, column=0, sticky="nsew", padx=15)

        # Night Schedule
        night_frame = self.create_schedule_frame(schedules_frame, "Night Schedule", "night")
        night_frame.grid(row=0, column=1, sticky="nsew", padx=15)

        # Control buttons with improved styling
        controls_frame = ctk.CTkFrame(tab, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(10, 20), padx=30)

        self.start_button = ctk.CTkButton(
            controls_frame,
            text="Start Scheduler",
            command=self.start_scheduler,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors['success'],
            hover_color="#2B8A3E",
            height=38,
            width=150
        )
        self.start_button.pack(side="left", padx=10)

        self.stop_button = ctk.CTkButton(
            controls_frame,
            text="Stop Scheduler",
            command=self.stop_scheduler,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors['danger'],
            hover_color="#B92E2C",
            height=38,
            width=150
        )
        self.stop_button.pack(side="left", padx=10)

    def create_schedule_frame(self, parent, title, schedule_type):
        frame = ctk.CTkFrame(parent)
        frame.configure(fg_color=("gray85", "gray17"))  # Subtle background difference
        
        # Title with icon
        title_frame = ctk.CTkFrame(frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(15, 20), padx=20)
        
        icon_text = "🌞" if schedule_type == "day" else "🌙"
        title_label = ctk.CTkLabel(
            title_frame,
            text=f"{icon_text} {title}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack()

        # Time selection with better styling
        time_frame = ctk.CTkFrame(frame, fg_color="transparent")
        time_frame.pack(fill="x", padx=20, pady=(0, 15))

        time_label = ctk.CTkLabel(
            time_frame,
            text="Schedule Time:",
            font=ctk.CTkFont(size=14)
        )
        time_label.pack(side="left", padx=(0, 10))
        
        time_var = tk.StringVar(value=self.schedules[schedule_type]['time'])
        time_entry = ctk.CTkEntry(
            time_frame,
            textvariable=time_var,
            width=100,
            height=32,
            font=ctk.CTkFont(size=14)
        )
        time_entry.pack(side="left")

        # Style selection with improved dropdown
        style_frame = ctk.CTkFrame(frame, fg_color="transparent")
        style_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        style_label = ctk.CTkLabel(
            style_frame,
            text="Wallpaper Style:",
            font=ctk.CTkFont(size=14)
        )
        style_label.pack(side="left", padx=(0, 10))
        
        style_var = tk.StringVar(value=self.schedules[schedule_type]['style'])
        style_menu = ctk.CTkOptionMenu(
            style_frame,
            values=self.wallpaper_styles,
            variable=style_var,
            command=lambda x: self.update_schedule_setting(schedule_type, 'style', x),
            width=120,
            height=32,
            font=ctk.CTkFont(size=14)
        )
        style_menu.pack(side="left")

        # Random rotation with modern toggle
        rotation_frame = ctk.CTkFrame(frame, fg_color="transparent")
        rotation_frame.pack(fill="x", padx=20, pady=(0, 15))

        random_var = tk.BooleanVar(value=self.schedules[schedule_type]['random_rotation'])
        random_check = ctk.CTkSwitch(  # Changed to Switch for modern look
            rotation_frame,
            text="Random Rotation",
            variable=random_var,
            command=lambda: self.update_schedule_setting(
                schedule_type, 'random_rotation', random_var.get()
            ),
            font=ctk.CTkFont(size=14)
        )
        random_check.pack(side="left", padx=(0, 15))

        interval_label = ctk.CTkLabel(
            rotation_frame,
            text="Interval (min):",
            font=ctk.CTkFont(size=14)
        )
        interval_label.pack(side="left", padx=(10, 5))

        interval_var = tk.StringVar(value=str(self.schedules[schedule_type]['rotation_interval']))
        interval_entry = ctk.CTkEntry(
            rotation_frame,
            textvariable=interval_var,
            width=60,
            height=32,
            font=ctk.CTkFont(size=14)
        )
        interval_entry.pack(side="left")

        # Wallpaper selection with improved buttons
        wallpaper_frame = ctk.CTkFrame(frame, fg_color="transparent")
        wallpaper_frame.pack(fill="x", padx=20, pady=(0, 15))

        select_button = ctk.CTkButton(
            wallpaper_frame,
            text="Select Wallpaper",
            command=lambda: self.select_wallpaper(frame, schedule_type),
            font=ctk.CTkFont(size=14),
            height=32,
            fg_color=self.colors['primary'],
            hover_color=self.colors['button_hover']
        )
        select_button.pack(side="left", padx=(0, 10))

        folder_button = ctk.CTkButton(
            wallpaper_frame,
            text="Select Folder",
            command=lambda: self.select_folder(schedule_type),
            font=ctk.CTkFont(size=14),
            height=32,
            fg_color=self.colors['primary'],
            hover_color=self.colors['button_hover']
        )
        folder_button.pack(side="left")

        # Preview area with placeholder
        preview_frame = ctk.CTkFrame(frame, fg_color=("gray80", "gray20"))
        preview_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        if not self.schedules[schedule_type]['wallpaper']:
            placeholder = ctk.CTkLabel(
                preview_frame,
                text="No wallpaper selected",
                font=ctk.CTkFont(size=14),
                text_color=self.colors['text_secondary']
            )
            placeholder.pack(pady=40)
        else:
            self.update_preview(frame, self.schedules[schedule_type]['wallpaper'])

        return frame

    def create_settings_tab(self):
        tab = self.tabview.tab("Settings")
        
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Application Settings
        app_settings = ctk.CTkFrame(settings_frame)
        app_settings.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            app_settings,
            text="Application Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        # Create checkboxes for boolean settings
        for setting in ['minimize_to_tray', 'show_notifications', 'auto_start', 'backup_wallpapers']:
            var = tk.BooleanVar(value=self.settings[setting])
            ctk.CTkCheckBox(
                app_settings,
                text=setting.replace('_', ' ').title(),
                variable=var,
                command=lambda s=setting, v=var: self.update_setting(s, v.get())
            ).pack(pady=5)

        # Backup folder selection
        backup_frame = ctk.CTkFrame(app_settings)
        backup_frame.pack(fill="x", pady=10, padx=20)
        
        ctk.CTkLabel(backup_frame, text="Backup Folder:").pack(side="left", padx=(0, 10))
        
        backup_entry = ctk.CTkEntry(
            backup_frame,
            width=300
        )
        backup_entry.insert(0, self.settings['backup_folder'])
        backup_entry.pack(side="left", padx=(0, 10))
        
        def select_backup_folder():
            folder = filedialog.askdirectory()
            if folder:
                backup_entry.delete(0, tk.END)
                backup_entry.insert(0, folder)
                self.update_setting('backup_folder', folder)
        
        ctk.CTkButton(
            backup_frame,
            text="Browse",
            command=select_backup_folder
        ).pack(side="left")

    def create_statistics_tab(self):
        tab = self.tabview.tab("Statistics")
        
        stats_frame = ctk.CTkFrame(tab)
        stats_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Add statistics content
        ctk.CTkLabel(
            stats_frame,
            text="Wallpaper Statistics",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        # Add some example statistics
        stats = self.calculate_statistics()
        
        for key, value in stats.items():
            stat_frame = ctk.CTkFrame(stats_frame)
            stat_frame.pack(fill="x", pady=5, padx=20)
            
            ctk.CTkLabel(
                stat_frame,
                text=f"{key}:",
                font=ctk.CTkFont(weight="bold")
            ).pack(side="left", padx=(0, 10))
            
            ctk.CTkLabel(
                stat_frame,
                text=str(value)
            ).pack(side="left")

    def create_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=32, fg_color=("gray85", "gray17"))
        self.status_bar.pack(fill="x", side="bottom")
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.status_label.pack(side="left", padx=10)
        
        self.scheduler_status = ctk.CTkLabel(
            self.status_bar,
            text="Scheduler: Stopped",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors['text_secondary']
        )
        self.scheduler_status.pack(side="right", padx=10)

    def update_schedule_setting(self, schedule_type: str, setting: str, value: Any):
        self.schedules[schedule_type][setting] = value
        self.save_schedules()
        if self.is_running:
            self.restart_scheduler()

    def update_setting(self, setting: str, value: Any):
        self.settings[setting] = value
        self.save_settings()

    def toggle_theme(self):
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.current_theme = new_theme
        ctk.set_appearance_mode(new_theme)
        self.update_setting('theme', new_theme)

    def backup_wallpapers(self):
        try:
            backup_dir = Path(self.settings['backup_folder'])
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for schedule_type in ['day', 'night']:
                if self.schedules[schedule_type]['wallpaper']:
                    src = Path(self.schedules[schedule_type]['wallpaper'])
                    if src.exists():
                        dst = backup_dir / f"{schedule_type}_{timestamp}_{src.name}"
                        shutil.copy2(src, dst)
                        
            self.show_status("Wallpapers backed up successfully")
        except Exception as e:
            self.show_status(f"Backup failed: {str(e)}", error=True)
            logging.error(f"Backup failed: {str(e)}")

    def clean_backups(self):
        try:
            backup_dir = Path(self.settings['backup_folder'])
            if not backup_dir.exists():
                return
                
            # Keep only last 10 backups for each type
            for schedule_type in ['day', 'night']:
                pattern = f"{schedule_type}_*"
                backups = sorted(backup_dir.glob(pattern))
                if len(backups) > 10:
                    for old_backup in backups[:-10]:
                        old_backup.unlink()
                        
            self.show_status("Old backups cleaned successfully")
        except Exception as e:
            self.show_status(f"Cleanup failed: {str(e)}", error=True)
            logging.error(f"Cleanup failed: {str(e)}")

    def show_status(self, message: str, error: bool = False):
        self.status_label.configure(
            text=message,
            text_color="red" if error else "white"
        )

    def calculate_statistics(self) -> Dict[str, Any]:
        stats = {
            "Total Wallpapers": 0,
            "Day Wallpapers": 0,
            "Night Wallpapers": 0,
            "Last Change": "Never",
            "Scheduler Status": "Running" if self.is_running else "Stopped"
        }
        
        for schedule_type in ['day', 'night']:
            if self.schedules[schedule_type]['wallpaper']:
                stats[f"{schedule_type.title()} Wallpapers"] += 1
            if self.schedules[schedule_type]['wallpapers_folder']:
                folder = Path(self.schedules[schedule_type]['wallpapers_folder'])
                if folder.exists():
                    stats[f"{schedule_type.title()} Wallpapers"] += len(list(folder.glob("*.jpg")))
                    stats[f"{schedule_type.title()} Wallpapers"] += len(list(folder.glob("*.png")))
        
        stats["Total Wallpapers"] = stats["Day Wallpapers"] + stats["Night Wallpapers"]
        
        return stats

    def import_settings(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if 'schedules' in data and 'settings' in data:
                        self.schedules = data['schedules']
                        self.settings = data['settings']
                        self.save_schedules()
                        self.save_settings()
                        self.show_status("Settings imported successfully")
                    else:
                        raise ValueError("Invalid settings file format")
            except Exception as e:
                self.show_status(f"Import failed: {str(e)}", error=True)
                logging.error(f"Import failed: {str(e)}")

    def export_settings(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            try:
                data = {
                    'schedules': self.schedules,
                    'settings': self.settings
                }
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=4)
                self.show_status("Settings exported successfully")
            except Exception as e:
                self.show_status(f"Export failed: {str(e)}", error=True)
                logging.error(f"Export failed: {str(e)}")

    def view_logs(self):
        if os.path.exists('wallpaper_scheduler.log'):
            with open('wallpaper_scheduler.log', 'r') as f:
                log_window = ctk.CTkToplevel(self)
                log_window.title("Application Logs")
                log_window.geometry("800x600")
                
                log_text = ctk.CTkTextbox(log_window)
                log_text.pack(fill="both", expand=True, padx=10, pady=10)
                log_text.insert("1.0", f.read())
                log_text.configure(state="disabled")

    def show_about(self):
        about_window = ctk.CTkToplevel(self)
        about_window.title("About Wallpaper Scheduler")
        about_window.geometry("400x300")
        
        ctk.CTkLabel(
            about_window,
            text="Wallpaper Scheduler",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(
            about_window,
            text="A modern wallpaper management application\n\n" +
                 "Features:\n" +
                 "- Day/Night scheduling\n" +
                 "- Random rotation\n" +
                 "- Multiple wallpaper styles\n" +
                 "- Backup management\n" +
                 "- Theme customization"
        ).pack(pady=20)
        
        ctk.CTkLabel(
            about_window,
            text="Version 2.0.0"
        ).pack(pady=20)

    def update_preview(self, frame, image_path):
        try:
            # Clear existing preview
            for widget in frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "":
                    widget.destroy()

            # Create preview container
            preview_container = ctk.CTkFrame(frame, fg_color=("gray80", "gray20"))
            preview_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

            # Load and resize image
            image = Image.open(image_path)
            
            # Calculate aspect ratio
            aspect_ratio = image.width / image.height
            target_height = 180
            target_width = int(target_height * aspect_ratio)
            
            image.thumbnail((target_width, target_height))
            photo = ImageTk.PhotoImage(image)

            # Create preview label with image
            preview_label = ctk.CTkLabel(
                preview_container,
                text="",
                image=photo,
                fg_color="transparent"
            )
            preview_label.image = photo  # Keep a reference
            preview_label.pack(pady=10)

            # Add image info
            info_text = f"{Path(image_path).name}\n{image.width}x{image.height}"
            info_label = ctk.CTkLabel(
                preview_container,
                text=info_text,
                font=ctk.CTkFont(size=12),
                text_color=self.colors['text_secondary']
            )
            info_label.pack(pady=(0, 10))

        except Exception as e:
            logging.error(f"Error updating preview: {e}")
            self.show_status(f"Error updating preview: {str(e)}", error=True)

    def load_schedules(self):
        try:
            if os.path.exists('schedules.json'):
                with open('schedules.json', 'r') as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, dict) and 'day' in loaded_data and 'night' in loaded_data:
                        # Ensure all required fields are present
                        for schedule_type in ['day', 'night']:
                            default_schedule = self.DEFAULT_SCHEDULE[schedule_type].copy()
                            if schedule_type in loaded_data:
                                # Update default values with loaded values while preserving structure
                                loaded_schedule = loaded_data[schedule_type]
                                for key in default_schedule:
                                    if key in loaded_schedule:
                                        default_schedule[key] = loaded_schedule[key]
                            loaded_data[schedule_type] = default_schedule
                        self.schedules = loaded_data
                    else:
                        self.schedules = self.DEFAULT_SCHEDULE.copy()
        except Exception as e:
            logging.error(f"Error loading schedules: {e}")
            self.schedules = self.DEFAULT_SCHEDULE.copy()

    def load_settings(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    loaded_data = json.load(f)
                    self.settings.update(loaded_data)
        except Exception as e:
            logging.error(f"Error loading settings: {e}")

    def save_schedules(self):
        try:
            with open('schedules.json', 'w') as f:
                json.dump(self.schedules, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving schedules: {e}")
            self.show_status(f"Error saving schedules: {str(e)}", error=True)

    def save_settings(self):
        try:
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            self.show_status(f"Error saving settings: {str(e)}", error=True)

    def set_wallpaper(self, wallpaper_path):
        try:
            if os.path.exists(wallpaper_path):
                ctypes.windll.user32.SystemParametersInfoW(20, 0, wallpaper_path, 3)
                self.show_status(f"Wallpaper changed: {Path(wallpaper_path).name}")
                logging.info(f"Wallpaper changed to: {wallpaper_path}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error setting wallpaper: {e}")
            self.show_status(f"Error setting wallpaper: {str(e)}", error=True)
            return False

    def get_random_wallpaper(self, schedule_type):
        if self.schedules[schedule_type]['wallpapers_folder']:
            folder = Path(self.schedules[schedule_type]['wallpapers_folder'])
            if folder.exists():
                wallpapers = list(folder.glob("*.jpg")) + list(folder.glob("*.png"))
                if wallpapers:
                    return str(random.choice(wallpapers))
        return self.schedules[schedule_type]['wallpaper']

    def run_scheduler(self):
        while self.is_running:
            try:
                current_time = datetime.now().time()
                current_hour = current_time.hour
                
                # Determine current period (day or night)
                day_start = datetime.strptime(self.schedules['day']['time'], "%H:%M").time()
                night_start = datetime.strptime(self.schedules['night']['time'], "%H:%M").time()
                
                current_period = 'day' if day_start <= current_time < night_start else 'night'
                
                # Handle random rotation
                if self.schedules[current_period]['random_rotation']:
                    if not hasattr(self, 'last_rotation') or \
                       datetime.now() - self.last_rotation > timedelta(
                           minutes=self.schedules[current_period]['rotation_interval']
                       ):
                        wallpaper = self.get_random_wallpaper(current_period)
                        if wallpaper:
                            self.set_wallpaper(wallpaper)
                            self.last_rotation = datetime.now()
                else:
                    # Regular schedule
                    wallpaper = self.schedules[current_period]['wallpaper']
                    if wallpaper:
                        self.set_wallpaper(wallpaper)
                
                time.sleep(60)  # Check every minute
            except Exception as e:
                logging.error(f"Scheduler error: {e}")
                self.show_status(f"Scheduler error: {str(e)}", error=True)
                time.sleep(60)

    def start_scheduler(self):
        if not self.is_running:
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self.run_scheduler)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            self.scheduler_status.configure(text="Scheduler: Running")
            self.show_status("Scheduler started")
            logging.info("Scheduler started")

    def stop_scheduler(self):
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        self.scheduler_status.configure(text="Scheduler: Stopped")
        self.show_status("Scheduler stopped")
        logging.info("Scheduler stopped")

    def restart_scheduler(self):
        self.stop_scheduler()
        self.start_scheduler()

    def quit_app(self):
        self.stop_scheduler()
        self.quit()

    def select_wallpaper(self, frame, schedule_type):
        file_path = filedialog.askopenfilename(
            title=f"Select {schedule_type.title()} Wallpaper",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("BMP files", "*.bmp"),
                ("GIF files", "*.gif"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.schedules[schedule_type]['wallpaper'] = file_path
            self.save_schedules()
            self.update_preview(frame, file_path)
            self.show_status(f"{schedule_type.title()} wallpaper selected: {Path(file_path).name}")

    def select_folder(self, schedule_type):
        folder_path = filedialog.askdirectory(
            title=f"Select {schedule_type.title()} Wallpapers Folder"
        )
        if folder_path:
            self.schedules[schedule_type]['wallpapers_folder'] = folder_path
            self.save_schedules()
            self.show_status(f"{schedule_type.title()} wallpapers folder selected")

if __name__ == "__main__":
    try:
        app = WallpaperScheduler()
        app.mainloop()
    except Exception as e:
        logging.critical(f"Application crashed: {e}")
        raise 