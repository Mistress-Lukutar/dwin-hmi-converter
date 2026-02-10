# ServoHMI DWIN Converter - Agent Guide

## Project Overview

This is a Python-based tool for converting HTML-based Human Machine Interface (HMI) designs into 24-bit BMP images compatible with **DWIN DGUS (DWIN Graphic User System)** industrial displays.

The project uses an external JSON configuration approach, allowing multiple HMI projects to be managed with different configuration files stored in the `input/` directory.

### Key Purpose
- Input: HTML + CSS + JavaScript interface design + JSON configuration
- Output: 24-bit BMP images (configurable resolution) for DWIN displays
- Use case: Industrial HMI systems with multi-state UI elements

---

## Technology Stack

### Core Technologies
| Component | Purpose | Version |
|-----------|---------|---------|
| Python | Main runtime | 3.10+ |
| Selenium | Headless browser automation | >=4.0.0 |
| Pillow (PIL) | Image processing and BMP conversion | >=9.0.0 |
| Chrome | HTML rendering engine | Latest stable |
| ChromeDriver | WebDriver for Chrome | Bundled with Selenium |

### Project Structure
```
servoHMI_dwin/
├── input/                      # Project configurations and HTML files
│   ├── config.json             # Default project configuration
│   └── UI_Non_Auto.html        # Source HTML interface
├── src/                        # Source code package
│   ├── __init__.py
│   ├── config_loader.py        # JSON configuration loader
│   ├── driver.py               # WebDriver management
│   ├── capture/                # Screenshot capture modules
│   │   ├── __init__.py
│   │   ├── page.py             # Full page screenshot capture
│   │   ├── element.py          # Individual element capture
│   │   └── state_capture.py    # CSS-based state capture (NEW)
│   ├── processing/             # Image processing modules
│   │   ├── __init__.py
│   │   ├── dedup.py            # Duplicate removal
│   │   ├── organize.py         # Size-based organization
│   │   └── verify.py           # BMP format verification
│   ├── utils/                  # Utility modules
│   │   ├── __init__.py
│   │   ├── filesystem.py       # File system operations
│   │   └── image.py            # Image processing utilities
│   └── dgus/                   # DGUS preparation module
│       ├── __init__.py
│       └── prepare.py          # DGUS project preparation
├── scripts/                    # Executable scripts
│   ├── convert.py              # Main entry point with --config support
│   └── convert.bat             # Batch launcher
├── tests/                      # Test suite
├── .venv/                      # Python virtual environment
├── output/                     # Generated BMP files (created at runtime)
│   ├── pages/                  # Full page screenshots
│   │   └── *_coords.json       # Element coordinates per page
│   ├── elements/               # Individual UI elements
│   └── dgus/                   # DGUS project files
│       ├── DWIN_SET/           # Files for display upload
│       ├── ICON/               # Grouped unique UI elements
│       ├── templates/          # Template images with element outlines
│       ├── touch_areas_guide.txt  # Touch area configuration guide
│       └── pages_info.txt      # Page descriptions
├── requirements.txt            # Python dependencies
├── convert.bat                 # Windows batch launcher
├── setup.py                    # Package setup
└── AGENTS.md                   # This file
```

---

## Build and Run Commands

### Prerequisites
1. Python 3.10 or higher installed
2. Google Chrome installed at standard location
3. Create virtual environment and install dependencies

### Initial Setup
```powershell
# Create virtual environment
python -m venv .venv

# Activate environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Converter

**With default configuration (input/config.json):**
```powershell
.\convert.bat
# or
python scripts\convert.py
```

**With specific configuration:**
```powershell
python scripts\convert.py --config input\my_project.json
```

**Development mode (skip DGUS preparation):**
```powershell
python scripts\convert.py --skip-dgus
python scripts\convert.py --config input\project.json --skip-dgus
```

**Verbose output:**
```powershell
python scripts\convert.py -v
python scripts\convert.py --config input\project.json --skip-dgus -v
```

---

## Configuration System

### JSON Configuration Format

Each project has a JSON configuration file stored in `input/`:

```json
{
  "name": "My HMI Project",
  "html_file": "UI_Non_Auto.html",
  "resolution": [1024, 768],
  "bmp_depth": 24,
  "container_selector": ".hmi-container",
  
  "pages": {
    "0": {"name": "main", "title": "Main Control"},
    "1": {"name": "settings", "title": "Settings"},
    "2": {"name": "logs", "title": "Logs"},
    "3": {"name": "selftest", "title": "Self-Test"}
  },
  
  "elements": {
    "btn_move": "#btnMove",
    "btn_heater": "#btnHeater",
    "indicator_air": "#airIndicator"
  },
  
  "element_states": {
    "led_heater": {
      "selector": "#ledHeater",
      "page": 0,
      "states": [
        {"name": "off", "js": "el.classList.remove('green'); el.classList.add('red');"},
        {"name": "on", "js": "el.classList.remove('red'); el.classList.add('green');"}
      ]
    }
  },
  
  "touch_areas": {
    "main": {
      "btn_move": {"x": 15, "y": 653, "width": 484, "height": 80}
    }
  },
  
  "page_mapping": {
    "00_main.bmp": "00.bmp",
    "01_settings.bmp": "01.bmp"
  }
}
```

### Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Project name for display |
| `html_file` | string | Path to HTML file (relative to config) |
| `resolution` | [w, h] | Target display resolution |
| `bmp_depth` | int | Color depth (24 for DWIN) |
| `container_selector` | string | CSS selector for main container |
| `pages` | object | Page definitions by number |
| `elements` | object | Static element CSS selectors |
| `element_states` | object | Multi-state element configurations |
| `touch_areas` | object | Touch area coordinates by page |
| `page_mapping` | object | Output file to DGUS file mapping |

### Multi-State Element Configuration

The key feature for DWIN Variable Icon implementation:

```json
"element_states": {
  "element_name": {
    "selector": "#cssSelector",
    "page": 0,
    "states": [
      {
        "name": "state1",
        "js": "el.classList.remove('active'); el.style.color = 'gray';"
      },
      {
        "name": "state2", 
        "js": "el.classList.add('active'); el.style.color = 'green';"
      }
    ]
  }
}
```

The `js` code is executed in browser context with `el` referencing the element.

---

## Architecture Changes (Simplified)

### Old Approach (Complex)
```
Simulate click → Update app state → Wait for render → Capture page
├── 14+ page screenshots
├── Complex JavaScript simulation
├── Hardcoded to specific HTML logic
└── 30-40 seconds runtime
```

### New Approach (Simplified)
```
Navigate to page → Apply CSS classes → Capture element
├── 4 page screenshots + element states
├── Simple CSS manipulation only
├── Works with any HTML structure
└── 10-15 seconds runtime
```

### Removed Components
- `StateSimulator` with complex state logic
- URL parameter modes (`?alarm=1`, `?startup=error`)
- Hardcoded JavaScript function calls (`toggleHeater()`, etc.)
- Multiple page states (idle, moving, fuel, etc.)

### New Components
- `ProjectConfig` - loads from JSON
- `StateCapture` - CSS-only state switching
- `config_loader` - JSON parsing and validation

---

## Key Classes Reference

### ProjectConfig
```python
class ProjectConfig:
    @classmethod
    def from_file(cls, config_path: Path) -> "ProjectConfig"
    def get_html_path(self) -> Path
    def get_page_numbers(self) -> List[int]
    def get_element_states_for_page(self, page_num: int) -> Dict[str, dict]
