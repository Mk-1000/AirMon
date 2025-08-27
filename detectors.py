#!/usr/bin/env python3
"""
Wireless device detectors for different platforms and device types
"""

import platform
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import List, Optional

# Platform-specific imports
try:
    import psutil
except ImportError:
    psutil = None

try:
    import usb.core
    import usb.util
    import usb.backend.libusb1
    import usb.backend.openusb
    import usb.backend.libusb0
except ImportError:
    usb = None

# Windows-specific imports
if platform.system() == "Windows":
    try:
        import wmi
        import win32com.client
        import pythoncom
    except ImportError:
        wmi = None
        win32com = None
        pythoncom = None

# Linux/Unix-specific imports
if platform.system() in ["Linux", "Darwin"]:
    try:
        import bluetooth
    except ImportError:
        bluetooth = None

from models import WirelessDevice, DeviceType, DeviceStatus

class WirelessDetector(ABC):
    """Abstract base class for wireless device detectors"""
    
    @abstractmethod
    def detect_devices(self) -> List[WirelessDevice]:
        """Detect and return list of wireless devices"""
        pass
    
    @abstractmethod
    def can_manage_device(self, device: WirelessDevice) -> bool:
        """Check if the detector can manage the given device"""
        pass
    
    @abstractmethod
    def enable_device(self, device: WirelessDevice) -> bool:
        """Enable the given device"""
        pass
    
    @abstractmethod
    def disable_device(self, device: WirelessDevice) -> bool:
        """Disable the given device"""
        pass

