import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import random

class DashboardWindow(ttk.Frame):
    def __init__(self, parent, screenshot_history):
        super().__init__(parent)
        self.screenshot_history = screenshot_history
        self.current_page = 0
        self.items_per_page = 10
        self.current_image = None  # Keep reference to prevent garbage collection
        
        self._create_widgets()
        self._load_history()

    def _create_widgets(self):
        # Main container
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(expand=True, fill='both', padx=5, pady=5)

        # Left panel - History list
        self.history_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.history_frame, weight=1)

        # Top buttons frame
        buttons_frame = ttk.Frame(self.history_frame)
        buttons_frame.pack(fill=tk.X, pady=5)

        # Add Generate Test Data button
        ttk.Button(
            buttons_frame,
            text="Generate Test Data",
            command=self._generate_test_data
        ).pack(side=tk.LEFT, padx=5)

        # Add Refresh button
        ttk.Button(
            buttons_frame,
            text="Refresh",
            command=self._load_history
        ).pack(side=tk.LEFT, padx=5)

        # History list with scrollbar
        self.history_list = ttk.Treeview(
            self.history_frame,
            columns=('Date', 'Time', 'Alerts'),
            show='headings'
        )
        self.history_list.heading('Date', text='Date')
        self.history_list.heading('Time', text='Time')
        self.history_list.heading('Alerts', text='Alerts')
        
        scrollbar = ttk.Scrollbar(
            self.history_frame,
            orient=tk.VERTICAL,
            command=self.history_list.yview
        )
        self.history_list.configure(yscrollcommand=scrollbar.set)
        
        self.history_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.history_list.bind('<<TreeviewSelect>>', self._on_select_item)

        # Navigation buttons
        nav_frame = ttk.Frame(self.history_frame)
        nav_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            nav_frame,
            text="Previous",
            command=self._previous_page
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            nav_frame,
            text="Next",
            command=self._next_page
        ).pack(side=tk.LEFT, padx=5)

        # Right panel - Screenshot preview
        self.preview_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.preview_frame, weight=2)

        # Preview label
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack(expand=True, fill='both', padx=5, pady=5)

        # Analysis details
        self.details_frame = ttk.LabelFrame(
            self.preview_frame,
            text="Analysis Details",
            padding=10
        )
        self.details_frame.pack(fill=tk.X, padx=5, pady=5)

        self.details_text = tk.Text(
            self.details_frame,
            height=5,
            width=40,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.details_text.pack(fill=tk.X)

        # Delete button
        ttk.Button(
            self.preview_frame,
            text="Delete Screenshot",
            command=self._delete_current
        ).pack(pady=5)

        # Set up auto-refresh
        self._setup_auto_refresh()

    def _setup_auto_refresh(self):
        """Set up automatic refresh of the history list"""
        self._load_history()
        self.after(5000, self._setup_auto_refresh)  # Refresh every 5 seconds

    def _generate_test_data(self):
        """Generate sample screenshot entries with mock analysis data"""
        # Create a sample blank image
        image = Image.new('RGB', (800, 600), color='white')
        
        # Generate entries for the last 24 hours
        now = datetime.now()
        for i in range(20):
            # Generate random timestamp within last 24 hours
            timestamp = now - timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Generate random analysis results
            analysis = {
                'violence': random.uniform(0.1, 0.9),
                'adult': random.uniform(0.1, 0.9),
                'hate': random.uniform(0.1, 0.9),
                'drugs': random.uniform(0.1, 0.9)
            }
            
            # Save to history
            self.screenshot_history.save_screenshot(image, analysis)
        
        # Refresh the display
        self._load_history()

    def _load_history(self):
        """Load and display screenshot history"""
        # Clear existing items
        for item in self.history_list.get_children():
            self.history_list.delete(item)

        # Get paginated history
        entries = self.screenshot_history.get_history(
            limit=self.items_per_page,
            offset=self.current_page * self.items_per_page
        )

        # Add entries to the list
        for entry in entries:
            timestamp = datetime.fromisoformat(entry['timestamp'])
            analysis = entry.get('analysis', {})
            has_alerts = any(
                float(score) >= 0.7
                for score in analysis.values()
                if isinstance(score, (int, float, str)) and str(score).replace('.', '', 1).isdigit()
            )
            
            self.history_list.insert(
                '',
                'end',
                values=(
                    timestamp.strftime('%Y-%m-%d'),
                    timestamp.strftime('%H:%M:%S'),
                    '⚠️' if has_alerts else ''
                ),
                tags=(entry['filename'],)
            )

    def _on_select_item(self, event):
        """Handle screenshot selection"""
        selection = self.history_list.selection()
        if not selection:
            return

        item = selection[0]
        filename = self.history_list.item(item)['tags'][0]
        
        # Load and display the screenshot
        screenshot = self.screenshot_history.get_screenshot(filename)
        if screenshot:
            # Resize for preview
            preview_size = (400, 300)
            screenshot.thumbnail(preview_size, Image.LANCZOS)
            
            # Convert to PhotoImage
            self.current_image = ImageTk.PhotoImage(screenshot)
            self.preview_label.configure(image=self.current_image)

            # Update analysis details
            entry = next(
                (e for e in self.screenshot_history.get_history()
                 if e['filename'] == filename),
                None
            )
            
            self.details_text.configure(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            
            if entry and entry.get('analysis'):
                details = "\n".join(
                    f"{k.title()}: {v:.2f}"
                    for k, v in entry['analysis'].items()
                    if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).isdigit())
                )
                self.details_text.insert(tk.END, details)
            else:
                self.details_text.insert(tk.END, "No analysis data available")
            
            self.details_text.configure(state=tk.DISABLED)

    def _delete_current(self):
        """Delete the currently selected screenshot"""
        selection = self.history_list.selection()
        if not selection:
            return

        item = selection[0]
        filename = self.history_list.item(item)['tags'][0]
        
        if self.screenshot_history.delete_screenshot(filename):
            self.history_list.delete(item)
            self.preview_label.configure(image='')
            self.details_text.configure(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            self.details_text.configure(state=tk.DISABLED)

    def _previous_page(self):
        """Show previous page of history"""
        if self.current_page > 0:
            self.current_page -= 1
            self._load_history()

    def _next_page(self):
        """Show next page of history"""
        # Get entries for next page
        entries = self.screenshot_history.get_history(
            limit=self.items_per_page,
            offset=(self.current_page + 1) * self.items_per_page
        )
        # Check if there are entries in the next page before incrementing
        if len(entries) > 0:
            self.current_page += 1
            self._load_history()
