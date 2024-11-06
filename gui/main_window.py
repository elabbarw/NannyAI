import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from .settings_window import SettingsWindow
from .dashboard_window import DashboardWindow
from .device_window import DeviceWindow
from .styles import apply_styles
from report_generator import ReportGenerator
from datetime import datetime, timedelta
import os
import subprocess
import platform
from system_tray import SystemTrayIcon

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind('<Enter>', self.show)
        self.widget.bind('<Leave>', self.hide)

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox('insert')
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip = tk.Toplevel()
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f'+{x}+{y}')
        label = ttk.Label(self.tooltip, text=self.text, background='#ffffe0')
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class MainWindow:
    def __init__(self, root, config, screenshot_mgr, content_analyzer, notification_mgr):
        self.root = root
        self.config = config
        self.screenshot_mgr = screenshot_mgr
        self.content_analyzer = content_analyzer
        self.notification_mgr = notification_mgr
        self.report_generator = ReportGenerator(
            screenshot_mgr.history_manager,
            screenshot_mgr.device_manager
        )

        self.root.title("NannyAI")
        self.root.geometry("800x600")
        
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Setup keyboard shortcuts
        self.root.bind('<Control-Shift-H>', self._toggle_window)
        self.root.bind('<Control-Shift-S>', self._start_all_monitoring)
        self.root.bind('<Control-Shift-X>', self._stop_all_monitoring)
        
        apply_styles(self.root)
        self._create_widgets()
        
        # Initialize system tray icon
        self.system_tray = SystemTrayIcon(self)
        self.system_tray.run()
        
        # Add keyboard shortcut hints to tooltips
        self._add_shortcut_tooltips()

    def _create_widgets(self):
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)

        # Main monitoring tab
        monitoring_tab = ttk.Frame(self.notebook)
        self.notebook.add(monitoring_tab, text='Monitoring')
        self._create_monitoring_tab(monitoring_tab)

        # Dashboard tab
        dashboard_tab = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_tab, text='Dashboard')
        self.dashboard = DashboardWindow(dashboard_tab, self.screenshot_mgr.history_manager)
        self.dashboard.pack(expand=True, fill='both')

    def _create_monitoring_tab(self, parent):
        # Device Management Button
        ttk.Button(
            parent,
            text="Manage Devices",
            command=self._open_device_manager
        ).pack(pady=10)

        # Status Frame
        status_frame = ttk.LabelFrame(parent, text="Monitoring Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = ttk.Label(
            status_frame,
            text="Status: No active devices",
            font=('Arial', 12)
        )
        self.status_label.pack()

        # Backend Info Label
        self.backend_label = ttk.Label(
            status_frame,
            text="Active Devices: 0",
            font=('Arial', 10)
        )
        self.backend_label.pack(pady=2)

        # Error Message Label
        self.error_label = ttk.Label(
            status_frame,
            text="",
            foreground="red",
            wraplength=350
        )
        self.error_label.pack(fill=tk.X, pady=5)

        # Control Buttons
        button_frame = ttk.Frame(parent, padding=10)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        self.start_button = ttk.Button(
            button_frame,
            text="Start All Monitoring",
            command=self._start_all_monitoring
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="Stop All Monitoring",
            command=self._stop_all_monitoring
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Settings",
            command=self._open_settings
        ).pack(side=tk.LEFT, padx=5)

        # Report Generation Frame
        report_frame = ttk.LabelFrame(parent, text="Report Generation", padding=10)
        report_frame.pack(fill=tk.X, padx=10, pady=5)

        # Report Period Selection
        period_frame = ttk.Frame(report_frame)
        period_frame.pack(fill=tk.X, pady=5)

        ttk.Label(period_frame, text="Period:").pack(side=tk.LEFT, padx=5)
        self.period_var = tk.StringVar(value="last_7_days")
        period_menu = ttk.OptionMenu(
            period_frame,
            self.period_var,
            "last_7_days",
            "last_7_days",
            "last_30_days",
            "today",
            "yesterday"
        )
        period_menu.pack(side=tk.LEFT, padx=5)

        # Device Selection for Report
        device_frame = ttk.Frame(report_frame)
        device_frame.pack(fill=tk.X, pady=5)

        ttk.Label(device_frame, text="Device:").pack(side=tk.LEFT, padx=5)
        self.report_device_var = tk.StringVar(value="all")
        self.device_menu = ttk.OptionMenu(
            device_frame,
            self.report_device_var,
            "all",
            "all"
        )
        self.device_menu.pack(side=tk.LEFT, padx=5)

        # Generate Report Button
        ttk.Button(
            report_frame,
            text="Generate Report",
            command=self._generate_report
        ).pack(pady=5)

        # Debug Mode Frame
        debug_frame = ttk.LabelFrame(parent, text="Debug Options", padding=10)
        debug_frame.pack(fill=tk.X, padx=10, pady=5)

        self.debug_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            debug_frame,
            text="Debug Mode",
            variable=self.debug_var,
            command=self._toggle_debug_mode
        ).pack(side=tk.LEFT, padx=5)

        # Update initial state
        self._update_status()
        self._update_device_menu()

    def _add_shortcut_tooltips(self):
        Tooltip(self.start_button, "Start all monitoring (Ctrl+Shift+S)")
        Tooltip(self.stop_button, "Stop all monitoring (Ctrl+Shift+X)")

    def _on_close(self):
        self.root.withdraw()

    def show(self):
        self.root.deiconify()
        self.root.lift()

    def hide(self):
        self.root.withdraw()

    def _toggle_window(self, event=None):
        if self.root.state() == 'withdrawn':
            self.root.deiconify()
            self.root.lift()
        else:
            self.root.withdraw()

    def _open_device_manager(self):
        DeviceWindow(self.root, self.screenshot_mgr.device_manager, self.screenshot_mgr)

    def _start_all_monitoring(self, event=None):
        if self.screenshot_mgr.start_monitoring():
            messagebox.showinfo(
                "Success",
                "Monitoring started for all devices"
            )
        else:
            messagebox.showerror(
                "Error",
                "Failed to start monitoring for some devices"
            )
        self._update_status()

    def _stop_all_monitoring(self, event=None):
        self.screenshot_mgr.stop_monitoring()
        self._update_status()

    def _toggle_debug_mode(self):
        self.screenshot_mgr.set_debug_mode(self.debug_var.get())
        self._update_status()

    def _update_status(self):
        active_devices = [
            device for device in self.screenshot_mgr.device_manager.get_all_devices()
            if device.is_active
        ]
        total_devices = len(self.screenshot_mgr.device_manager.get_all_devices())
        
        status = (
            f"Status: {len(active_devices)} of {total_devices} devices active"
            if total_devices > 0
            else "Status: No devices configured"
        )
        self.status_label.config(text=status)
        
        active_info = "\n".join(
            f"Device '{device.name}': {device.config.get('screenshot_backend', 'Not Set')}"
            for device in active_devices
        )
        self.backend_label.config(
            text=active_info if active_info else "No active devices"
        )
        
        errors = [
            f"{device.name}: {device.last_error}"
            for device in self.screenshot_mgr.device_manager.get_all_devices()
            if device.last_error
        ]
        self.error_label.config(text="\n".join(errors) if errors else "")

        self._update_device_menu()

    def _update_device_menu(self):
        menu = self.device_menu['menu']
        menu.delete(0, 'end')
        
        menu.add_command(
            label="All Devices",
            command=lambda: self.report_device_var.set("all")
        )
        
        for device in self.screenshot_mgr.device_manager.get_all_devices():
            menu.add_command(
                label=device.name,
                command=lambda d=device: self.report_device_var.set(d.device_id)
            )

    def _open_pdf(self, filepath):
        try:
            system = platform.system().lower()
            if system == 'windows':
                os.startfile(filepath)
            elif system == 'linux':
                subprocess.Popen(['xdg-open', filepath])
            elif system == 'darwin':
                subprocess.Popen(['open', filepath])
            return True
        except Exception as e:
            return False

    def _generate_report(self):
        end_date = datetime.now()
        period = self.period_var.get()
        
        if period == "last_7_days":
            start_date = end_date - timedelta(days=7)
        elif period == "last_30_days":
            start_date = end_date - timedelta(days=30)
        elif period == "today":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "yesterday":
            end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = end_date - timedelta(days=1)

        device_id = None if self.report_device_var.get() == "all" else self.report_device_var.get()

        report_path = self.report_generator.generate_report(start_date, end_date, device_id)
        
        if report_path:
            if messagebox.askyesno(
                "Report Generated",
                f"Report generated successfully.\nWould you like to open it?"
            ):
                if not self._open_pdf(report_path):
                    save_path = filedialog.asksaveasfilename(
                        defaultextension=".pdf",
                        initialfile=os.path.basename(report_path),
                        filetypes=[("PDF files", "*.pdf")]
                    )
                    if save_path:
                        try:
                            import shutil
                            shutil.copy2(report_path, save_path)
                            messagebox.showinfo(
                                "Success",
                                f"Report saved to:\n{save_path}"
                            )
                        except Exception:
                            messagebox.showerror(
                                "Error",
                                "Failed to save report to selected location"
                            )
        else:
            messagebox.showerror(
                "Error",
                "Failed to generate report"
            )

    def _open_settings(self):
        SettingsWindow(self.root, self.config)
