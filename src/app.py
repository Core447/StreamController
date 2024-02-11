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
# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk

# Import Python modules
from loguru import logger as log
import os

# Import own modules
from src.windows.mainWindow.mainWindow import MainWindow
from src.windows.AssetManager.AssetManager import AssetManager
from src.windows.Store.Store import Store
from src.windows.Shortcuts.Shortcuts import ShortcutsWindow

# Import globals
import globals as gl

class App(Adw.Application):
    def __init__(self, deck_manager, **kwargs):
        super().__init__(**kwargs)
        self.deck_manager = deck_manager
        self.connect("activate", self.on_activate)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(os.path.join(gl.top_level_dir, "style.css"))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def on_activate(self, app):
        log.trace("running: on_activate")
        self.main_win = MainWindow(application=app, deck_manager=self.deck_manager)
        self.main_win.present()

        
        self.shortcuts = ShortcutsWindow(app=app, application=app)
        # self.shortcuts.present()

        log.success("Finished loading app")

    def let_user_select_asset(self, default_path, callback_func=None, *callback_args, **callback_kwargs):
        self.asset_manager = AssetManager(application=self, main_window=self.main_win)
        self.asset_manager.show_for_path(default_path, callback_func, *callback_args, **callback_kwargs)