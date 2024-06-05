"""Add all menus and commands to Nuke's ui"""

# Import third-party modules
import nuke

# Import local modules
from smartCache import osl as smartcache
from smartCache import cache
from smartCache import check
from smartCache.mvc.styles import ICONS


def add_to_ui():
    """Add menu and commands to Nuke's UI."""
    menu = nuke.menu("Nuke").addMenu("cragl/smartCache", icon=ICONS["logo"])

    menu.addCommand("Create smartCache", smartcache.create_smartCache, "Shift+C")
    menu.addCommand("Open cache manager", smartcache.show_main)
    menu.addSeparator()
    menu.addCommand("Render selected caches", smartcache.show_render_dialog)
    menu.addCommand("Check selected cache nodes", check.check_selected_cache_nodes_still_valid)
    menu.addSeparator()
    menu.addCommand("Set selected to cached", cache.set_selected_to_cached, "Alt+Shift+C")
    menu.addCommand("Set selected to live", cache.set_selected_to_live, "Alt+Shift+L")
    menu.addSeparator()
    menu.addCommand("Delete selected caches", cache.delete_selected_caches)
    menu.addSeparator()
    menu.addCommand("Settings", lambda: smartcache.show_main(main_section=False))
    menu.addSeparator()
    menu.addCommand("&about", smartcache.show_about_window)

    nodes_menu = nuke.menu("Nodes").addMenu("smartCache", ICONS["logo"])
    nodes_menu.addCommand("smartCache", smartcache.create_smartCache, "Shift+C", ICONS["diskcache_plus"])


add_to_ui()
