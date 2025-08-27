#!/usr/bin/env python3
"""
Modern GUI for Wireless Device Manager with battery monitoring and device management
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from typing import Optional, List
import platform

from models import WirelessDevice, DeviceType, DeviceStatus, SystemInfo
from device_manager import WirelessDeviceManager
from system_monitor import SystemMonitor

class ModernWirelessDeviceGUI:
    """Modern GUI for the Wireless Device Manager with enhanced features"""
    
    def __init__(self):
        self.manager = WirelessDeviceManager()
        self.system_monitor = SystemMonitor()
        
        # Setup main window
        self.root = tk.Tk()
        self.root.title("AirMon - Wireless Device Manager")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Variables
        self.scan_timer = None
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.selected_device = None
        
        # Setup GUI
        self.setup_gui()
        
        # Start system monitoring
        self.system_monitor.start_monitoring(callback=self.on_system_update, interval=2.0)
        
        # Initial scan
        self.scan_devices()
    
    def setup_gui(self):
        """Setup the main GUI components"""
        # Main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(2, weight=1)
        
        # Header section
        self.setup_header(main_container)
        
        # Control panel
        self.setup_control_panel(main_container)
        
        # Main content area
        self.setup_main_content(main_container)
        
        # Status bar
        self.setup_status_bar(main_container)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_header(self, parent):
        """Setup the header section with title and system info"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(header_frame, text="AirMon", font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        subtitle_label = ttk.Label(header_frame, text="Wireless Device Manager", font=('Arial', 12))
        subtitle_label.grid(row=1, column=0, sticky=tk.W)
        
        # System info panel
        system_frame = ttk.LabelFrame(header_frame, text="System Information", padding="5")
        system_frame.grid(row=0, column=1, rowspan=2, padx=(20, 0), sticky=(tk.E, tk.N, tk.S))
        
        # Battery info
        self.battery_label = ttk.Label(system_frame, text="Battery: --")
        self.battery_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # CPU info
        self.cpu_label = ttk.Label(system_frame, text="CPU: --")
        self.cpu_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # Memory info
        self.memory_label = ttk.Label(system_frame, text="Memory: --")
        self.memory_label.grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        
        # Platform info
        self.platform_label = ttk.Label(system_frame, text=f"Platform: {platform.system()}")
        self.platform_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
    
    def setup_control_panel(self, parent):
        """Setup the control panel with buttons and filters"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        control_frame.columnconfigure(1, weight=1)
        
        # Left side - Action buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0, sticky=tk.W)
        
        self.scan_button = ttk.Button(button_frame, text="Scan Devices", command=self.scan_devices)
        self.scan_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.refresh_button = ttk.Button(button_frame, text="Auto Refresh", command=self.toggle_auto_refresh)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        self.auto_refresh_check = ttk.Checkbutton(button_frame, text="Auto", variable=self.auto_refresh_var)
        self.auto_refresh_check.pack(side=tk.LEFT, padx=5)
        
        # Device management buttons
        self.enable_button = ttk.Button(button_frame, text="Enable", command=self.enable_selected_device)
        self.enable_button.pack(side=tk.LEFT, padx=(10, 5))
        
        self.disable_button = ttk.Button(button_frame, text="Disable", command=self.disable_selected_device)
        self.disable_button.pack(side=tk.LEFT, padx=5)
        
        # Right side - Filters
        filter_frame = ttk.Frame(control_frame)
        filter_frame.grid(row=0, column=1, sticky=tk.E)
        
        # Device type filter
        ttk.Label(filter_frame, text="Filter by type:").pack(side=tk.LEFT, padx=(0, 5))
        self.type_filter_var = tk.StringVar(value="All")
        type_filter_combo = ttk.Combobox(filter_frame, textvariable=self.type_filter_var, 
                                        values=["All"] + [t.value for t in DeviceType], 
                                        state="readonly", width=15)
        type_filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status filter
        ttk.Label(filter_frame, text="Filter by status:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_filter_var = tk.StringVar(value="All")
        status_filter_combo = ttk.Combobox(filter_frame, textvariable=self.status_filter_var, 
                                          values=["All"] + [s.value for s in DeviceStatus], 
                                          state="readonly", width=15)
        status_filter_combo.pack(side=tk.LEFT, padx=(0, 10))
    
    def setup_main_content(self, parent):
        """Setup the main content area with device list and info panel"""
        # Create notebook for tabs
        notebook = ttk.Notebook(parent)
        notebook.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Devices tab
        devices_frame = ttk.Frame(notebook)
        notebook.add(devices_frame, text="Devices")
        devices_frame.columnconfigure(0, weight=1)
        devices_frame.rowconfigure(0, weight=1)
        
        # Device tree with scrollbars
        tree_frame = ttk.Frame(devices_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Treeview columns
        columns = ('Name', 'Type', 'Interface', 'MAC Address', 'Status', 'Battery', 'Signal')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=15)
        
        # Configure columns
        self.tree.column('#0', width=50, minwidth=50)
        self.tree.column('Name', width=250, minwidth=200)
        self.tree.column('Type', width=120, minwidth=100)
        self.tree.column('Interface', width=150, minwidth=120)
        self.tree.column('MAC Address', width=130, minwidth=120)
        self.tree.column('Status', width=100, minwidth=80)
        self.tree.column('Battery', width=80, minwidth=60)
        self.tree.column('Signal', width=80, minwidth=60)
        
        # Configure headings
        self.tree.heading('#0', text='#')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Interface', text='Interface')
        self.tree.heading('MAC Address', text='MAC Address')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Battery', text='Battery')
        self.tree.heading('Signal', text='Signal')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid tree and scrollbars
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_device_select)
        self.tree.bind('<Double-1>', self.show_device_details)
        
        # Device info panel
        info_frame = ttk.LabelFrame(devices_frame, text="Device Information", padding="5")
        info_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        self.info_text = scrolledtext.ScrolledText(info_frame, width=40, wrap=tk.WORD)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def setup_status_bar(self, parent):
        """Setup the status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Progress bar for operations
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, mode='indeterminate')
        self.progress_bar.grid(row=0, column=1, sticky=tk.E, padx=(10, 0))
    
    def scan_devices(self):
        """Scan for devices in a separate thread"""
        self.status_label.config(text="Scanning devices...")
        self.scan_button.config(state="disabled")
        self.progress_bar.start()
        
        # Run scan in thread to avoid GUI freezing
        thread = threading.Thread(target=self._scan_thread)
        thread.daemon = True
        thread.start()
    
    def _scan_thread(self):
        """Thread function for scanning devices"""
        try:
            devices = self.manager.scan_devices()
            # Update GUI in main thread
            self.root.after(0, self._update_device_list, devices)
        except Exception as e:
            self.root.after(0, self._scan_error, str(e))
    
    def _update_device_list(self, devices: List[WirelessDevice]):
        """Update the device list in the GUI"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Group devices by type
        device_groups = {}
        for device in devices:
            device_type = device.device_type.value
            if device_type not in device_groups:
                device_groups[device_type] = []
            device_groups[device_type].append(device)
        
        # Add devices to tree grouped by type
        for group_name, group_devices in device_groups.items():
            # Add group header
            group_id = self.tree.insert('', 'end', text='', 
                                       values=(f"{group_name} ({len(group_devices)})", '', '', '', '', '', ''))
            
            # Add devices in group
            for i, device in enumerate(group_devices):
                battery_text = f"{device.battery_level}%" if device.battery_level is not None else "N/A"
                signal_text = f"{device.signal_strength}%" if device.signal_strength is not None else "N/A"
                
                self.tree.insert(group_id, 'end', text=str(i+1),
                               values=(
                                   device.name,
                                   device.device_type.value,
                                   device.interface,
                                   device.mac_address or 'N/A',
                                   device.status.value,
                                   battery_text,
                                   signal_text
                               ))
        
        # Expand all groups
        for item in self.tree.get_children():
            self.tree.item(item, open=True)
        
        self.status_label.config(text=f"Found {len(devices)} devices")
        self.scan_button.config(state="normal")
        self.progress_bar.stop()
        
        # Schedule next scan if auto-refresh is enabled
        if self.auto_refresh_var.get():
            self.scan_timer = self.root.after(5000, self.scan_devices)  # Scan every 5 seconds
    
    def _scan_error(self, error_message: str):
        """Handle scan errors"""
        self.status_label.config(text="Scan failed")
        self.scan_button.config(state="normal")
        self.progress_bar.stop()
        messagebox.showerror("Scan Error", f"Failed to scan devices:\n{error_message}")
    
    def toggle_auto_refresh(self):
        """Toggle auto refresh mode"""
        if self.auto_refresh_var.get():
            if self.scan_timer:
                self.root.after_cancel(self.scan_timer)
            self.scan_devices()
        else:
            if self.scan_timer:
                self.root.after_cancel(self.scan_timer)
                self.scan_timer = None
    
    def on_device_select(self, event):
        """Handle device selection"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            parent = self.tree.parent(item)
            if parent:  # This is a device, not a group
                self.selected_device = self.get_device_from_tree_item(item)
                self.update_device_info()
                self.update_button_states()
            else:
                self.selected_device = None
                self.update_button_states()
    
    def get_device_from_tree_item(self, item) -> Optional[WirelessDevice]:
        """Get device object from tree item"""
        values = self.tree.item(item, 'values')
        if len(values) < 5:
            return None
        
        name, device_type_str, interface, mac_address, status_str = values[:5]
        
        # Find the actual device object
        for device in self.manager.devices:
            if (device.name == name and 
                device.device_type.value == device_type_str and
                device.interface == interface):
                return device
        
        return None
    
    def update_button_states(self):
        """Update enable/disable button states based on selected device"""
        if self.selected_device and self.manager.can_manage_device(self.selected_device):
            self.enable_button.config(state="normal")
            self.disable_button.config(state="normal")
        else:
            self.enable_button.config(state="disabled")
            self.disable_button.config(state="disabled")
    
    def update_device_info(self):
        """Update device information display"""
        if not self.selected_device:
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, "No device selected. Click on a device to view information.")
            return
        
        device = self.selected_device
        info = f"Device Information\n"
        info += f"{'='*50}\n\n"
        info += f"Name: {device.name}\n"
        info += f"Type: {device.device_type.value}\n"
        info += f"Interface: {device.interface}\n"
        info += f"MAC Address: {device.mac_address or 'N/A'}\n"
        info += f"Status: {device.status.value}\n"
        
        if device.battery_level is not None:
            info += f"Battery: {device.battery_level}%\n"
        if device.signal_strength is not None:
            info += f"Signal: {device.signal_strength}%\n"
        
        if device.vendor_id:
            info += f"Vendor ID: {device.vendor_id}\n"
        if device.product_id:
            info += f"Product ID: {device.product_id}\n"
        
        if device.additional_info:
            info += f"\nAdditional Information:\n"
            info += f"{'-'*30}\n"
            for key, value in device.additional_info.items():
                info += f"{key.replace('_', ' ').title()}: {value}\n"
        
        # Management capabilities
        info += f"\nManagement Capabilities:\n"
        info += f"{'-'*30}\n"
        manageable = self.manager.can_manage_device(device)
        info += f"Can be managed: {'Yes' if manageable else 'No'}\n"
        
        if manageable:
            info += f"Available actions: Enable, Disable\n"
        else:
            info += f"Note: This device type may require manual management\n"
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
    
    def enable_selected_device(self):
        """Enable the selected device"""
        if not self.selected_device:
            messagebox.showwarning("No Device Selected", "Please select a device first.")
            return
        
        device = self.selected_device
        if not self.manager.can_manage_device(device):
            messagebox.showwarning("Cannot Manage", f"Device '{device.name}' cannot be managed by this application.")
            return
        
        try:
            success = self.manager.enable_device(device)
            if success:
                messagebox.showinfo("Success", f"Device '{device.name}' enabled successfully.")
                self.scan_devices()  # Refresh to show new status
            else:
                messagebox.showwarning("Warning", 
                                     f"Could not enable device '{device.name}'.\n"
                                     f"This may require administrator privileges or the device may not support this operation.")
        except Exception as e:
            messagebox.showerror("Error", f"Error enabling device: {e}")
    
    def disable_selected_device(self):
        """Disable the selected device"""
        if not self.selected_device:
            messagebox.showwarning("No Device Selected", "Please select a device first.")
            return
        
        device = self.selected_device
        if not self.manager.can_manage_device(device):
            messagebox.showwarning("Cannot Manage", f"Device '{device.name}' cannot be managed by this application.")
            return
        
        result = messagebox.askyesno("Confirm", f"Are you sure you want to disable '{device.name}'?")
        if result:
            try:
                success = self.manager.disable_device(device)
                if success:
                    messagebox.showinfo("Success", f"Device '{device.name}' disabled successfully.")
                    self.scan_devices()  # Refresh to show new status
                else:
                    messagebox.showwarning("Warning", 
                                         f"Could not disable device '{device.name}'.\n"
                                         f"This may require administrator privileges or the device may not support this operation.")
            except Exception as e:
                messagebox.showerror("Error", f"Error disabling device: {e}")
    
    def show_device_details(self, event=None):
        """Show detailed device information in a new window"""
        if not self.selected_device:
            return
        
        device = self.selected_device
        
        # Create detail window
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Device Details - {device.name}")
        detail_window.geometry("600x500")
        detail_window.transient(self.root)
        detail_window.grab_set()
        
        # Detail content
        detail_text = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD)
        detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Format detailed information
        detail_info = f"Detailed Device Information\n"
        detail_info += f"{'='*60}\n\n"
        detail_info += f"Device Name: {device.name}\n"
        detail_info += f"Device Type: {device.device_type.value}\n"
        detail_info += f"Interface: {device.interface}\n"
        detail_info += f"MAC Address: {device.mac_address or 'N/A'}\n"
        detail_info += f"Status: {device.status.value}\n"
        detail_info += f"Vendor ID: {device.vendor_id or 'N/A'}\n"
        detail_info += f"Product ID: {device.product_id or 'N/A'}\n"
        detail_info += f"Battery Level: {device.battery_level or 'N/A'}\n"
        detail_info += f"Signal Strength: {device.signal_strength or 'N/A'}\n"
        
        if device.additional_info:
            detail_info += f"\nAdditional Information:\n"
            detail_info += f"{'-'*40}\n"
            for key, value in device.additional_info.items():
                detail_info += f"{key.replace('_', ' ').title()}: {value}\n"
        
        detail_text.insert(1.0, detail_info)
        detail_text.config(state=tk.DISABLED)
    
    def on_system_update(self, system_info, battery_info):
        """Callback for system monitoring updates"""
        # Update system info display in main thread
        self.root.after(0, self._update_system_display, system_info, battery_info)
    
    def _update_system_display(self, system_info, battery_info):
        """Update system display in main thread"""
        # Update header labels
        if system_info.battery_percentage is not None:
            battery_text = f"Battery: {system_info.battery_percentage}%"
            if system_info.battery_plugged:
                battery_text += " (Plugged)"
            else:
                battery_text += " (Unplugged)"
            self.battery_label.config(text=battery_text)
        else:
            self.battery_label.config(text="Battery: N/A")
        
        self.cpu_label.config(text=f"CPU: {system_info.cpu_usage:.1f}%")
        self.memory_label.config(text=f"Memory: {system_info.memory_usage:.1f}%")
    
    def on_closing(self):
        """Handle application closing"""
        try:
            # Stop system monitoring
            self.system_monitor.stop_monitoring()
            
            # Cancel any pending timers
            if self.scan_timer:
                self.root.after_cancel(self.scan_timer)
            
            # Close the window
            self.root.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            self.root.destroy()
    
    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
        except Exception as e:
            messagebox.showerror("Application Error", f"An error occurred: {e}")
            self.on_closing()
