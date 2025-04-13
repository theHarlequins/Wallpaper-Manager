import sys
import json
import os
from datetime import datetime
from pathlib import Path
import winreg
import ctypes
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QTimeEdit,
                            QFileDialog, QListWidget, QMessageBox, QSystemTrayIcon,
                            QMenu, QStyle, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QIcon, QAction
import schedule
import time
import threading

class WallpaperScheduler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wallpaper Scheduler")
        self.setMinimumSize(800, 600)
        
        # Initialize variables with default structure
        self.default_schedule = {
            'day': {'start': '06:00', 'end': '18:00', 'wallpaper': ''},
            'night': {'start': '18:00', 'end': '06:00', 'wallpaper': ''}
        }
        self.schedules = self.default_schedule.copy()
        self.config_file = Path("schedules.json")
        self.load_schedules()
        
        # Setup UI
        self.setup_ui()
        self.setup_tray()
        self.setup_autostart()
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Day Schedule Group
        day_group = QGroupBox("Day Schedule")
        day_layout = QGridLayout()
        
        # Day start time
        day_layout.addWidget(QLabel("Start Time:"), 0, 0)
        self.day_start_time = QTimeEdit()
        self.day_start_time.setDisplayFormat("HH:mm")
        if self.schedules['day']['start']:
            self.day_start_time.setTime(QTime.fromString(self.schedules['day']['start'], "HH:mm"))
        day_layout.addWidget(self.day_start_time, 0, 1)
        
        # Day end time
        day_layout.addWidget(QLabel("End Time:"), 0, 2)
        self.day_end_time = QTimeEdit()
        self.day_end_time.setDisplayFormat("HH:mm")
        if self.schedules['day']['end']:
            self.day_end_time.setTime(QTime.fromString(self.schedules['day']['end'], "HH:mm"))
        day_layout.addWidget(self.day_end_time, 0, 3)
        
        # Day wallpaper selection
        self.day_wallpaper_btn = QPushButton("Select Day Wallpaper")
        self.day_wallpaper_btn.clicked.connect(lambda: self.select_wallpaper('day'))
        day_layout.addWidget(self.day_wallpaper_btn, 1, 0, 1, 2)
        
        self.day_wallpaper_label = QLabel(self.schedules['day']['wallpaper'] or "No wallpaper selected")
        day_layout.addWidget(self.day_wallpaper_label, 1, 2, 1, 2)
        
        day_group.setLayout(day_layout)
        layout.addWidget(day_group)

        # Night Schedule Group
        night_group = QGroupBox("Night Schedule")
        night_layout = QGridLayout()
        
        # Night start time
        night_layout.addWidget(QLabel("Start Time:"), 0, 0)
        self.night_start_time = QTimeEdit()
        self.night_start_time.setDisplayFormat("HH:mm")
        if self.schedules['night']['start']:
            self.night_start_time.setTime(QTime.fromString(self.schedules['night']['start'], "HH:mm"))
        night_layout.addWidget(self.night_start_time, 0, 1)
        
        # Night end time
        night_layout.addWidget(QLabel("End Time:"), 0, 2)
        self.night_end_time = QTimeEdit()
        self.night_end_time.setDisplayFormat("HH:mm")
        if self.schedules['night']['end']:
            self.night_end_time.setTime(QTime.fromString(self.schedules['night']['end'], "HH:mm"))
        night_layout.addWidget(self.night_end_time, 0, 3)
        
        # Night wallpaper selection
        self.night_wallpaper_btn = QPushButton("Select Night Wallpaper")
        self.night_wallpaper_btn.clicked.connect(lambda: self.select_wallpaper('night'))
        night_layout.addWidget(self.night_wallpaper_btn, 1, 0, 1, 2)
        
        self.night_wallpaper_label = QLabel(self.schedules['night']['wallpaper'] or "No wallpaper selected")
        night_layout.addWidget(self.night_wallpaper_label, 1, 2, 1, 2)
        
        night_group.setLayout(night_layout)
        layout.addWidget(night_group)

        # Save button
        save_btn = QPushButton("Save Schedule")
        save_btn.clicked.connect(self.save_current_schedule)
        layout.addWidget(save_btn)

    def select_wallpaper(self, mode):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select {mode.capitalize()} Wallpaper", "", 
            "Image Files (*.jpg *.jpeg *.png *.bmp)"
        )
        
        if file_path:
            self.schedules[mode]['wallpaper'] = file_path
            if mode == 'day':
                self.day_wallpaper_label.setText(Path(file_path).name)
            else:
                self.night_wallpaper_label.setText(Path(file_path).name)

    def save_current_schedule(self):
        # Save day schedule
        self.schedules['day']['start'] = self.day_start_time.time().toString("HH:mm")
        self.schedules['day']['end'] = self.day_end_time.time().toString("HH:mm")
        
        # Save night schedule
        self.schedules['night']['start'] = self.night_start_time.time().toString("HH:mm")
        self.schedules['night']['end'] = self.night_end_time.time().toString("HH:mm")
        
        self.save_schedules()
        self.update_scheduler()
        
        QMessageBox.information(self, "Success", "Schedule saved successfully!")

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.quit_application)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def setup_autostart(self):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                                winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, "WallpaperScheduler", 0, winreg.REG_SZ, 
                             str(Path(sys.argv[0]).absolute()))
            winreg.CloseKey(key)
        except OSError as e:
            QMessageBox.warning(self, "Auto-start Error", 
                              f"Failed to set auto-start: {str(e)}")

    def load_schedules(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_schedules = json.load(f)
                    # Ensure the loaded data has the correct structure
                    if isinstance(loaded_schedules, dict) and 'day' in loaded_schedules and 'night' in loaded_schedules:
                        self.schedules = loaded_schedules
                    else:
                        self.schedules = self.default_schedule.copy()
            except (json.JSONDecodeError, KeyError):
                self.schedules = self.default_schedule.copy()
        else:
            self.schedules = self.default_schedule.copy()

    def save_schedules(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.schedules, f)

    def set_wallpaper(self, path):
        try:
            # Set wallpaper style to Fill (10)
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                "Control Panel\\Desktop", 0, 
                                winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "10")
            winreg.CloseKey(key)

            # Set the wallpaper
            ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
            
            self.tray_icon.showMessage(
                "Wallpaper Changed",
                f"Changed to {Path(path).name}",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        except Exception as e:
            self.tray_icon.showMessage(
                "Error",
                f"Failed to set wallpaper: {str(e)}",
                QSystemTrayIcon.MessageIcon.Critical,
                2000
            )

    def update_scheduler(self):
        schedule.clear()
        
        # Schedule day wallpaper
        if self.schedules['day']['wallpaper']:
            schedule.every().day.at(self.schedules['day']['start']).do(
                self.set_wallpaper, self.schedules['day']['wallpaper'])
        
        # Schedule night wallpaper
        if self.schedules['night']['wallpaper']:
            schedule.every().day.at(self.schedules['night']['start']).do(
                self.set_wallpaper, self.schedules['night']['wallpaper'])

    def run_scheduler(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Wallpaper Scheduler",
            "Application minimized to tray",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def quit_application(self):
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WallpaperScheduler()
    window.show()
    sys.exit(app.exec()) 