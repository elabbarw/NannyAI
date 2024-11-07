# Installation Guide

This guide provides detailed installation instructions for the NannyAI application across different platforms.

## Prerequisites

### Windows
1. Install Python 3.11 or newer from [python.org](https://python.org)
2. Ensure Python is added to PATH during installation
3. Install Git (optional, for cloning repository)

### Linux
1. Install Python and required system packages:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.11 python3-pip python3-tk x11-apps python3-dev

# Fedora
sudo dnf install python3.11 python3-pip python3-tkinter xorg-x11-apps python3-devel
```

### macOS
1. Install Python 3.11 or newer:
   - Using Homebrew: `brew install python@3.11`
   - Or download from [python.org](https://python.org)
2. Install Xcode Command Line Tools:
```bash
xcode-select --install
```

## Installation Steps

1. **Get the Source Code**

   Option 1 - Using Git:
   ```bash
   git clone https://github.com/elabbarw/nannyai.git
   cd nannyai
   ```

   Option 2 - Download ZIP:
   - Download the repository as ZIP
   - Extract to desired location
   - Open terminal/command prompt in extracted directory

2. **Install Python Dependencies**

   ```bash
   # Create and activate virtual environment (optional but recommended)
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **First Run**

   ```bash
   python main.py
   ```

   On first run:
   1. Application creates necessary directories
   2. Initializes configuration
   3. Tests screenshot capability
   4. Opens main window

## Platform-Specific Setup

### Windows

1. **Enable Screen Capture**:
   - No additional setup needed
   - Application uses PIL ImageGrab

2. **Remote Monitoring**:
   - Install VNC viewer if needed
   - Configure Windows Defender/antivirus exceptions

### Linux

1. **X11 Setup**:
   ```bash
   # Install X11 dependencies
   sudo apt-get install python3-xlib
   
   # Allow X11 connections
   xhost +local:
   ```

2. **VNC Setup**:
   ```bash
   # Install VNC components
   sudo apt-get install vncviewer
   ```

### macOS

1. **Screen Recording Permission**:
   - System Preferences → Security & Privacy → Screen Recording
   - Enable permission for Terminal/IDE

2. **VNC Setup**:
   - Built-in VNC support
   - No additional setup needed

## Verification

1. **Test Screenshot Capability**:
   - Start application
   - Add local device
   - Try capturing screenshot
   - Check logs for errors

2. **Test AI Analysis**:
   - Configure API keys
   - Enable monitoring
   - Verify analysis results in dashboard

3. **Test Remote Monitoring** (if needed):
   - Configure VNC connection
   - Verify connection status
   - Test remote screenshot capture

## Common Installation Issues

1. **Missing Dependencies**:
   ```bash
   # Reinstall requirements
   pip install --no-cache-dir -r requirements.txt
   ```

2. **Permission Errors**:
   ```bash
   # Linux/macOS
   chmod +x main.py
   sudo chown -R $USER:$USER .
   ```

3. **API Configuration**:
   - Verify API keys in settings
   - Check API key environment variables
   - Review application logs

4. **GUI Issues**:
   ```bash
   # Linux: Install additional Tk
   sudo apt-get install python3-tk
   
   # macOS: Install Tk through brew
   brew install python-tk
   ```

## Data Directory Structure

The application creates the following directory structure:
```
data/
├── config.json       # Application configuration
├── devices.json      # Device settings
├── logs/            # Application logs
├── reports/         # Generated PDF reports
└── screenshots/     # Captured screenshots
    └── history.json # Screenshot metadata
```

## Updating

1. **Backup Data**:
   - Copy `data` directory
   - Export configuration if needed

2. **Update Code**:
   ```bash
   git pull  # If using Git
   ```
   Or download and extract new version

3. **Update Dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

## Support

For installation support:
1. Check application logs in `data/logs/`
2. Review troubleshooting guide in README
3. Submit issue with:
   - Error messages
   - System information
   - Installation method used
