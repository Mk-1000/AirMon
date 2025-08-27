#!/usr/bin/env python3
"""
System monitoring utilities for battery, CPU, memory, and network information
"""

import platform
import subprocess
import threading
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Platform-specific imports
try:
    import psutil
except ImportError:
    psutil = None

from models import SystemInfo

class SystemMonitor:
    """System monitoring class for battery, CPU, memory, and network information"""
    
    def __init__(self):
        self._battery_info = {}
        self._system_info = None
        self._monitoring = False
        self._monitor_thread = None
        self._callbacks = []
    
    def start_monitoring(self, callback=None, interval=2.0):
        """Start system monitoring in background thread"""
        if self._monitoring:
            return
        
        if callback:
            self._callbacks.append(callback)
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None
    
    def _monitor_loop(self, interval):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                system_info = self.get_system_info()
                battery_info = self.get_battery_info()
                
                # Update cached info
                self._system_info = system_info
                self._battery_info = battery_info
                
                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(system_info, battery_info)
                    except Exception as e:
                        print(f"Error in system monitor callback: {e}")
                
                time.sleep(interval)
            except Exception as e:
                print(f"Error in system monitoring: {e}")
                time.sleep(interval)
    
    def get_system_info(self) -> SystemInfo:
        """Get current system information"""
        try:
            # Basic system info
            platform_name = platform.system()
            platform_version = platform.platform()
            architecture = platform.architecture()[0]
            
            # CPU and memory usage
            cpu_usage = 0.0
            memory_usage = 0.0
            
            if psutil:
                cpu_usage = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                memory_usage = memory.percent
            
            # Network interfaces
            network_interfaces = []
            if psutil:
                try:
                    interfaces = psutil.net_if_addrs()
                    network_interfaces = list(interfaces.keys())
                except:
                    pass
            
            # Battery information
            battery_percentage = None
            battery_plugged = False
            
            if psutil and hasattr(psutil, 'sensors_battery'):
                try:
                    battery = psutil.sensors_battery()
                    if battery:
                        battery_percentage = int(battery.percent)
                        battery_plugged = battery.power_plugged
                except:
                    pass
            
            # Fallback battery detection for different platforms
            if battery_percentage is None:
                battery_info = self.get_battery_info()
                battery_percentage = battery_info.get('percentage')
                battery_plugged = battery_info.get('plugged', False)
            
            return SystemInfo(
                platform=platform_name,
                platform_version=platform_version,
                architecture=architecture,
                battery_percentage=battery_percentage,
                battery_plugged=battery_plugged,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                network_interfaces=network_interfaces
            )
        
        except Exception as e:
            print(f"Error getting system info: {e}")
            return SystemInfo(
                platform=platform.system(),
                platform_version=platform.platform(),
                architecture=platform.architecture()[0] if platform.architecture() else "Unknown"
            )
    
    def get_battery_info(self) -> Dict[str, Any]:
        """Get detailed battery information"""
        battery_info = {
            'percentage': None,
            'plugged': False,
            'time_left': None,
            'power_consumption': None,
            'temperature': None,
            'health': None
        }
        
        try:
            if psutil and hasattr(psutil, 'sensors_battery'):
                battery = psutil.sensors_battery()
                if battery:
                    battery_info['percentage'] = int(battery.percent)
                    battery_info['plugged'] = battery.power_plugged
                    if battery.secsleft != -1:
                        battery_info['time_left'] = battery.secsleft
            
            # Platform-specific battery detection
            if platform.system() == "Windows":
                battery_info.update(self._get_windows_battery_info())
            elif platform.system() == "Linux":
                battery_info.update(self._get_linux_battery_info())
            elif platform.system() == "Darwin":
                battery_info.update(self._get_macos_battery_info())
        
        except Exception as e:
            print(f"Error getting battery info: {e}")
        
        return battery_info
    
    def _get_windows_battery_info(self) -> Dict[str, Any]:
        """Get Windows-specific battery information"""
        info = {}
        
        try:
            # Try using WMI for detailed battery info
            if 'wmi' in globals() and wmi:
                import pythoncom
                pythoncom.CoInitialize()
                c = wmi.WMI()
                
                for battery in c.Win32_Battery():
                    if battery.EstimatedChargeRemaining is not None:
                        info['percentage'] = int(battery.EstimatedChargeRemaining)
                    if battery.BatteryStatus is not None:
                        # BatteryStatus: 1=Discharging, 2=AC Power, 3=Fully Charged, 4=Low, 5=Critical, 6=Charging
                        info['plugged'] = battery.BatteryStatus in [2, 3, 6]
                    if battery.EstimatedRunTime is not None:
                        info['time_left'] = battery.EstimatedRunTime * 60  # Convert to seconds
                    if battery.Temperature is not None:
                        info['temperature'] = battery.Temperature
                    break
                
                pythoncom.CoUninitialize()
        
        except Exception as e:
            print(f"Windows battery detection error: {e}")
        
        return info
    
    def _get_linux_battery_info(self) -> Dict[str, Any]:
        """Get Linux-specific battery information"""
        info = {}
        
        try:
            # Try reading from /sys/class/power_supply
            import os
            
            # Find battery directory
            battery_dir = None
            for item in os.listdir('/sys/class/power_supply/'):
                if item.startswith('BAT'):
                    battery_dir = f'/sys/class/power_supply/{item}'
                    break
            
            if battery_dir:
                # Read battery percentage
                try:
                    with open(f'{battery_dir}/capacity', 'r') as f:
                        info['percentage'] = int(f.read().strip())
                except:
                    pass
                
                # Read power status
                try:
                    with open(f'{battery_dir}/status', 'r') as f:
                        status = f.read().strip().lower()
                        info['plugged'] = status in ['charging', 'full']
                except:
                    pass
                
                # Read time to empty/full
                try:
                    if info.get('plugged'):
                        with open(f'{battery_dir}/time_to_full_now', 'r') as f:
                            info['time_left'] = int(f.read().strip())
                    else:
                        with open(f'{battery_dir}/time_to_empty_now', 'r') as f:
                            info['time_left'] = int(f.read().strip())
                except:
                    pass
                
                # Read power consumption
                try:
                    with open(f'{battery_dir}/power_now', 'r') as f:
                        power_mw = int(f.read().strip())
                        info['power_consumption'] = power_mw / 1000.0  # Convert to watts
                except:
                    pass
                
                # Read temperature
                try:
                    with open(f'{battery_dir}/temp', 'r') as f:
                        temp_celsius = int(f.read().strip()) / 10.0  # Usually in 0.1°C units
                        info['temperature'] = temp_celsius
                except:
                    pass
        
        except Exception as e:
            print(f"Linux battery detection error: {e}")
        
        return info
    
    def _get_macos_battery_info(self) -> Dict[str, Any]:
        """Get macOS-specific battery information"""
        info = {}
        
        try:
            # Use system_profiler for battery info
            result = subprocess.run(['system_profiler', 'SPPowerDataType'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                current_section = None
                
                for line in lines:
                    line = line.strip()
                    if 'Battery Information:' in line:
                        current_section = 'battery'
                    elif current_section == 'battery':
                        if 'Charge Remaining (mAh):' in line:
                            try:
                                mah = int(line.split(':')[1].strip())
                                # Estimate percentage (this is approximate)
                                info['percentage'] = min(100, max(0, int(mah / 10)))
                            except:
                                pass
                        elif 'Fully Charged:' in line:
                            info['plugged'] = 'Yes' in line
                        elif 'Time Remaining:' in line:
                            time_str = line.split(':')[1].strip()
                            if time_str != '0:00':
                                # Parse time string (e.g., "2:30")
                                try:
                                    parts = time_str.split(':')
                                    minutes = int(parts[0]) * 60 + int(parts[1])
                                    info['time_left'] = minutes * 60  # Convert to seconds
                                except:
                                    pass
        
        except Exception as e:
            print(f"macOS battery detection error: {e}")
        
        return info
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network interface information"""
        network_info = {
            'interfaces': {},
            'active_connections': [],
            'wireless_networks': []
        }
        
        try:
            if psutil:
                # Get network interfaces
                interfaces = psutil.net_if_addrs()
                interface_stats = psutil.net_if_stats()
                
                for interface_name, addresses in interfaces.items():
                    interface_info = {
                        'name': interface_name,
                        'addresses': [],
                        'status': 'unknown',
                        'speed': None
                    }
                    
                    # Get addresses
                    for addr in addresses:
                        interface_info['addresses'].append({
                            'family': str(addr.family),
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': getattr(addr, 'broadcast', None)
                        })
                    
                    # Get interface status
                    if interface_name in interface_stats:
                        stats = interface_stats[interface_name]
                        interface_info['status'] = 'up' if stats.isup else 'down'
                        interface_info['speed'] = stats.speed
                    
                    network_info['interfaces'][interface_name] = interface_info
                
                # Get active connections
                connections = psutil.net_connections()
                for conn in connections:
                    if conn.status == 'ESTABLISHED':
                        network_info['active_connections'].append({
                            'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                            'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            'status': conn.status,
                            'pid': conn.pid
                        })
        
        except Exception as e:
            print(f"Error getting network info: {e}")
        
        return network_info
    
    def get_cached_system_info(self) -> Optional[SystemInfo]:
        """Get cached system information"""
        return self._system_info
    
    def get_cached_battery_info(self) -> Dict[str, Any]:
        """Get cached battery information"""
        return self._battery_info.copy()
