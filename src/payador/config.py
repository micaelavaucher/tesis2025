"""Configuration management for PAYADOR.

This module handles all configuration-related functionality including
reading config files, setting up paths, and managing global settings.
Only application-level configurations are managed here.
User-level configurations are handled via Streamlit session state.
"""

import configparser
import time

PATH_GAMELOGS = 'logs'

def load_config():
    """Load configuration from config.ini file."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

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

def get_enable_rag(config):
    """Get the RAG enable setting from config."""
    return config["Options"].getboolean("EnableRAG", fallback=True)

def get_debug(config):
    """Get the debug setting from config."""
    return config["Options"].getboolean("Debug", fallback=False)
