"""
Configuration management for build system.
"""

import yaml
import sys
from pathlib import Path

class BuildConfig:
    """Manages build configuration from cicd.yaml"""
    
    def __init__(self, config_path='cicd.yaml'):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"✅ Loaded {self.config_path}")
            return config
        except Exception as e:
            print(f"❌ ERROR: Could not load {self.config_path}: {e}")
            sys.exit(1)
    
    def save_config(self):
        """Save configuration back to YAML file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"❌ ERROR: Could not save {self.config_path}: {e}")
            return False
    
    def get_version_string(self):
        """Get current version as string."""
        v = self.config['version']
        return f"{v['major']}.{v['minor']}.{v['patch']}"
    
    def increment_version(self):
        """Increment patch version (with rollover to minor)."""
        self.config['version']['patch'] += 1
        if self.config['version']['patch'] > 99:
            self.config['version']['patch'] = 0
            self.config['version']['minor'] += 1
        return self.get_version_string()
    
    def get_ssh_config(self):
        """Get SSH configuration."""
        return self.config.get('ssh', {})
    
    def get_nuitka_config(self):
        """Get Nuitka configuration."""
        return self.config.get('nuitka', {})
