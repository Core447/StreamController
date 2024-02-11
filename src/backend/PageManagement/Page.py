"""
Author: Core447
Year: 2023

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This programm comes with ABSOLUTELY NO WARRANTY!

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import os
import json
from loguru import logger as log
from copy import copy
import shutil

# Import globals
import globals as gl

class Page:
    def __init__(self, json_path, deck_controller, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dict = {}

        self.json_path = json_path
        self.deck_controller = deck_controller

        # Dir that contains all actions this allows us to keep them at reload
        self.action_objects = {}

        self.load(load_from_file=True)

    def get_name(self) -> str:
        return os.path.splitext(os.path.basename(self.json_path))[0]

    def load(self, load_from_file: bool = False):
        if load_from_file:
            with open(self.json_path) as f:
                self.dict.update(json.load(f))
        self.load_action_objects()

        # Call on_ready for all actions
        self.call_actions_ready()

    def save(self):
        # Make backup in case something goes wrong
        self.make_backup()

        without_objects = self.get_without_action_objects()
        # Make keys last element
        self.move_key_to_end(without_objects, "keys")
        with open(self.json_path, "w") as f:
            json.dump(without_objects, f, indent=4)

    def make_backup(self):
        os.makedirs(os.path.join(gl.DATA_PATH, "pages","backups"), exist_ok=True)

        src_path = self.json_path
        dst_path = os.path.join(gl.DATA_PATH, "pages","backups", os.path.basename(src_path))

        # Check if json in src is valid
        with open(src_path) as f:
            try:
                json.load(f)
            except json.decoder.JSONDecodeError as e:
                log.error(f"Invalid json in {src_path}: {e}")
                return

        shutil.copy2(src_path, dst_path)

    def move_key_to_end(self, dictionary, key):
        if key in self.dict:
            value = self.dict.pop(key)
            self.dict[key] = value

    def set_background(self, file_path, loop=True, fps=30, show=True):
        background = {
            "show": show,
            "path": file_path,
            "loop": loop,
            "fps": fps
        }
        self.dict["background"] = background
        self.save()

    def load_action_objects(self):
        # Store loaded action objects
        self.loaded_action_objects = copy(self.action_objects)

        # Load action objects
        self.action_objects = {}
        for key in self.dict.get("keys", {}):
            if "actions" not in self.dict["keys"][key]:
                continue
            for i, action in enumerate(self.dict["keys"][key]["actions"]):
                action_class = gl.plugin_manager.get_action_from_action_string(action["name"])
                
                self.action_objects.setdefault(key, {})
                if action_class is None:
                    self.action_objects[key][i] = action["name"].split("::")[0]
                    continue

                old_object = self.action_objects[key].get(i)
                if isinstance(old_object, action_class):
                    # Action already exists - keep it
                    continue
                
                if i in self.loaded_action_objects.get(key, []):
                    if not isinstance(self.loaded_action_objects.get(key, [i])[i], str):
                        self.action_objects[key][i] = self.loaded_action_objects[key][i]
                        continue

                action_object = action_class(deck_controller=self.deck_controller, page=self, coords=key)
                self.action_objects[key][i] = action_object

    def remove_plugin_action_objects(self, plugin_id: str) -> bool:
        plugin_obj = gl.plugin_manager.get_plugin_by_id(plugin_id)
        if plugin_obj is None:
            return False
        for key in list(self.action_objects.keys()):
            for index in list(self.action_objects[key].keys()):
                if isinstance(self.action_objects[key][index], str):
                    continue
                if self.action_objects[key][index].PLUGIN_BASE == plugin_obj:
                    # Remove object
                    action = self.action_objects[key][index]
                    del action

                    # Remove action from action_objects
                    del self.action_objects[key][index]

        return True
    
    def get_keys_with_plugin(self, plugin_id: str):
        plugin_obj = gl.plugin_manager.get_plugin_by_id(plugin_id)
        if plugin_obj is None:
            return
        
        keys = []
        for key in self.action_objects:
            for action in self.action_objects[key].values():
                if isinstance(action, str):
                    continue
                if action.PLUGIN_BASE == plugin_obj:
                    keys.append(key)

        return keys

    def remove_plugin_actions_from_json(self, plugin_id: str): 
        for key in self.dict["keys"]:
            for i, action in enumerate(self.dict["keys"][key]["actions"]):
                # Check if the action is from the plugin by using the plugin id before the action name
                if self.dict["keys"][key]["actions"].split("::")[0] == plugin_id:
                    del self.dict["keys"][key]["actions"][i]

        self.save()

    def get_without_action_objects(self):
        dictionary = copy(self.dict)
        for key in dictionary.get("keys", {}):
            if "actions" not in dictionary["keys"][key]:
                continue
            for action in dictionary["keys"][key]["actions"]:
                if "object" in action:
                    del action["object"]

        return dictionary

    def get_all_actions(self):
        actions = []
        for key in self.action_objects:
            for action in self.action_objects[key].values():
                actions.append(action)
        return actions
    
    def get_all_actions_for_key(self, key):
        actions = []
        if key in self.action_objects:
            for action in self.action_objects[key].values():
                actions.append(action)
        return actions
    
    def get_settings_for_action(self, action_object, coords: list = None):
        if coords is None:
            for key in self.dict["keys"]:
                for i, action in enumerate(self.dict["keys"][key]["actions"]):
                    if not key in self.action_objects:
                        break
                    if not i in self.action_objects[key]:
                        break
                    if self.action_objects[key][i] == action_object:
                        return action["settings"]
        else:
            for i, action in enumerate(self.dict["keys"][coords]["actions"]):
                if not coords in self.action_objects:
                    break
                if not i in self.action_objects[coords]:
                    break
                if self.action_objects[coords][i] == action_object:
                    return action["settings"]
        return {}
                
    def set_settings_for_action(self, action_object, settings: dict, coords: list = None):
        if coords is None:
            for key in self.dict["keys"]:
                for i, action in enumerate(self.dict["keys"][key]["actions"]):
                    if self.action_objects[key][i] == action_object:
                        self.dict["keys"][key]["actions"][i]["settings"] = settings
        else:
            for i, action in enumerate(self.dict["keys"][coords]["actions"]):
                if self.action_objects[coords][i] == action_object:
                    self.dict["keys"][coords]["actions"][i]["settings"] = settings

    def has_key_an_image_controlling_action(self, page_coords: str):
        if page_coords not in self.action_objects:
            return False
        for action in self.action_objects[page_coords].values():
            if action.CONTROLS_KEY_IMAGE:
                print(action)
                return True
        return False

    def call_actions_ready(self):
        for action in self.get_all_actions():
            if hasattr(action, "on_ready"):
                if not action.on_ready_called:
                    action.on_ready()
                    action.on_ready_called = True

    def get_name(self):
        return os.path.splitext(os.path.basename(self.json_path))[0]
    
    def get_pages_with_same_json(self, get_self: bool = False) -> list:
        pages: list[Page]= []
        for controller in gl.deck_manager.deck_controller:
            if controller.active_page is None:
                continue
            if controller.active_page == self and not get_self:
                continue
            if controller.active_page.json_path == self.json_path:
                pages.append(controller.active_page)
        return pages
    
    def reload_similar_pages(self, page_coords=None, reload_self: bool = False):
        self.save()
        for page in self.get_pages_with_same_json(get_self=reload_self):
            page.load(load_from_file=True)
            if page_coords is None:
                page.deck_controller.reload_page()
            else:
                # Reload only given key
                page.deck_controller.load_key(page_coords)