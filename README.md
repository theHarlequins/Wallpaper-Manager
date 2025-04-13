# Wallpaper Manager

A modern, feature-rich wallpaper management application for Windows with day/night scheduling and advanced customization options.

![Wallpaper Manager Screenshot](screenshots/main.png)

## Features

- 🌞 Day/Night wallpaper scheduling
- 🔄 Random wallpaper rotation with customizable intervals
- 🖼️ Multiple wallpaper styles (fill, fit, stretch, tile, center, span)
- 📁 Folder-based wallpaper selection
- 🎨 Dark/Light theme support
- 💾 Backup management system
- 📊 Wallpaper statistics
- 🔍 Comprehensive logging
- ⚙️ Customizable settings
- 🔄 Import/Export configuration

## Requirements

- Windows 10/11
- Python 3.8 or higher
- Required Python packages (install via `pip install -r requirements.txt`):
  - customtkinter
  - Pillow
  - pywin32
  - schedule

## Installation

1. Clone this repository:

```bash
git clone https://github.com/theHarlequins/Wallpaper-Manager.git
cd Wallpaper-Manager
```

2. Install required dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python app.py
```

## Usage

1. Launch the application
2. Configure your day and night schedules:
   - Set schedule times
   - Choose wallpaper style
   - Select individual wallpapers or folders
   - Enable random rotation if desired
3. Use the Start/Stop buttons to control the scheduler
4. Access additional features through the menu bar:
   - Toggle dark/light theme
   - Backup wallpapers
   - View statistics
   - Import/Export settings

## Configuration

The application stores its configuration in two JSON files:

- `schedules.json`: Contains day/night schedule settings
- `settings.json`: Contains application preferences

## Features in Detail

### Wallpaper Scheduling

- Set specific times for day and night wallpapers
- Choose from multiple wallpaper styles
- Preview wallpapers before applying

### Random Rotation

- Enable automatic wallpaper rotation
- Set custom rotation intervals
- Select folders for random wallpaper selection

### Backup Management

- Automatic wallpaper backup
- Configurable backup location
- Backup cleanup functionality

### Theme Customization

- Switch between dark and light themes
- Modern, clean interface
- Consistent styling throughout

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Icons from various open-source projects
