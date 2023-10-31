import os
import importlib
from loguru import logger as log

from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.DeckManagement.HelperMethods import get_last_dir

class PluginManager:
    action_index = {}
    def __init__(self):
        pass

    def load_plugins(self):
        # get all folders in plugins folder
        folders = os.listdir("plugins")
        for folder in folders:
            # path = os.path.join("plugins", folder, f"{folder}.py")
            # Import main module
            importlib.import_module(f"plugins.{folder}.main")

        # Get all classes extending from PluginBase and generate objects for them
        print(self.init_plugins())

    def init_plugins(self):
        subclasses = PluginBase.__subclasses__()
        for subclass in subclasses:
            obj = subclass()

    def generate_action_index(self):
        plugins = self.get_plugins()
        for plugin in plugins.keys():
            for action in plugins[plugin]["object"].ACTIONS.keys():
                path = plugins[plugin]["folder-path"]
                # Remove everything except the last folder
                path = get_last_dir(path)
                self.action_index[f"{path}::{action}"] = plugins[plugin]["object"].ACTIONS[action]
            
    def get_plugins(self):
        return PluginBase.plugins
    
    def get_actions_for_plugin(self, plugin_name):
        return PluginBase.plugins[plugin_name]["object"].ACTIONS
    
    def get_action_from_action_string(self, action_string: str):
        """
        Example string: dev_core447_MediaPlugin::Pause
        """
        print(self.action_index)
        # plugin_name, action_name = action_string.split("::")
        try:
            return self.action_index[action_string]
        except KeyError:
            log.warning(f"Requested action {action_string} not found, skipping...")
            return None
        
    def get_action_string_from_action(self, action):
        for key, value in self.action_index.items():
            if value == action:
                return key