"""Configuration loader"""
import yaml
import os


def load_conference_config():
    """Load conference configurations"""
    config_path = os.path.join(os.path.dirname(__file__), 'conferences.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_settings():
    """Load global settings"""
    config_path = os.path.join(os.path.dirname(__file__), 'settings.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
