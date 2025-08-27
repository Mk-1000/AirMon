#!/usr/bin/env python3
"""
Main device manager that coordinates all wireless device detectors
"""

from typing import List, Optional
from models import WirelessDevice, DeviceType, DeviceStatus
from detectors import BluetoothDetector, USBWirelessDetector, NetworkWirelessDetector

class WirelessDeviceManager:
    """Main manager class that coordinates all detectors"""
    
    def __init__(self):
        self.detectors = [
            BluetoothDetector(),
            USBWirelessDetector(),
            NetworkWirelessDetector()
        ]
        self.devices: List[WirelessDevice] = []
        self._scan_callbacks = []
    
    def add_scan_callback(self, callback):
        """Add a callback to be called when devices are scanned"""
        self._scan_callbacks.append(callback)
    
    def scan_devices(self) -> List[WirelessDevice]:
        """Scan for all wireless devices using all detectors"""
        self.devices = []
        
        for detector in self.detectors:
            try:
                detected_devices = detector.detect_devices()
                self.devices.extend(detected_devices)
            except Exception as e:
                print(f"Error with detector {detector.__class__.__name__}: {e}")
        
        # Notify callbacks
        for callback in self._scan_callbacks:
            try:
                callback(self.devices)
            except Exception as e:
                print(f"Error in scan callback: {e}")
        
        return self.devices
    
    def get_devices_by_type(self, device_type: DeviceType) -> List[WirelessDevice]:
        """Get devices filtered by type"""
        return [device for device in self.devices if device.device_type == device_type]
    
    def get_devices_by_status(self, status: DeviceStatus) -> List[WirelessDevice]:
        """Get devices filtered by status"""
        return [device for device in self.devices if device.status == status]
    
    def get_device_by_name(self, name: str) -> Optional[WirelessDevice]:
        """Get a specific device by name"""
        for device in self.devices:
            if device.name == name:
                return device
        return None
    
    def get_device_by_mac(self, mac_address: str) -> Optional[WirelessDevice]:
        """Get a specific device by MAC address"""
        for device in self.devices:
            if device.mac_address == mac_address:
                return device
        return None
    
    def enable_device(self, device: WirelessDevice) -> bool:
        """Enable a device using the appropriate detector"""
        for detector in self.detectors:
            if detector.can_manage_device(device):
                success = detector.enable_device(device)
                if success:
                    # Update device status
                    device.status = DeviceStatus.ENABLED
                return success
        return False
    
    def disable_device(self, device: WirelessDevice) -> bool:
        """Disable a device using the appropriate detector"""
        for detector in self.detectors:
            if detector.can_manage_device(device):
                success = detector.disable_device(device)
                if success:
                    # Update device status
                    device.status = DeviceStatus.DISABLED
                return success
        return False
    
    def can_manage_device(self, device: WirelessDevice) -> bool:
        """Check if any detector can manage the given device"""
        return any(detector.can_manage_device(device) for detector in self.detectors)
    
    def get_manageable_devices(self) -> List[WirelessDevice]:
        """Get all devices that can be managed"""
        return [device for device in self.devices if self.can_manage_device(device)]
    
    def get_device_statistics(self) -> dict:
        """Get statistics about detected devices"""
        stats = {
            'total_devices': len(self.devices),
            'by_type': {},
            'by_status': {},
            'manageable': len(self.get_manageable_devices())
        }
        
        # Count by type
        for device_type in DeviceType:
            count = len(self.get_devices_by_type(device_type))
            if count > 0:
                stats['by_type'][device_type.value] = count
        
        # Count by status
        for status in DeviceStatus:
            count = len(self.get_devices_by_status(status))
            if count > 0:
                stats['by_status'][status.value] = count
        
        return stats
    
    def refresh_device_status(self, device: WirelessDevice) -> bool:
        """Refresh the status of a specific device"""
        # This would require re-scanning or checking the device status
        # For now, we'll just re-scan all devices
        return self.scan_devices()
    
    def get_device_detector(self, device: WirelessDevice):
        """Get the detector that can manage the given device"""
        for detector in self.detectors:
            if detector.can_manage_device(device):
                return detector
        return None
