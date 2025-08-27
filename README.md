# AirMon - Wireless Device Manager

A comprehensive cross-platform application for detecting, monitoring, and managing wireless devices including Bluetooth, WiFi adapters, RF dongles, and other wireless peripherals.

## Features

### 🔍 Device Detection
- **Bluetooth Devices**: Controllers, paired devices, audio devices
- **WiFi Adapters**: Wireless network interfaces and adapters
- **RF Dongles**: Wireless receivers, Logitech Unifying receivers, gaming dongles
- **USB Wireless Devices**: Various wireless USB peripherals
- **Wireless Audio**: Headsets, speakers, microphones

### 📊 System Monitoring
- **Battery Monitoring**: Real-time battery percentage and status
- **CPU Usage**: Current CPU utilization
- **Memory Usage**: RAM usage statistics
- **Network Interfaces**: Active network connections
- **Platform Information**: System details and architecture

### 🎛️ Device Management
- **Enable/Disable Devices**: Control device power states
- **Status Monitoring**: Real-time device status updates
- **Device Information**: Detailed device specifications
- **Management Capabilities**: Platform-specific device control

### 🖥️ Modern GUI
- **Tabbed Interface**: Organized device and system views
- **Real-time Updates**: Auto-refresh capabilities
- **Device Filtering**: Filter by type and status
- **Context Menus**: Right-click device management
- **Progress Indicators**: Visual feedback for operations

## Installation

### Prerequisites
- Python 3.9 or higher
- Administrator/sudo privileges (for device management features)

### Quick Install

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/AirMon.git
   cd AirMon
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

### Platform-Specific Setup

#### Windows
```bash
# Install Windows-specific dependencies
pip install pywin32 wmi

# Optional: Install libusb for enhanced USB support
# Download from: https://libusb.info/
```

#### Linux
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install bluetooth libbluetooth-dev

# Install Python dependencies
pip install pybluez
```

#### macOS
```bash
# Install system dependencies (if needed)
brew install bluetooth

# Install Python dependencies
pip install pybluez
```

## Usage

### Starting the Application
```bash
python main.py
```

The application will:
1. Check system dependencies
2. Display system information
3. Launch the GUI interface

### GUI Features

#### Device Tab
- **Scan Devices**: Manually scan for wireless devices
- **Auto Refresh**: Enable automatic device scanning
- **Enable/Disable**: Control device power states
- **Device Information**: View detailed device specs
- **Filters**: Filter devices by type and status

#### System Monitoring
- **Battery Status**: Real-time battery percentage
- **CPU Usage**: Current processor utilization
- **Memory Usage**: RAM usage statistics
- **Platform Info**: System details

### Device Management

#### Supported Device Types
- **Bluetooth**: Controllers, audio devices, peripherals
- **WiFi Adapters**: Wireless network interfaces
- **RF Dongles**: Wireless receivers and transmitters
- **USB Wireless**: Various wireless USB devices

#### Management Operations
- **Enable Device**: Power on wireless devices
- **Disable Device**: Power off wireless devices
- **Status Check**: Verify device connectivity
- **Information Display**: Show device specifications

## File Structure

```
AirMon/
├── main.py              # Main application entry point
├── models.py            # Data models and enums
├── detectors.py         # Device detection classes
├── device_manager.py    # Device management coordination
├── system_monitor.py    # System monitoring utilities
├── gui.py              # Modern GUI interface
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Technical Details

### Architecture
- **Modular Design**: Separated concerns across multiple files
- **Platform Abstraction**: Cross-platform compatibility
- **Threading**: Non-blocking GUI with background operations
- **Error Handling**: Graceful fallbacks for missing dependencies

### Device Detection Methods
- **Windows**: WMI, Device Manager integration
- **Linux**: bluetoothctl, lsusb, iwconfig
- **macOS**: system_profiler, networksetup
- **Fallback Methods**: Command-line tools and system APIs

### System Monitoring
- **Battery**: Platform-specific battery APIs
- **CPU/Memory**: psutil library integration
- **Network**: Interface and connection monitoring
- **Real-time Updates**: Background monitoring threads

## Troubleshooting

### Common Issues

#### "No devices found"
- Ensure wireless devices are connected
- Check if devices are powered on
- Verify administrator privileges
- Try manual scan button

#### "Cannot manage device"
- Some devices require administrator privileges
- Not all devices support software management
- Check device-specific requirements

#### "Dependencies missing"
- Install required packages: `pip install -r requirements.txt`
- Platform-specific setup may be required
- Check installation instructions above

#### "Permission denied"
- Run as administrator (Windows)
- Use sudo (Linux/macOS)
- Check device permissions

### Debug Mode
Run with verbose output:
```bash
python main.py --debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **psutil**: System monitoring capabilities
- **pyusb**: USB device detection
- **pybluez**: Bluetooth device management
- **tkinter**: GUI framework

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review platform-specific setup instructions

---

**AirMon** - Making wireless device management simple and efficient across all platforms.