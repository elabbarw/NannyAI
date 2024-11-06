import json
import os
from utils.logger import get_logger
from keyrings.alt.file import PlaintextKeyring

class ConfigManager:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_file = "data/config.json"
        self.keyring = PlaintextKeyring()
        self._initialize_api_keys()
        self.config = self._load_config()

    def _initialize_api_keys(self):
        """Initialize API keys from environment variables if not already set"""
        try:
            # Check for OpenAI key
            if not self.keyring.get_password("screen_monitor", "openai_api_key"):
                openai_key = os.environ.get('OPENAI_API_KEY')
                if openai_key:
                    self.keyring.set_password("screen_monitor", "openai_api_key", openai_key)

            # Check for Gemini key
            if not self.keyring.get_password("screen_monitor", "gemini_api_key"):
                gemini_key = os.environ.get('GEMINI_API_KEY')
                if gemini_key:
                    self.keyring.set_password("screen_monitor", "gemini_api_key", gemini_key)
        except Exception as e:
            self.logger.error(f"Failed to initialize API keys: {str(e)}")

    def _load_config(self):
        """Load configuration from file"""
        default_config = {
            'monitoring_enabled': False,
            'screenshot_interval': 30,
            'vision_provider': 'openai',
            'api_keys': {},
            'model_settings': {
                'openai': {
                    'available_models': ['gpt-4o','gpt-4o-mini'],
                    'selected_model': 'gpt-4o-mini'
                },
                'gemini': {
                    'available_models': ['gemini-1.5-flash-8b','gemini-1.5-flash-002','gemini-1.5-pro-002'],
                    'selected_model': 'gemini-1.5-flash-8b'
                }
            },
            'email_settings': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'sender_email': '',
                'sender_password': '',
                'parent_email': ''
            },
            'content_thresholds': {
                'violence': 0.7,
                'adult': 0.7,
                'hate': 0.7,
                'drugs': 0.7,
                'gambling': 0.7
            },
            'monitored_categories': [
                'violence',
                'adult',
                'hate',
                'drugs',
                'gambling'
            ]
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Load API keys from keyring
                    config['api_keys'] = {}
                    for provider in ['openai', 'gemini']:
                        key = self.keyring.get_password("screen_monitor", f"{provider}_api_key")
                        if key:
                            config['api_keys'][provider] = key
                    return config
            return default_config
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return default_config

    def save(self):
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Create a copy of config to save
            save_config = self.config.copy()
            
            # Remove API keys from the config file
            if 'api_keys' in save_config:
                del save_config['api_keys']
            
            with open(self.config_file, 'w') as f:
                json.dump(save_config, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")
            return False

    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
        self.save()

    def get_api_key(self, provider):
        """Get API key for specified provider"""
        try:
            key = self.keyring.get_password("screen_monitor", f"{provider}_api_key")
            if not key:
                # Fallback to environment variables
                env_key = os.environ.get(f'{provider.upper()}_API_KEY')
                if env_key:
                    self.set_api_key(provider, env_key)
                    return env_key
            return key
        except Exception as e:
            self.logger.error(f"Failed to get API key: {str(e)}")
            # Fallback to environment variables
            return os.environ.get(f'{provider.upper()}_API_KEY')

    def set_api_key(self, provider, key):
        """Set API key for specified provider"""
        try:
            if key:
                self.keyring.set_password("screen_monitor", f"{provider}_api_key", key)
            else:
                try:
                    self.keyring.delete_password("screen_monitor", f"{provider}_api_key")
                except:
                    pass
            return True
        except Exception as e:
            self.logger.error(f"Failed to set API key: {str(e)}")
            return False

    def get_model_settings(self, provider):
        """Get model settings for specified provider"""
        model_settings = self.config.get('model_settings', {})
        return model_settings.get(provider, {
            'available_models': [],
            'selected_model': None
        })

    def set_selected_model(self, provider, model):
        """Set selected model for specified provider"""
        if 'model_settings' not in self.config:
            self.config['model_settings'] = {}
        if provider not in self.config['model_settings']:
            self.config['model_settings'][provider] = {
                'available_models': [],
                'selected_model': None
            }
        self.config['model_settings'][provider]['selected_model'] = model
        self.save()
