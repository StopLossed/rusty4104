"""Entry point for the GTK stock screener app."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from ui.main_window import MainWindow
from utils.logging import configure_logging


class StockScreenerApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.rusty4104.StockScreener")

    def do_activate(self) -> None:
        window = self.props.active_window
        if not window:
            window = MainWindow(self)
        window.present()


def main() -> None:
    configure_logging()
    app = StockScreenerApplication()
    app.run(None)


if __name__ == "__main__":
    main()
