import tkinter as tk
from tkinter import ttk, messagebox

class DeviceWindow(tk.Toplevel):
    def __init__(self, parent, device_manager, screenshot_manager):
        super().__init__(parent)
        self.device_manager = device_manager
        self.screenshot_manager = screenshot_manager
        
        self.title("Device Management")
        self.geometry("600x400")
        self.resizable(False, False)
        
        self._create_widgets()
        self._load_devices()

    def _create_widgets(self):
        # Devices list frame
        list_frame = ttk.LabelFrame(self, text="Monitored Devices", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Devices list with scrollbar
        self.devices_list = ttk.Treeview(
            list_frame,
            columns=('Name', 'Type', 'Status', 'Backend', 'Error'),
            show='headings'
        )
        self.devices_list.heading('Name', text='Device Name')
        self.devices_list.heading('Type', text='Type')
        self.devices_list.heading('Status', text='Status')
        self.devices_list.heading('Backend', text='Backend')
        self.devices_list.heading('Error', text='Last Error')
        
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.devices_list.yview
        )
        self.devices_list.configure(yscrollcommand=scrollbar.set)
        
        self.devices_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Control buttons frame
        controls_frame = ttk.Frame(self, padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            controls_frame,
            text="Add Device",
            command=self._add_device
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            controls_frame,
            text="Edit Device",
            command=self._edit_device
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            controls_frame,
            text="Remove Device",
            command=self._remove_device
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            controls_frame,
            text="Start Monitoring",
            command=self._start_selected
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            controls_frame,
            text="Stop Monitoring",
            command=self._stop_selected
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            controls_frame,
            text="Refresh",
            command=self._load_devices
        ).pack(side=tk.LEFT, padx=5)

    def _load_devices(self):
        """Load and display devices"""
        # Clear existing items
        for item in self.devices_list.get_children():
            self.devices_list.delete(item)

        # Add devices to the list
        for device in self.device_manager.get_all_devices():
            device_type = "VNC" if device.config.get('vnc_host') else "Local"
            self.devices_list.insert(
                '',
                'end',
                values=(
                    device.name,
                    device_type,
                    'Active' if device.is_active else 'Inactive',
                    device.config.get('screenshot_backend', 'Not Set'),
                    device.last_error or ''
                ),
                tags=(device.device_id,)
            )

    def _add_device(self):
        """Add a new device"""
        dialog = DeviceDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            device = self.device_manager.add_device(
                dialog.result['name'],
                dialog.result['config']
            )
            if device:
                self.screenshot_manager.test_screenshot_capability(device.device_id)
                self._load_devices()

    def _edit_device(self):
        """Edit selected device"""
        selection = self.devices_list.selection()
        if not selection:
            messagebox.showwarning(
                "No Selection",
                "Please select a device to edit"
            )
            return

        item = selection[0]
        device_id = self.devices_list.item(item)['tags'][0]
        device = self.device_manager.get_device(device_id)
        
        if device:
            dialog = DeviceDialog(self, device)
            self.wait_window(dialog)
            if dialog.result:
                device.name = dialog.result['name']
                device.config.update(dialog.result['config'])
                self.device_manager.update_device_config(device_id, device.config)
                self._load_devices()

    def _remove_device(self):
        """Remove selected device"""
        selection = self.devices_list.selection()
        if not selection:
            messagebox.showwarning(
                "No Selection",
                "Please select a device to remove"
            )
            return

        if messagebox.askyesno(
            "Confirm Removal",
            "Are you sure you want to remove this device?"
        ):
            item = selection[0]
            device_id = self.devices_list.item(item)['tags'][0]
            
            # Stop monitoring if active
            self.screenshot_manager.stop_monitoring(device_id)
            
            # Remove device
            if self.device_manager.remove_device(device_id):
                self._load_devices()

    def _start_selected(self):
        """Start monitoring selected device"""
        selection = self.devices_list.selection()
        if not selection:
            messagebox.showwarning(
                "No Selection",
                "Please select a device to start"
            )
            return

        item = selection[0]
        device_id = self.devices_list.item(item)['tags'][0]
        if self.screenshot_manager.start_monitoring(device_id):
            self._load_devices()
        else:
            messagebox.showerror(
                "Error",
                "Failed to start monitoring. Check device status."
            )

    def _stop_selected(self):
        """Stop monitoring selected device"""
        selection = self.devices_list.selection()
        if not selection:
            messagebox.showwarning(
                "No Selection",
                "Please select a device to stop"
            )
            return

        item = selection[0]
        device_id = self.devices_list.item(item)['tags'][0]
        self.screenshot_manager.stop_monitoring(device_id)
        self._load_devices()

