"""Configuration management for PAYADOR.

This module handles all configuration-related functionality including
reading config files, setting up paths, and managing global settings.
"""

import configparser
import time

PATH_GAMELOGS = 'logs'

def load_config():
    """Load configuration from config.ini file."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

def get_language(config):
    """Get the language setting from config."""
    return config['Options']['Language']

def get_generation_mode(config):
    """Get the generation mode from config."""
    return config['Options'].get('GenerationMode', 'preset')

def get_model_names(config):
    """Get model names from config."""
    reasoning_model_name = config['Models']['ReasoningModel']
    narrative_model_name = config['Models']['NarrativeModel']
    return reasoning_model_name, narrative_model_name

def create_log_filename():
    """Create a unique log filename based on current timestamp."""
    timestamp = time.time()
    today = time.gmtime(timestamp)
    return f"{today[0]}_{today[1]}_{today[2]}_{str(int(time.time()))[-5:]}.json"

def get_world_id(config):
    """Get the world ID from config."""
    return config["Options"]["WorldID"]
