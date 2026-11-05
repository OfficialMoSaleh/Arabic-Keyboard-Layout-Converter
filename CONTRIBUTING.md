# Contributing to Arabic Keyboard Layout Converter 🤝

Thank you for your interest in contributing to **Arabic Keyboard Layout Converter**! We welcome contributions from developers, designers, and translators from all around the world.

## How Can You Help?
- 🐛 **Report Bugs:** Open an issue describing the bug, steps to reproduce it, and the operating system or browser version.
- 💡 **Suggest Features:** Have an idea to make Arabic/English switching even faster? Create a Feature Request!
- 🔤 **Add Layouts / Corrections:** Improve character mappings, support additional Arabic layout variants (e.g., Arabic 102, Mac Arabic), or handle edge cases.
- 🎨 **UI / UX Improvements:** Help polish the widget and extension popup design.

## Development Setup

### 1. Windows Desktop App (`windows-app/`)
- Requires **Python 3.8+** on Windows.
- Pure standard library (`ctypes`, `tkinter`, `json`, `time`, `threading`). No third-party packages required!
- Run:
  ```powershell
  python windows-app/app.py
  ```

### 2. Chrome / Edge Extension (`chrome-extension/`)
- Manifest V3 compliant.
- No build steps or node dependencies needed!
- Load unpacked in `chrome://extensions/` with Developer Mode enabled.

### 3. Web Tool (`web-tool/`)
- Pure HTML, CSS, and Vanilla JavaScript.
- Simply open `web-tool/index.html` in any browser.

## Pull Request Guidelines
1. Fork the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/amazing-feature
   ```
2. Commit your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat: add support for Arabic 102 Mac layout"
   ```
3. Push to your branch:
   ```bash
   git push origin feature/amazing-feature
   ```
4. Open a Pull Request on GitHub.

Thank you for helping make Arabic typing effortless for everyone! ❤️
