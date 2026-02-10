# DWIN HMI Converter

A Python tool for converting HTML-based Human Machine Interface (HMI) designs into 24-bit BMP images compatible with **DWIN DGUS (DWIN Graphic User System)** industrial displays.

## Features

- **Multi-Project Support**: Manage multiple HMI projects with JSON configuration files
- **CSS-Based State Capture**: Capture UI elements in different states without complex simulation
- **Automatic Element Organization**: Group elements by size for DGUS Variable Icon implementation
- **Template Generation**: Create visual reference images with element outlines and coordinates
- **Command-Line Interface**: Easy-to-use CLI with verbose logging options

## Requirements

- Python 3.10+
- Google Chrome
- Windows (for .bat launcher) or any OS with Python

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/dwin-hmi-converter.git
cd dwin-hmi-converter

# Create virtual environment
python -m venv .venv

# Activate environment (Windows)
.venv\Scripts\activate

# Activate environment (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

1. **Prepare your HTML file** with the HMI interface design
2. **Create a configuration file** in `input/` directory (see `input/config.json` for example)
3. **Run the converter**:

```bash
# Using the batch launcher (Windows)
.\convert.bat

# Or using Python directly
python scripts/convert.py
```

## Project Structure

```
dwin-hmi-converter/
├── input/                      # Project configurations
│   ├── config.json            # Default configuration
│   └── *.html                 # HTML interface files
├── src/                        # Source code
│   ├── config_loader.py       # Configuration loader
│   ├── driver.py              # WebDriver management
│   ├── capture/               # Screenshot capture
│   ├── processing/            # Image processing
│   ├── utils/                 # Utilities
│   └── dgus/                  # DGUS preparation
├── scripts/
│   └── convert.py             # Main entry point
├── output/                     # Generated files (created at runtime)
│   ├── pages/                 # Page screenshots
│   ├── elements/              # UI elements
│   └── dgus/                  # DGUS project files
│       ├── DWIN_SET/          # Display upload files
│       ├── ICON/              # Organized icons
│       └── templates/         # Template images
└── convert.bat                # Windows launcher
```

## Configuration

Create a JSON configuration file for your project:

```json
{
  "name": "My HMI Project",
  "html_file": "interface.html",
  "resolution": [1024, 768],
  "container_selector": ".hmi-container",
  
  "pages": {
    "0": {"name": "main", "title": "Main Control"},
    "1": {"name": "settings", "title": "Settings"}
  },
  
  "elements": {
    "btn_start": "#btnStart",
    "led_status": "#ledStatus"
  },
  
  "element_states": {
    "led_status": {
      "selector": "#ledStatus",
      "page": 0,
      "states": [
        {"name": "off", "js": "el.classList.remove('on');"},
        {"name": "on", "js": "el.classList.add('on');"}
      ]
    }
  },
  
  "touch_areas": {
    "main": {
      "btn_start": {"x": 100, "y": 200, "width": 120, "height": 40}
    }
  },
  
  "page_mapping": {
    "00_main.bmp": "00.bmp",
    "01_settings.bmp": "01.bmp"
  }
}
```

### Configuration Fields

| Field | Description |
|-------|-------------|
| `name` | Project name |
| `html_file` | Path to HTML file |
| `resolution` | Display resolution `[width, height]` |
| `pages` | Page definitions |
| `elements` | CSS selectors for static elements |
| `element_states` | Multi-state element configurations |
| `touch_areas` | Touch area coordinates |
| `page_mapping` | Output to DGUS filename mapping |

## Usage

### Basic Usage

```bash
# Run with default configuration (input/config.json)
python scripts/convert.py

# Run with specific configuration
python scripts/convert.py --config input/project_a.json

# Skip DGUS preparation (faster for development)
python scripts/convert.py --skip-dgus

# Enable verbose output
python scripts/convert.py -v
```

### Multi-Project Setup

Store multiple projects in `input/` directory:

```
input/
├── project_a/
│   ├── config.json
│   └── interface.html
├── project_b/
│   ├── config.json
│   └── hmi.html
└── servo/
    ├── config.json
    └── UI_Non_Auto.html
```

Run specific project:

```bash
python scripts/convert.py --config input/project_a/config.json
```

## Output Files

After conversion, check the `output/` directory:

- **`output/pages/`** - Full page screenshots (e.g., `00_main.bmp`)
- **`output/elements/`** - Individual UI elements
- **`output/dgus/DWIN_SET/`** - DGUS-formatted files for display upload
- **`output/dgus/ICON/`** - Size-organized icons for Variable Icon
- **`output/dgus/templates/`** - Template images with element outlines

## DGUS Configuration

1. Open **DGUS Tool**
2. Load project from `output/dgus/` folder
3. Import BMP files from `output/dgus/DWIN_SET/`
4. Use template images in `output/dgus/templates/` as reference
5. Configure touch areas using `touch_areas_guide.txt`
6. Compile and upload to DWIN display

## How It Works

1. **Page Capture**: Navigates through all pages and captures full screenshots
2. **Element Capture**: Captures individual elements by CSS selectors
3. **State Capture**: Applies CSS classes to capture elements in different states
4. **Processing**: Removes duplicates and organizes by size
5. **DGUS Preparation**: Creates DWIN_SET folder with properly named files

## Element State Capture

Instead of simulating button clicks, the tool directly manipulates CSS classes:

```javascript
// Capture LED in "off" state
el.classList.remove('green');
el.classList.add('red');
capture_element();

// Capture LED in "on" state  
el.classList.remove('red');
el.classList.add('green');
capture_element();
```

This approach is faster and works with any HTML structure.

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please use the GitHub issue tracker.
