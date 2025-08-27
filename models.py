#!/usr/bin/env python3
"""
Data models for wireless device management
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum

# Device types enumeration
class DeviceType(Enum):
    BLUETOOTH = "Bluetooth"
    RF_DONGLE = "RF Dongle"
    WIFI_ADAPTER = "WiFi Adapter"
    WIRELESS_AUDIO = "Wireless Audio"
    UNKNOWN_WIRELESS = "Unknown Wireless"

# Device status enumeration
class DeviceStatus(Enum):
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    PAIRED = "Paired"
    DISCOVERABLE = "Discoverable"
    ENABLED = "Enabled"
    DISABLED = "Disabled"
    UNKNOWN = "Unknown"

@dataclass
class WirelessDevice:
    """Data class representing a wireless device"""
    name: str
    device_type: DeviceType
    interface: str
    mac_address: Optional[str] = None
    status: DeviceStatus = DeviceStatus.UNKNOWN
    vendor_id: Optional[str] = None
    product_id: Optional[str] = None
    battery_level: Optional[int] = None
    signal_strength: Optional[int] = None
    additional_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}

@dataclass
class SystemInfo:
    """System information data class"""
    platform: str
    platform_version: str
    architecture: str
    battery_percentage: Optional[int] = None
    battery_plugged: bool = False
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    network_interfaces: List[str] = None
    
    def __post_init__(self):
        if self.network_interfaces is None:
            self.network_interfaces = []
