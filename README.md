# NannyAI

A Python-based desktop application for monitoring screen content and alerting parents about potentially harmful material across multiple connected devices. This application provides real-time content monitoring with AI-powered analysis to help parents ensure their children's online safety.

## Features

- **Cross-Platform GUI Interface**: User-friendly interface for managing monitoring settings and viewing alerts
- **Automated Screenshot Capture**: Configurable interval-based screen capture across multiple devices
- **AI-Powered Content Analysis**: 
  - Multiple AI model support (OpenAI Vision, Google Gemini)
  - Configurable content categories and thresholds
  - Detection of inappropriate content including violence, adult content, hate speech, and drug-related material
- **Multi-Device Support**: 
  - Local and remote device monitoring via VNC
  - Device-specific monitoring preferences
  - Real-time device status tracking
- **Comprehensive Dashboard**:
  - Screenshot history viewing
  - Content analysis details
  - Paginated history view
- **Detailed Reporting**:
  - PDF report generation
  - Activity summaries and trends
  - Customizable date ranges
  - Device-specific filtering
- **Security Features**:
  - Secure API key storage
  - Configurable notification system
  - Parent email alerts

## Requirements

### System Requirements
- Python 3.11 or newer
- X11 (for Linux systems)
- System dependencies (automatically installed):
  - Tkinter for GUI
  - Pillow for image processing
  - VNC libraries for remote monitoring

### API Requirements
- OpenAI API key (for GPT-4 Vision analysis)
- Google Gemini API key (alternative vision model)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/elabbarw/nannyai.git
cd nannyai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Configuration

### General Settings
- Screenshot interval (default: 30 seconds)
- Vision provider selection (OpenAI/Gemini)
- Content detection thresholds
- Monitored categories

### Device Management
1. Open "Manage Devices" from the main window
2. Add local or remote devices:
   - For local monitoring: Simply add device name
   - For remote monitoring: Configure VNC connection details

### Email Notifications
1. Open Settings
2. Navigate to Email tab
3. Configure SMTP settings:
   - Server (default: smtp.gmail.com)
   - Port (default: 587)
   - Sender email and password
   - Parent notification email

## Usage

1. **Start Monitoring**:
   - Click "Start All Monitoring" to begin screenshot capture
   - Individual devices can be started/stopped from Device Management

2. **View Dashboard**:
   - Switch to Dashboard tab
   - Browse screenshot history
   - View analysis details for each capture

3. **Generate Reports**:
   - Select date range and device
   - Click "Generate Report"
   - View or save the generated PDF

## Troubleshooting

### Common Issues

1. **Screenshot Capture Fails**:
   - Verify correct permissions for screen capture
   - On Linux: Ensure X11 is running
   - Check device status in Device Management

2. **VNC Connection Issues**:
   - Verify network connectivity
   - Check VNC server status
   - Confirm correct password and port

3. **API Authentication Errors**:
   - Verify API keys are correctly configured
   - Check for sufficient API credits
   - Ensure selected models are available

4. **Email Notifications**:
   - Verify SMTP settings
   - For Gmail: Enable "Less secure app access"
   - Check spam folder for alerts

### Debug Mode

Enable Debug Mode from the main window to:
- View detailed logging
- Monitor backend operations
- Identify configuration issues

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## Support

For support, please:
1. Check the troubleshooting guide
2. Search existing issues
3. Create a new issue with:
   - Detailed problem description
   - Steps to reproduce
   - System information