```

### StateCapture
```python
class StateCapture:
    def capture_element_states(self, output_dir: Path) -> Dict[str, List[str]]
    def capture_static_elements(self, output_dir: Path) -> int
    def dismiss_selftest(self) -> None
```

### PageCapture
```python
class PageCapture:
    def capture_all_pages(self, output_dir: Path) -> List[str]
    def capture_full_page(self, filename: Path, container_selector: str) -> bool
```

---

## Multi-Project Workflow

### Project Structure Example
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

### Running Different Projects
```powershell
# Project A
python scripts\convert.py --config input\project_a\config.json

# Project B  
python scripts\convert.py --config input\project_b\config.json

# Default project
python scripts\convert.py
```

### Isolated Outputs
Each project outputs to the `output/` directory, so run one at a time or modify config to use project-specific output directories.

---

## Command Line Interface

### convert.py Options
```
usage: convert.py [-h] [--config PATH] [--skip-dgus] [-v]

Convert HTML HMI to DWIN-compatible BMP images

options:
  -h, --help       show this help message and exit
  --config PATH    Path to project configuration JSON file
  --skip-dgus      Skip DGUS project preparation
  -v, --verbose    Enable verbose logging
```

### Examples
```bash
# Default configuration
python scripts\convert.py

# Specific project
python scripts\convert.py --config input\custom.json

# Development mode
python scripts\convert.py --skip-dgus

# Debug mode
python scripts\convert.py -v

# Combined
python scripts\convert.py --config input\custom.json --skip-dgus -v
```

---

## Deployment Process

### Automatic Generation
1. **Prepare configuration**: Create `input/<project>/config.json`
2. **Run converter**: `python scripts\convert.py --config input/<project>/config.json`
3. **Check output**: Verify files in `output/` (pages, elements, dgus/)

### Output Files
- `output/pages/*.bmp` - Full page screenshots (4 files)
- `output/elements/*.bmp` - Static elements + state variants
- `output/dgus/DWIN_SET/*.bmp` - DGUS-formatted page files
- `output/dgus/ICON/*/` - Size-organized element icons
- `output/dgus/templates/*.bmp` - Template images with element outlines
- `output/dgus/touch_areas_guide.txt` - Coordinate reference

### Manual DGUS Configuration
1. Open DGUS Tool
2. Import BMP files from `HMI/DWIN_SET/`
3. Add Variable Icon controls using coordinates from guide
4. Configure touch areas
5. Upload to display

---

## Quick Reference for Agents

**To run the pipeline:**
```powershell
python scripts\convert.py --config input\myproject.json
```

**To modify element selectors:**
Edit `elements` section in the JSON configuration file.

**To add element states:**
Add entry to `element_states` in JSON with CSS manipulation JS.

**To change resolution:**
Modify `resolution` field in JSON config (must match HTML CSS).

**To add a new page:**
1. Add page HTML to the HTML file
2. Add page entry to `pages` in JSON config
3. Add page to `page_mapping` for DGUS

**Output locations:**
- `output/pages/` - Page screenshots
- `output/elements/` - UI elements with state variants
- `output/dgus/DWIN_SET/` - DGUS display files
- `output/dgus/ICON/32/` - 99/ - Icon groups by size
- `output/dgus/templates/` - Template images with element outlines

**DGUS Project setup:**
1. Open DGUS Tool
2. Load project from `output/dgus/` folder
3. Import BMP files from `output/dgus/DWIN_SET/`
4. Configure Variable Icons using `output/dgus/touch_areas_guide.txt`
