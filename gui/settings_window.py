import tkinter as tk
from tkinter import ttk, messagebox

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        
        self.title("Settings")
        self.geometry("500x600")
        self.resizable(False, False)
        
        self._create_widgets()

    def _create_widgets(self):
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # General Settings Tab
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text='General')
        self._create_general_settings(general_frame)
        
        # Content Filtering Tab
        filtering_frame = ttk.Frame(notebook)
        notebook.add(filtering_frame, text='Content Filtering')
        self._create_filtering_settings(filtering_frame)
        
        # API Settings Tab
        api_frame = ttk.Frame(notebook)
        notebook.add(api_frame, text='API Settings')
        self._create_api_settings(api_frame)
        
        # Email Settings Tab
        email_frame = ttk.Frame(notebook)
        notebook.add(email_frame, text='Email')
        self._create_email_settings(email_frame)
        
        # Save Button
        ttk.Button(
            self,
            text="Save Settings",
            command=self._save_settings
        ).pack(pady=10)

    def _create_general_settings(self, parent):
        # Interval Settings
        interval_frame = ttk.LabelFrame(parent, text="Screenshot Interval", padding=10)
        interval_frame.pack(fill=tk.X, padx=10, pady=5)

        self.interval_var = tk.StringVar(value=str(self.config.get('screenshot_interval', 30)))
        ttk.Label(interval_frame, text="Interval (seconds):").pack(side=tk.LEFT)
        ttk.Entry(
            interval_frame,
            textvariable=self.interval_var,
            width=10
        ).pack(side=tk.LEFT, padx=5)

    def _create_api_settings(self, parent):
        # Provider Selection
        provider_frame = ttk.LabelFrame(parent, text="Vision API Provider", padding=10)
        provider_frame.pack(fill=tk.X, padx=10, pady=5)

        self.provider_var = tk.StringVar(value=self.config.get('vision_provider', 'openai'))
        ttk.Label(provider_frame, text="Select Provider:").pack(side=tk.LEFT)
        provider_menu = ttk.OptionMenu(
            provider_frame,
            self.provider_var,
            self.provider_var.get(),
            'openai',
            'gemini',
            command=self._on_provider_change
        )
        provider_menu.pack(side=tk.LEFT, padx=5)

        # Model Selection
        model_frame = ttk.LabelFrame(parent, text="Model Settings", padding=10)
        model_frame.pack(fill=tk.X, padx=10, pady=5)

        # OpenAI Model Selection
        self.openai_model_frame = ttk.Frame(model_frame)
        self.openai_model_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.openai_model_frame, text="OpenAI Model:").pack(side=tk.LEFT)
        openai_settings = self.config.get_model_settings('openai')
        self.openai_model_var = tk.StringVar(value=openai_settings.get('selected_model', 'gpt-4o-mini'))
        self.openai_model_menu = ttk.OptionMenu(
            self.openai_model_frame,
            self.openai_model_var,
            self.openai_model_var.get(),
            *openai_settings.get('available_models', ['gpt-4o','gpt-4o-mini'])
        )
        self.openai_model_menu.pack(side=tk.LEFT, padx=5)

        # Gemini Model Selection
        self.gemini_model_frame = ttk.Frame(model_frame)
        self.gemini_model_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.gemini_model_frame, text="Gemini Model:").pack(side=tk.LEFT)
        gemini_settings = self.config.get_model_settings('gemini')
        self.gemini_model_var = tk.StringVar(value=gemini_settings.get('selected_model', 'gemini-1.5-flash-8'))
        self.gemini_model_menu = ttk.OptionMenu(
            self.gemini_model_frame,
            self.gemini_model_var,
            self.gemini_model_var.get(),
            *gemini_settings.get('available_models', ['gemini-1.5-flash-8','gemini-1.5-flash-002','gemini-1.5-pro-002'])
        )
        self.gemini_model_menu.pack(side=tk.LEFT, padx=5)

        # API Keys Frame
        api_keys_frame = ttk.LabelFrame(parent, text="API Keys", padding=10)
        api_keys_frame.pack(fill=tk.X, padx=10, pady=5)

        # OpenAI API Key
        openai_frame = ttk.Frame(api_keys_frame)
        openai_frame.pack(fill=tk.X, pady=5)
        ttk.Label(openai_frame, text="OpenAI API Key:").pack(side=tk.LEFT)
        self.openai_key_var = tk.StringVar(value=self.config.get_api_key('openai'))
        self.openai_key_entry = ttk.Entry(
            openai_frame,
            textvariable=self.openai_key_var,
            show='*',
            width=40
        )
        self.openai_key_entry.pack(side=tk.LEFT, padx=5)

        # Gemini API Key
        gemini_frame = ttk.Frame(api_keys_frame)
        gemini_frame.pack(fill=tk.X, pady=5)
        ttk.Label(gemini_frame, text="Gemini API Key:").pack(side=tk.LEFT)
        self.gemini_key_var = tk.StringVar(value=self.config.get_api_key('gemini'))
        self.gemini_key_entry = ttk.Entry(
            gemini_frame,
            textvariable=self.gemini_key_var,
            show='*',
            width=40
        )
        self.gemini_key_entry.pack(side=tk.LEFT, padx=5)

        # Show/Hide API Keys
        show_keys_frame = ttk.Frame(api_keys_frame)
        show_keys_frame.pack(fill=tk.X, pady=5)
        self.show_keys_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            show_keys_frame,
            text="Show API Keys",
            variable=self.show_keys_var,
            command=self._toggle_api_key_visibility
        ).pack(side=tk.LEFT)

        # Update model frame visibility based on current provider
        self._on_provider_change()

    def _on_provider_change(self, *args):
        """Handle provider change"""
        provider = self.provider_var.get()
        # Show/hide model frames based on selected provider
        if provider == 'openai':
            self.openai_model_frame.pack(fill=tk.X, pady=5)
            self.gemini_model_frame.pack_forget()
        else:
            self.openai_model_frame.pack_forget()
            self.gemini_model_frame.pack(fill=tk.X, pady=5)

    def _toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        show_char = '' if self.show_keys_var.get() else '*'
        self.openai_key_entry.config(show=show_char)
        self.gemini_key_entry.config(show=show_char)

    def _create_filtering_settings(self, parent):
        # Content Categories
        categories_frame = ttk.LabelFrame(parent, text="Monitored Categories", padding=10)
        categories_frame.pack(fill=tk.X, padx=10, pady=5)

        self.category_vars = {}
        monitored_categories = self.config.get('monitored_categories', [])
        
        for category in ['violence', 'adult', 'hate', 'drugs','gambling']:
            var = tk.BooleanVar(value=category in monitored_categories)
            self.category_vars[category] = var
            ttk.Checkbutton(
                categories_frame,
                text=category.capitalize(),
                variable=var
            ).pack(anchor=tk.W, pady=2)

        # Threshold Settings
        thresholds_frame = ttk.LabelFrame(parent, text="Detection Thresholds", padding=10)
        thresholds_frame.pack(fill=tk.X, padx=10, pady=5)

        self.threshold_vars = {}
        current_thresholds = self.config.get('content_thresholds', {})
        
        for category in ['violence', 'adult', 'hate', 'drugs','gambling']:
            frame = ttk.Frame(thresholds_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=f"{category.capitalize()}:").pack(side=tk.LEFT)
            var = tk.StringVar(value=str(current_thresholds.get(category, 0.7)))
            self.threshold_vars[category] = var
            ttk.Entry(frame, textvariable=var, width=10).pack(side=tk.RIGHT)

    def _create_email_settings(self, parent):
        email_settings = self.config.get('email_settings', {})
        
        # SMTP Settings Group
        smtp_frame = ttk.LabelFrame(parent, text="SMTP Settings", padding=10)
        smtp_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # SMTP Server
        self.smtp_server_var = tk.StringVar(value=email_settings.get('smtp_server', 'smtp.gmail.com'))
        ttk.Label(smtp_frame, text="SMTP Server:").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Entry(
            smtp_frame,
            textvariable=self.smtp_server_var,
            width=30
        ).pack(fill=tk.X, padx=10, pady=2)
        
        # SMTP Port
        self.smtp_port_var = tk.StringVar(value=str(email_settings.get('smtp_port', '587')))
        ttk.Label(smtp_frame, text="SMTP Port:").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Entry(
            smtp_frame,
            textvariable=self.smtp_port_var,
            width=10
        ).pack(fill=tk.X, padx=10, pady=2)
        
        # Sender Email
        self.sender_email_var = tk.StringVar(value=email_settings.get('sender_email', ''))
        ttk.Label(smtp_frame, text="Sender Email:").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Entry(
            smtp_frame,
            textvariable=self.sender_email_var,
            width=30
        ).pack(fill=tk.X, padx=10, pady=2)
        
        # Sender Password
        self.sender_password_var = tk.StringVar(value=email_settings.get('sender_password', ''))
        ttk.Label(smtp_frame, text="Sender Password:").pack(anchor=tk.W, padx=10, pady=2)
        password_entry = ttk.Entry(
            smtp_frame,
            textvariable=self.sender_password_var,
            width=30,
            show='*'
        )
        password_entry.pack(fill=tk.X, padx=10, pady=2)
        
        # Parent Email
        parent_frame = ttk.LabelFrame(parent, text="Notification Settings", padding=10)
        parent_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.parent_email_var = tk.StringVar(value=email_settings.get('parent_email', ''))
        ttk.Label(parent_frame, text="Parent Email:").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Entry(
            parent_frame,
            textvariable=self.parent_email_var,
            width=30
        ).pack(fill=tk.X, padx=10, pady=2)

    def _validate_api_keys(self):
        """Validate API keys before saving"""
        provider = self.provider_var.get()
        api_key = self.openai_key_var.get() if provider == 'openai' else self.gemini_key_var.get()
        
        if not api_key:
            messagebox.showerror(
                "Error",
                f"API key for {provider} is required with current provider selection"
            )
            return False
        return True

    def _save_settings(self):
        try:
            # Validate API keys based on selected provider
            if not self._validate_api_keys():
                return

            # Save API keys
            self.config.set_api_key('openai', self.openai_key_var.get())
            self.config.set_api_key('gemini', self.gemini_key_var.get())
            
            # Save selected models
            self.config.set_selected_model('openai', self.openai_model_var.get())
            self.config.set_selected_model('gemini', self.gemini_model_var.get())
            
            # Save interval
            interval = int(self.interval_var.get())
            self.config.set('screenshot_interval', interval)
            
            # Save vision provider
            self.config.set('vision_provider', self.provider_var.get())
            
            # Save monitored categories
            monitored_categories = [
                category for category, var in self.category_vars.items()
                if var.get()
            ]
            self.config.set('monitored_categories', monitored_categories)
            
            # Save thresholds
            thresholds = {}
            for category, var in self.threshold_vars.items():
                try:
                    value = float(var.get())
                    if 0 <= value <= 1:
                        thresholds[category] = value
                    else:
                        raise ValueError(f"Threshold for {category} must be between 0 and 1")
                except ValueError as e:
                    messagebox.showerror(
                        "Error",
                        str(e)
                    )
                    return
            self.config.set('content_thresholds', thresholds)
            
            # Save email settings
            email_settings = {
                        'smtp_server': self.smtp_server_var.get(),
                        'smtp_port': self.smtp_port_var.get(),
                        'sender_email': self.sender_email_var.get(),
                        'sender_password': self.sender_password_var.get(),
                        'parent_email': self.parent_email_var.get()
                    }
            self.config.set('email_settings', email_settings)
            
            self.destroy()
        except ValueError:
            messagebox.showerror(
                "Error",
                "Please enter valid values for all fields"
            )
