# Source Package - DWIN HMI Converter

This package contains the modular source code for converting HTML HMI designs
to DWIN DGUS-compatible BMP images.

## Package Structure

```
src/
├── __init__.py          # Package initialization
├── config_loader.py     # JSON configuration loader (NEW)
├── driver.py            # WebDriver management
├── capture/             # Screenshot capture modules
│   ├── __init__.py
│   ├── page.py          # Full page capture
│   ├── element.py       # Element capture
│   └── state_capture.py # CSS-based state capture (NEW)
├── processing/          # Image processing
│   ├── __init__.py
│   ├── dedup.py         # Duplicate removal
│   ├── organize.py      # Size-based organization
│   └── verify.py        # BMP verification
├── utils/               # Utilities
│   ├── filesystem.py    # File operations
│   └── image.py         # Image utilities
└── dgus/                # DGUS preparation
    ├── __init__.py
    └── prepare.py       # Project preparation
```

## New Architecture

### External Configuration
Configuration is now loaded from JSON files in the `input/` directory:

```python
from src.config_loader import ProjectConfig

config = ProjectConfig.from_file("input/myproject.json")
print(config.resolution)  # (1024, 768)
print(config.elements)    # {"btn_move": "#btnMove", ...}
```

### Simplified State Capture
Instead of simulating button clicks and application logic:

```python
from src.capture.state_capture import StateCapture

# Just apply CSS classes and capture
capture = StateCapture(driver, config)
capture.capture_element_states(output_dir)
```

## Migration from v1.x

Old hardcoded Config class is replaced by ProjectConfig loaded from JSON.
See `input/config.json` for the new configuration format.
