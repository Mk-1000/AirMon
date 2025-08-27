#!/usr/bin/env python3
"""
AirMon - Wireless Device Manager
A cross-platform application for detecting, listing, and managing wireless devices.

Requirements:
pip install psutil pyusb pybluez bluetooth-power-manager pywin32 wmi

For Linux, you may also need:
sudo apt-get install bluetooth libbluetooth-dev
sudo pip install pybluez

For Windows:
pip install pywin32 wmi

Author: AI Assistant
Python 3.9+ required
"""

import platform
import sys
from gui import ModernWirelessDeviceGUI

def check_dependencies():
    """Check if required dependencies are available and provide installation instructions"""
    missing_deps = []
    optional_deps = []
    
    # Check for psutil
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    # Check for USB support
    try:
        import usb.core
        import usb.util
    except ImportError:
        optional_deps.append("pyusb")
    
    # Platform-specific checks
    if platform.system() == "Windows":
        try:
            import wmi
            import win32com.client
            import pythoncom
        except ImportError:
            optional_deps.extend(["wmi", "pywin32"])
    
    if platform.system() in ["Linux", "Darwin"]:
        try:
            import bluetooth
        except ImportError:
            optional_deps.append("pybluez")
    
    print("Dependency Status:")
    print("=" * 40)
    
    if missing_deps:
        print("⚠️  Missing critical dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print(f"\n📦 Install with: pip install {' '.join(missing_deps)}")
        
    if optional_deps:
        print("ℹ️  Missing optional dependencies (reduced functionality):")
        for dep in optional_deps:
            print(f"   - {dep}")
        print(f"\n📦 Install with: pip install {' '.join(optional_deps)}")
        
        if platform.system() == "Linux" and "pybluez" in optional_deps:
            print("\n🐧 For Linux, you may also need:")
            print("   sudo apt-get install bluetooth libbluetooth-dev")
        
        if platform.system() == "Windows" and "pyusb" in optional_deps:
            print("\n🪟 For Windows USB support, you may need to install libusb:")
            print("   Download from: https://libusb.info/")
    
    if not missing_deps and not optional_deps:
        print("✅ All dependencies are available!")
    
    print("\nThe application will work with fallback methods for missing optional dependencies.")
    return len(missing_deps) == 0

def show_system_info():
    """Display system information"""
    print("System Information:")
    print("=" * 40)
    print(f"Platform: {platform.system()}")
    print(f"Platform Release: {platform.release()}")
    print(f"Platform Version: {platform.version()}")
    print(f"Architecture: {platform.architecture()[0]}")
    print(f"Machine: {platform.machine()}")
    print(f"Python Version: {sys.version}")
    print("")

def main():
    """Main entry point"""
    print("AirMon - Wireless Device Manager")
    print("=" * 50)
    
    show_system_info()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("\n❌ Critical dependencies missing. Please install them and try again.")
        input("Press Enter to exit...")
        return
    
    print("")
    
    # Check for admin privileges warning
    if platform.system() == "Windows":
        print("💡 Note: Some device management operations may require administrator privileges.")
    elif platform.system() == "Linux":
        print("💡 Note: Some device management operations may require sudo privileges.")
    
    print("🚀 Starting GUI...")
    print("")
    
    try:
        # Create and run the GUI
        app = ModernWirelessDeviceGUI()
        app.run()
    
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()