class BluetoothDetector(WirelessDetector):
    """Bluetooth device detector"""
    
    def detect_devices(self) -> List[WirelessDevice]:
        devices = []
        
        if platform.system() == "Windows":
            devices.extend(self._detect_windows_bluetooth())
        elif platform.system() == "Linux":
            devices.extend(self._detect_linux_bluetooth())
        elif platform.system() == "Darwin":
            devices.extend(self._detect_macos_bluetooth())
        
        return devices
    
    def _detect_windows_bluetooth(self) -> List[WirelessDevice]:
        devices = []
        if not wmi or not pythoncom:
            return devices
        
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            
            c = wmi.WMI()
            # Get Bluetooth devices
            for device in c.Win32_PnPEntity():
                if device.Name and "bluetooth" in device.Name.lower():
                    status = DeviceStatus.ENABLED if device.Status == "OK" else DeviceStatus.DISABLED
                    devices.append(WirelessDevice(
                        name=device.Name,
                        device_type=DeviceType.BLUETOOTH,
                        interface="Bluetooth",
                        status=status,
                        additional_info={
                            "device_id": device.DeviceID,
                            "manufacturer": device.Manufacturer
                        }
                    ))
        except Exception as e:
            print(f"Error detecting Windows Bluetooth devices: {e}")
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass
        
        return devices
    
    def _detect_linux_bluetooth(self) -> List[WirelessDevice]:
        devices = []
        
        try:
            # Try using bluetoothctl command
            result = subprocess.run(['bluetoothctl', 'list'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip().startswith('Controller'):
                        parts = line.split()
                        if len(parts) >= 3:
                            mac = parts[1]
                            name = ' '.join(parts[2:])
                            devices.append(WirelessDevice(
                                name=name,
                                device_type=DeviceType.BLUETOOTH,
                                interface="Bluetooth Controller",
                                mac_address=mac,
                                status=DeviceStatus.ENABLED
                            ))
            
            # Try to get paired devices
            result = subprocess.run(['bluetoothctl', 'paired-devices'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip().startswith('Device'):
                        parts = line.split()
                        if len(parts) >= 3:
                            mac = parts[1]
                            name = ' '.join(parts[2:])
                            devices.append(WirelessDevice(
                                name=name,
                                device_type=DeviceType.BLUETOOTH,
                                interface="Bluetooth Device",
                                mac_address=mac,
                                status=DeviceStatus.PAIRED
                            ))
        
        except Exception as e:
            print(f"Error detecting Linux Bluetooth devices: {e}")
        
        return devices
    
    def _detect_macos_bluetooth(self) -> List[WirelessDevice]:
        devices = []
        
        try:
            # Use system_profiler to get Bluetooth info
            result = subprocess.run(['system_profiler', 'SPBluetoothDataType'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse the output (simplified parsing)
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'Address:' in line:
                        mac = line.split(':')[1].strip()
                        # Look for device name in previous lines
                        name = "Bluetooth Device"
                        for j in range(max(0, i-5), i):
                            if lines[j].strip() and ':' not in lines[j]:
                                name = lines[j].strip()
                                break
                        
                        devices.append(WirelessDevice(
                            name=name,
                            device_type=DeviceType.BLUETOOTH,
                            interface="Bluetooth",
                            mac_address=mac,
                            status=DeviceStatus.CONNECTED
                        ))
        
        except Exception as e:
            print(f"Error detecting macOS Bluetooth devices: {e}")
        
        return devices
    
    def can_manage_device(self, device: WirelessDevice) -> bool:
        return device.device_type == DeviceType.BLUETOOTH
    
    def enable_device(self, device: WirelessDevice) -> bool:
        # Implementation would depend on platform and specific device
        # This is a simplified version
        try:
            if platform.system() == "Linux":
                subprocess.run(['bluetoothctl', 'power', 'on'], 
                             capture_output=True, timeout=5)
                return True
        except Exception:
            pass
        return False
    
    def disable_device(self, device: WirelessDevice) -> bool:
        try:
            if platform.system() == "Linux":
                subprocess.run(['bluetoothctl', 'power', 'off'], 
                             capture_output=True, timeout=5)
                return True
        except Exception:
            pass
        return False

class USBWirelessDetector(WirelessDetector):
    """USB-based wireless device detector (dongles, adapters)"""
    
    # Known wireless device vendor IDs
    WIRELESS_VENDORS = {
        0x046d: "Logitech",  # Logitech wireless devices
        0x045e: "Microsoft", # Microsoft wireless devices
        0x1532: "Razer",     # Razer wireless devices
        0x0b05: "ASUS",      # ASUS wireless adapters
        0x0bda: "Realtek",   # Realtek wireless adapters
        0x148f: "Ralink",    # Ralink wireless adapters
        0x0cf3: "Atheros",   # Atheros wireless adapters
        0x8087: "Intel",     # Intel wireless adapters
    }
    
    def __init__(self):
        self.backend = None
        self._initialize_backend()
    
    def _initialize_backend(self):
        """Initialize USB backend"""
        if not usb:
            return
        
        # Try different backends in order of preference
        backends = [
            usb.backend.libusb1.get_backend,
            usb.backend.libusb0.get_backend,
            usb.backend.openusb.get_backend,
        ]
        
        for get_backend in backends:
            try:
                backend = get_backend()
                if backend is not None:
                    self.backend = backend
                    print(f"Using USB backend: {backend.__class__.__name__}")
                    break
            except Exception as e:
                continue
        
        if self.backend is None:
            print("No USB backend available. USB device detection will be limited.")
    
    def detect_devices(self) -> List[WirelessDevice]:
        devices = []
        
        if not usb or self.backend is None:
            # Fallback to system commands
            return self._detect_devices_fallback()
        
        try:
            # Find USB devices using the backend
            usb_devices = usb.core.find(find_all=True, backend=self.backend)
            
            for device in usb_devices:
                if self._is_wireless_device(device):
                    device_info = self._get_device_info(device)
                    devices.append(device_info)
        
        except Exception as e:
            print(f"Error detecting USB wireless devices: {e}")
            # Try fallback method
            return self._detect_devices_fallback()
        
        return devices
    
    def _detect_devices_fallback(self) -> List[WirelessDevice]:
        """Fallback method using system commands"""
        devices = []
        
        try:
            if platform.system() == "Windows":
                devices.extend(self._detect_windows_usb_fallback())
            elif platform.system() == "Linux":
                devices.extend(self._detect_linux_usb_fallback())
            elif platform.system() == "Darwin":
                devices.extend(self._detect_macos_usb_fallback())
        except Exception as e:
            print(f"Error in USB fallback detection: {e}")
        
        return devices
    
    def _detect_windows_usb_fallback(self) -> List[WirelessDevice]:
        """Windows USB detection using WMI"""
        devices = []
        if not wmi or not pythoncom:
            return devices
        
        try:
            pythoncom.CoInitialize()
            c = wmi.WMI()
            
            for device in c.Win32_USBControllerDevice():
                dependent = device.Dependent
                if dependent and hasattr(dependent, 'Name'):
                    name = dependent.Name
                    if name and any(term in name.lower() for term in ['wireless', 'wifi', 'bluetooth', 'dongle']):
                        devices.append(WirelessDevice(
                            name=name,
                            device_type=self._classify_device_by_name(name),
                            interface="USB",
                            status=DeviceStatus.CONNECTED,
                            additional_info={"detection_method": "WMI"}
                        ))
        except Exception as e:
            print(f"Windows USB fallback error: {e}")
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass
        
        return devices
    
    def _detect_linux_usb_fallback(self) -> List[WirelessDevice]:
        """Linux USB detection using lsusb"""
        devices = []
        
        try:
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        # Parse lsusb output
                        parts = line.split()
                        if len(parts) >= 6:
                            device_info = ' '.join(parts[6:])
                            if any(term in device_info.lower() for term in ['wireless', 'wifi', 'bluetooth', 'dongle']):
                                # Extract vendor:product ID
                                id_part = parts[5]  # Format: vendor_id:product_id
                                vendor_id, product_id = id_part.split(':')
                                
                                devices.append(WirelessDevice(
                                    name=device_info,
                                    device_type=self._classify_device_by_name(device_info),
                                    interface=f"USB (Bus {parts[1]}, Device {parts[3].rstrip(':')})",
                                    vendor_id=vendor_id,
                                    product_id=product_id,
                                    status=DeviceStatus.CONNECTED,
                                    additional_info={"detection_method": "lsusb"}
                                ))
        except Exception as e:
            print(f"Linux USB fallback error: {e}")
        
        return devices
    
    def _detect_macos_usb_fallback(self) -> List[WirelessDevice]:
        """macOS USB detection using system_profiler"""
        devices = []
        
        try:
            result = subprocess.run(['system_profiler', 'SPUSBDataType'], 
                                  capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                current_device = None
                
                for line in lines:
                    line = line.strip()
                    if line.endswith(':') and not line.startswith(' '):
                        # This is a device name
                        device_name = line[:-1]
                        if any(term in device_name.lower() for term in ['wireless', 'wifi', 'bluetooth', 'dongle']):
                            current_device = {
                                'name': device_name,
                                'type': self._classify_device_by_name(device_name)
                            }
                    elif current_device and 'Product ID:' in line:
                        current_device['product_id'] = line.split(':')[1].strip()
                    elif current_device and 'Vendor ID:' in line:
                        current_device['vendor_id'] = line.split(':')[1].strip()
                        # Add the device when we have enough info
                        devices.append(WirelessDevice(
                            name=current_device['name'],
                            device_type=current_device['type'],
                            interface="USB",
                            vendor_id=current_device.get('vendor_id'),
                            product_id=current_device.get('product_id'),
                            status=DeviceStatus.CONNECTED,
                            additional_info={"detection_method": "system_profiler"}
                        ))
                        current_device = None
        except Exception as e:
            print(f"macOS USB fallback error: {e}")
        
        return devices
    
    def _classify_device_by_name(self, name: str) -> DeviceType:
        """Classify device based on name"""
        name_lower = name.lower()
        
        if any(term in name_lower for term in ['receiver', 'dongle', 'unifying']):
            return DeviceType.RF_DONGLE
        elif any(term in name_lower for term in ['wifi', 'wireless lan', '802.11', 'wlan']):
            return DeviceType.WIFI_ADAPTER
        elif any(term in name_lower for term in ['bluetooth']):
            return DeviceType.BLUETOOTH
        elif any(term in name_lower for term in ['audio', 'headset', 'speaker', 'microphone']):
            return DeviceType.WIRELESS_AUDIO
        else:
            return DeviceType.UNKNOWN_WIRELESS
    
    def _is_wireless_device(self, device) -> bool:
        """Check if USB device is likely a wireless device"""
        try:
            # Check vendor ID
            if device.idVendor in self.WIRELESS_VENDORS:
                return True
            
            # Check device class (some wireless devices use HID class)
            if hasattr(device, 'bDeviceClass'):
                # Class 9 is Hub, Class 3 is HID (keyboards/mice)
                if device.bDeviceClass in [3, 9]:
                    return True
            
            # Check interface class
            try:
                for cfg in device:
                    for intf in cfg:
                        if intf.bInterfaceClass in [3, 224]:  # HID or Wireless
                            return True
            except:
                pass
            
        except Exception:
            pass
        
        return False
    
    def _get_device_info(self, device) -> WirelessDevice:
        """Extract device information"""
        try:
            vendor_name = self.WIRELESS_VENDORS.get(device.idVendor, "Unknown")
            
            # Try to get product name
            try:
                product_name = usb.util.get_string(device, device.iProduct)
            except:
                product_name = f"USB Device {device.idVendor:04x}:{device.idProduct:04x}"
            
            # Determine device type based on product name or vendor
            device_type = self._classify_device(product_name, vendor_name)
            
            return WirelessDevice(
                name=f"{vendor_name} {product_name}",
                device_type=device_type,
                interface=f"USB (Bus {device.bus}, Device {device.address})",
                vendor_id=f"{device.idVendor:04x}",
                product_id=f"{device.idProduct:04x}",
                status=DeviceStatus.CONNECTED,
                additional_info={
                    "bus": device.bus,
                    "address": device.address,
                    "vendor_name": vendor_name,
                    "detection_method": "pyusb"
                }
            )
        
        except Exception as e:
            return WirelessDevice(
                name="Unknown USB Wireless Device",
                device_type=DeviceType.UNKNOWN_WIRELESS,
                interface="USB",
                status=DeviceStatus.UNKNOWN,
                additional_info={"error": str(e)}
            )
    
    def _classify_device(self, product_name: str, vendor_name: str) -> DeviceType:
        """Classify device based on name and vendor"""
        product_lower = product_name.lower()
        vendor_lower = vendor_name.lower()
        
        if any(term in product_lower for term in ['receiver', 'dongle', 'unifying']):
            return DeviceType.RF_DONGLE
        elif any(term in product_lower for term in ['wifi', 'wireless lan', '802.11', 'wlan']):
            return DeviceType.WIFI_ADAPTER
        elif any(term in product_lower for term in ['audio', 'headset', 'speaker', 'microphone']):
            return DeviceType.WIRELESS_AUDIO
        else:
            return DeviceType.RF_DONGLE  # Assume RF dongle for most wireless USB devices
    
    def can_manage_device(self, device: WirelessDevice) -> bool:
        return device.device_type in [DeviceType.RF_DONGLE, DeviceType.WIFI_ADAPTER]
    
    def enable_device(self, device: WirelessDevice) -> bool:
        # USB devices are typically managed by the OS
        # This would require platform-specific implementation
        return False
    
    def disable_device(self, device: WirelessDevice) -> bool:
        # USB devices are typically managed by the OS
        # This would require platform-specific implementation
        return False

class NetworkWirelessDetector(WirelessDetector):
    """Network interface wireless detector"""
    
    def detect_devices(self) -> List[WirelessDevice]:
        devices = []
        
        if not psutil:
            return self._detect_network_fallback()
        
        try:
            # Get network interfaces
            interfaces = psutil.net_if_addrs()
            interface_stats = psutil.net_if_stats()
            
            for interface_name, addresses in interfaces.items():
                if self._is_wireless_interface(interface_name):
                    device_info = self._get_interface_info(interface_name, addresses, interface_stats)
                    devices.append(device_info)
        
        except Exception as e:
            print(f"Error detecting network wireless devices: {e}")
            return self._detect_network_fallback()
        
        return devices
    
    def _detect_network_fallback(self) -> List[WirelessDevice]:
        """Fallback network detection using system commands"""
        devices = []
        
        try:
            if platform.system() == "Linux":
                devices.extend(self._detect_linux_network_fallback())
            elif platform.system() == "Windows":
                devices.extend(self._detect_windows_network_fallback())
            elif platform.system() == "Darwin":
                devices.extend(self._detect_macos_network_fallback())
        except Exception as e:
            print(f"Network fallback detection error: {e}")
        
        return devices
    
    def _detect_linux_network_fallback(self) -> List[WirelessDevice]:
        """Linux network detection fallback"""
        devices = []
        
        try:
            # Try iwconfig
            result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'IEEE 802.11' in line:
                        interface_name = line.split()[0]
                        devices.append(WirelessDevice(
                            name=f"Wireless Interface {interface_name}",
                            device_type=DeviceType.WIFI_ADAPTER,
                            interface=interface_name,
                            status=DeviceStatus.ENABLED,
                            additional_info={"detection_method": "iwconfig"}
                        ))
        except Exception as e:
            print(f"Linux network fallback error: {e}")
        
        return devices
    
    def _detect_windows_network_fallback(self) -> List[WirelessDevice]:
        """Windows network detection fallback"""
        devices = []
        
        try:
            result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                current_interface = None
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('Name'):
                        interface_name = line.split(':', 1)[1].strip()
                        current_interface = {
                            'name': interface_name,
                            'status': DeviceStatus.UNKNOWN
                        }
                    elif current_interface and line.startswith('State'):
                        state = line.split(':', 1)[1].strip().lower()
                        current_interface['status'] = DeviceStatus.ENABLED if 'connected' in state else DeviceStatus.DISABLED
                        
                        devices.append(WirelessDevice(
                            name=f"Wireless Interface {current_interface['name']}",
                            device_type=DeviceType.WIFI_ADAPTER,
                            interface=current_interface['name'],
                            status=current_interface['status'],
                            additional_info={"detection_method": "netsh"}
                        ))
                        current_interface = None
        except Exception as e:
            print(f"Windows network fallback error: {e}")
        
        return devices
    
    def _detect_macos_network_fallback(self) -> List[WirelessDevice]:
        """macOS network detection fallback"""
        devices = []
        
        try:
            result = subprocess.run(['networksetup', '-listallhardwareports'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                current_port = None
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('Hardware Port:'):
                        port_name = line.split(':', 1)[1].strip()
                        if 'wi-fi' in port_name.lower() or 'wireless' in port_name.lower():
                            current_port = {'name': port_name}
                    elif current_port and line.startswith('Device:'):
                        device_name = line.split(':', 1)[1].strip()
                        devices.append(WirelessDevice(
                            name=f"Wireless Interface {current_port['name']}",
                            device_type=DeviceType.WIFI_ADAPTER,
                            interface=device_name,
                            status=DeviceStatus.ENABLED,
                            additional_info={"detection_method": "networksetup"}
                        ))
                        current_port = None
        except Exception as e:
            print(f"macOS network fallback error: {e}")
        
        return devices
    
    def _is_wireless_interface(self, interface_name: str) -> bool:
        """Check if interface is wireless"""
        wireless_indicators = ['wlan', 'wifi', 'wl', 'ath', 'ra', 'wireless']
        name_lower = interface_name.lower()
        
        return any(indicator in name_lower for indicator in wireless_indicators)
    
    def _get_interface_info(self, interface_name: str, addresses, interface_stats) -> WirelessDevice:
        """Get information about wireless interface"""
        mac_address = None
        
        # Find MAC address
        for addr in addresses:
            if hasattr(addr.family, 'name') and addr.family.name == 'AF_PACKET':
                mac_address = addr.address
                break
            elif addr.family == 17:  # MAC address family number
                mac_address = addr.address
                break
        
        # Get interface status
        status = DeviceStatus.UNKNOWN
        if interface_name in interface_stats:
            stats = interface_stats[interface_name]
            status = DeviceStatus.ENABLED if stats.isup else DeviceStatus.DISABLED
        
        return WirelessDevice(
            name=f"Wireless Interface {interface_name}",
            device_type=DeviceType.WIFI_ADAPTER,
            interface=interface_name,
            mac_address=mac_address,
            status=status,
            additional_info={
                "interface_name": interface_name,
                "addresses": len(addresses),
                "detection_method": "psutil"
            }
        )
    
    def can_manage_device(self, device: WirelessDevice) -> bool:
        return device.device_type == DeviceType.WIFI_ADAPTER
    
    def enable_device(self, device: WirelessDevice) -> bool:
        try:
            interface_name = device.additional_info.get("interface_name", device.interface)
            
            if platform.system() == "Linux":
                subprocess.run(['ip', 'link', 'set', interface_name, 'up'], 
                             capture_output=True, timeout=5)
                return True
            elif platform.system() == "Windows":
                # Windows interface management would require admin privileges
                subprocess.run(['netsh', 'interface', 'set', 'interface', interface_name, 'enabled'], 
                             capture_output=True, timeout=5)
                return True
        except Exception:
            pass
        return False
    
    def disable_device(self, device: WirelessDevice) -> bool:
        try:
            interface_name = device.additional_info.get("interface_name", device.interface)
            
            if platform.system() == "Linux":
                subprocess.run(['ip', 'link', 'set', interface_name, 'down'], 
                             capture_output=True, timeout=5)
                return True
            elif platform.system() == "Windows":
                subprocess.run(['netsh', 'interface', 'set', 'interface', interface_name, 'disabled'], 
                             capture_output=True, timeout=5)
                return True
        except Exception:
            pass
        return False