class DeviceDialog(tk.Toplevel):
    def __init__(self, parent, device=None):
        super().__init__(parent)
        self.result = None
        self.device = device
        
        self.title("Add Device" if not device else "Edit Device")
        self.geometry("400x350")
        self.resizable(False, False)
        
        self._create_widgets()
        if device:
            self._load_device_data()

    def _create_widgets(self):
        # Name entry
        ttk.Label(self, text="Device Name:").pack(padx=10, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(
            self,
            textvariable=self.name_var,
            width=30
        ).pack(padx=10, pady=5)

        # Device type selection
        type_frame = ttk.LabelFrame(self, text="Device Type", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=5)

        self.device_type = tk.StringVar(value="local")
        ttk.Radiobutton(
            type_frame,
            text="Local Device",
            variable=self.device_type,
            value="local",
            command=self._toggle_vnc_settings
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            type_frame,
            text="Remote VNC",
            variable=self.device_type,
            value="vnc",
            command=self._toggle_vnc_settings
        ).pack(anchor=tk.W)

        # VNC Settings
        self.vnc_frame = ttk.LabelFrame(self, text="VNC Settings", padding=10)
        
        # VNC Host
        ttk.Label(self.vnc_frame, text="Host:").pack(anchor=tk.W)
        self.vnc_host_var = tk.StringVar()
        ttk.Entry(
            self.vnc_frame,
            textvariable=self.vnc_host_var,
            width=30
        ).pack(fill=tk.X)

        # VNC Port
        ttk.Label(self.vnc_frame, text="Port:").pack(anchor=tk.W)
        self.vnc_port_var = tk.StringVar(value="5900")
        ttk.Entry(
            self.vnc_frame,
            textvariable=self.vnc_port_var,
            width=10
        ).pack(anchor=tk.W)

        # VNC Password
        ttk.Label(self.vnc_frame, text="Password:").pack(anchor=tk.W)
        self.vnc_password_var = tk.StringVar()
        ttk.Entry(
            self.vnc_frame,
            textvariable=self.vnc_password_var,
            show="*",
            width=30
        ).pack(fill=tk.X)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self._on_save
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy
        ).pack(side=tk.LEFT, padx=5)

        # Initial state
        self._toggle_vnc_settings()

    def _toggle_vnc_settings(self):
        """Show/hide VNC settings based on device type"""
        if self.device_type.get() == "vnc":
            self.vnc_frame.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.vnc_frame.pack_forget()

    def _load_device_data(self):
        """Load existing device data for editing"""
        self.name_var.set(self.device.name)
        
        if self.device.config.get('vnc_host'):
            self.device_type.set("vnc")
            self.vnc_host_var.set(self.device.config.get('vnc_host', ''))
            self.vnc_port_var.set(str(self.device.config.get('vnc_port', '5900')))
            self.vnc_password_var.set(self.device.config.get('vnc_password', ''))
        else:
            self.device_type.set("local")
        
        self._toggle_vnc_settings()

    def _validate_inputs(self):
        """Validate user inputs"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning(
                "Invalid Input",
                "Please enter a device name"
            )
            return False

        if self.device_type.get() == "vnc":
            host = self.vnc_host_var.get().strip()
            port = self.vnc_port_var.get().strip()
            password = self.vnc_password_var.get().strip()

            if not host:
                messagebox.showwarning(
                    "Invalid Input",
                    "Please enter VNC host"
                )
                return False

            try:
                port = int(port)
                if not (1 <= port <= 65535):
                    raise ValueError()
            except ValueError:
                messagebox.showwarning(
                    "Invalid Input",
                    "Port must be a number between 1 and 65535"
                )
                return False

            if not password:
                messagebox.showwarning(
                    "Invalid Input",
                    "Please enter VNC password"
                )
                return False

        return True

    def _on_save(self):
        """Handle save button click"""
        if not self._validate_inputs():
            return

        config = {}
        if self.device_type.get() == "vnc":
            config.update({
                'vnc_host': self.vnc_host_var.get().strip(),
                'vnc_port': int(self.vnc_port_var.get().strip()),
                'vnc_password': self.vnc_password_var.get().strip()
            })

        self.result = {
            'name': self.name_var.get().strip(),
            'config': config
        }
        self.destroy()
