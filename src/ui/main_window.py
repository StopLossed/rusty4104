"""GTK4 main window for the stock screener."""

from __future__ import annotations

import os
import threading
from dataclasses import asdict
from datetime import date
from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib, GObject, Gtk

from data.alpaca_client import AlpacaDataProvider
from screener.engine import ScanConfig, ScanResult, ScreenerEngine


class ResultRow(GObject.Object):
    __gtype_name__ = "ResultRow"

    symbol = GObject.Property(type=str)
    last_close = GObject.Property(type=float)
    signal_type = GObject.Property(type=str)
    signal_age = GObject.Property(type=int)
    macd = GObject.Property(type=float)
    signal_line = GObject.Property(type=float)
    histogram = GObject.Property(type=float)
    fast_ma = GObject.Property(type=float)
    slow_ma = GObject.Property(type=float)
    last_bar_time = GObject.Property(type=str)

    def __init__(self, result: ScanResult):
        super().__init__()
        self.raw = result
        self.symbol = result.symbol
        self.last_close = float(result.last_close)
        self.signal_type = result.signal_type
        self.signal_age = int(result.signal_age)
        self.macd = float(result.macd or 0.0)
        self.signal_line = float(result.signal_line or 0.0)
        self.histogram = float(result.histogram or 0.0)
        self.fast_ma = float(result.fast_ma or 0.0)
        self.slow_ma = float(result.slow_ma or 0.0)
        self.last_bar_time = result.last_bar_time


class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent: Gtk.Window, api_key: str, secret_key: str):
        super().__init__(title="Alpaca Settings", transient_for=parent, modal=True)
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)

        box = self.get_content_area()
        grid = Gtk.Grid(column_spacing=12, row_spacing=8, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)

        self.api_entry = Gtk.Entry(text=api_key)
        self.secret_entry = Gtk.Entry(text=secret_key)
        self.secret_entry.set_visibility(False)

        grid.attach(Gtk.Label(label="API Key", halign=Gtk.Align.START), 0, 0, 1, 1)
        grid.attach(self.api_entry, 1, 0, 1, 1)
        grid.attach(Gtk.Label(label="Secret Key", halign=Gtk.Align.START), 0, 1, 1, 1)
        grid.attach(self.secret_entry, 1, 1, 1, 1)

        box.append(grid)

    def get_values(self) -> tuple[str, str]:
        return self.api_entry.get_text().strip(), self.secret_entry.get_text().strip()


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app: Gtk.Application):
        super().__init__(application=app, title="Alpaca Stock Screener")
        self.set_default_size(1300, 760)

        self.api_key = os.getenv("ALPACA_API_KEY", "")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY", "")

        self.cancel_event = threading.Event()
        self.scan_thread: Optional[threading.Thread] = None

        self._build_ui()

    def _build_ui(self) -> None:
        header = Gtk.HeaderBar()
        self.set_titlebar(header)

        settings_btn = Gtk.Button(label="Settings")
        settings_btn.connect("clicked", self.on_settings_clicked)
        header.pack_end(settings_btn)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        self.set_child(root)

        panel = Gtk.Frame(label="Scan Filters")
        root.append(panel)

        panel_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        panel.set_child(panel_box)

        self.symbol_text = Gtk.TextView()
        self.symbol_text.get_buffer().set_text("AAPL\nMSFT\nNVDA\nTSLA")
        self.symbol_text.set_vexpand(False)
        self.symbol_text.set_size_request(-1, 100)
        panel_box.append(Gtk.Label(label="Symbols (paste tickers, one per line or comma-separated)", halign=Gtk.Align.START))
        panel_box.append(self.symbol_text)

        controls = Gtk.Grid(column_spacing=8, row_spacing=8)
        panel_box.append(controls)

        self.timeframe_combo = Gtk.DropDown.new_from_strings(["Day", "Hour", "Minute"])
        self.lookback_spin = Gtk.SpinButton.new_with_range(30, 2000, 1)
        self.lookback_spin.set_value(180)
        self.end_date_entry = Gtk.Entry(placeholder_text="YYYY-MM-DD (optional)")
        self.within_spin = Gtk.SpinButton.new_with_range(1, 20, 1)
        self.within_spin.set_value(1)

        self.macd_check = Gtk.CheckButton(label="Enable MACD")
        self.macd_check.set_active(True)
        self.macd_fast = Gtk.SpinButton.new_with_range(2, 50, 1)
        self.macd_slow = Gtk.SpinButton.new_with_range(3, 100, 1)
        self.macd_sig = Gtk.SpinButton.new_with_range(2, 50, 1)
        self.macd_fast.set_value(12)
        self.macd_slow.set_value(26)
        self.macd_sig.set_value(9)

        self.ma_check = Gtk.CheckButton(label="Enable MA")
        self.ma_fast = Gtk.SpinButton.new_with_range(2, 200, 1)
        self.ma_slow = Gtk.SpinButton.new_with_range(3, 400, 1)
        self.ma_fast.set_value(20)
        self.ma_slow.set_value(200)

        self.load_btn = Gtk.Button(label="Load Symbols File")
        self.load_btn.connect("clicked", self.on_load_symbols)
        self.scan_btn = Gtk.Button(label="Run Scan")
        self.scan_btn.connect("clicked", self.on_run_scan)
        self.cancel_btn = Gtk.Button(label="Cancel")
        self.cancel_btn.set_sensitive(False)
        self.cancel_btn.connect("clicked", self.on_cancel_scan)

        controls.attach(Gtk.Label(label="Timeframe"), 0, 0, 1, 1)
        controls.attach(self.timeframe_combo, 1, 0, 1, 1)
        controls.attach(Gtk.Label(label="Lookback Days"), 2, 0, 1, 1)
        controls.attach(self.lookback_spin, 3, 0, 1, 1)
        controls.attach(Gtk.Label(label="End Date"), 4, 0, 1, 1)
        controls.attach(self.end_date_entry, 5, 0, 1, 1)
        controls.attach(Gtk.Label(label="Within Last N Bars"), 6, 0, 1, 1)
        controls.attach(self.within_spin, 7, 0, 1, 1)

        controls.attach(self.macd_check, 0, 1, 1, 1)
        controls.attach(Gtk.Label(label="Fast"), 1, 1, 1, 1)
        controls.attach(self.macd_fast, 2, 1, 1, 1)
        controls.attach(Gtk.Label(label="Slow"), 3, 1, 1, 1)
        controls.attach(self.macd_slow, 4, 1, 1, 1)
        controls.attach(Gtk.Label(label="Signal"), 5, 1, 1, 1)
        controls.attach(self.macd_sig, 6, 1, 1, 1)

        controls.attach(self.ma_check, 0, 2, 1, 1)
        controls.attach(Gtk.Label(label="Fast"), 1, 2, 1, 1)
        controls.attach(self.ma_fast, 2, 2, 1, 1)
        controls.attach(Gtk.Label(label="Slow"), 3, 2, 1, 1)
        controls.attach(self.ma_slow, 4, 2, 1, 1)

        controls.attach(self.load_btn, 5, 2, 1, 1)
        controls.attach(self.scan_btn, 6, 2, 1, 1)
        controls.attach(self.cancel_btn, 7, 2, 1, 1)

        content = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        content.set_vexpand(True)
        root.append(content)

        self.store = Gio.ListStore.new(ResultRow)
        self.sort_model = Gtk.SortListModel(model=self.store)
        self.selection = Gtk.SingleSelection(model=self.sort_model)
        self.selection.connect("notify::selected-item", self.on_result_selected)

        self.column_view = Gtk.ColumnView(model=self.selection)
        for title, prop_name, fmt in [
            ("Symbol", "symbol", "{}"),
            ("Last Close", "last_close", "{:.2f}"),
            ("Signal", "signal_type", "{}"),
            ("Age", "signal_age", "{}"),
            ("MACD", "macd", "{:.4f}"),
            ("Signal Line", "signal_line", "{:.4f}"),
            ("Hist", "histogram", "{:.4f}"),
            ("Fast MA", "fast_ma", "{:.2f}"),
            ("Slow MA", "slow_ma", "{:.2f}"),
            ("Last Bar", "last_bar_time", "{}"),
        ]:
            self.column_view.append_column(self._make_text_column(title, prop_name, fmt))

        scroller = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        scroller.set_child(self.column_view)
        content.set_start_child(scroller)

        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        self.detail_label = Gtk.Label(label="Select a row to view details", wrap=True, halign=Gtk.Align.START)
        right_box.append(self.detail_label)

        self.sparkline = Gtk.DrawingArea(content_width=360, content_height=220)
        self.sparkline.set_draw_func(self.draw_sparkline)
        right_box.append(self.sparkline)
        content.set_end_child(right_box)

        self.status_label = Gtk.Label(label="Ready", xalign=0)
        root.append(self.status_label)

        self.selected_result: Optional[ScanResult] = None

    def _make_text_column(self, title: str, prop_name: str, fmt: str) -> Gtk.ColumnViewColumn:
        factory = Gtk.SignalListItemFactory()

        def on_setup(_factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
            list_item.set_child(Gtk.Label(xalign=0))

        def on_bind(_factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
            row = list_item.get_item()
            label = list_item.get_child()
            value = getattr(row, prop_name)
            label.set_text(fmt.format(value))

        factory.connect("setup", on_setup)
        factory.connect("bind", on_bind)

        column = Gtk.ColumnViewColumn(title=title, factory=factory)
        sorter = Gtk.PropertyExpression.new(ResultRow, None, prop_name)
        column.set_sorter(Gtk.StringSorter.new(expression=sorter) if prop_name in {"symbol", "signal_type", "last_bar_time"} else Gtk.NumericSorter.new(expression=sorter))
        column.set_resizable(True)
        return column

    def on_settings_clicked(self, _button: Gtk.Button) -> None:
        dialog = SettingsDialog(self, self.api_key, self.secret_key)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.api_key, self.secret_key = dialog.get_values()
        dialog.destroy()

    def on_load_symbols(self, _button: Gtk.Button) -> None:
        chooser = Gtk.FileChooserNative(title="Load Symbols", action=Gtk.FileChooserAction.OPEN, transient_for=self)
        response = chooser.run()
        if response == Gtk.ResponseType.ACCEPT:
            file = chooser.get_file()
            if file:
                path = file.get_path()
                if path:
                    with open(path, "r", encoding="utf-8") as f:
                        self.symbol_text.get_buffer().set_text(f.read())
        chooser.destroy()

    def on_cancel_scan(self, _button: Gtk.Button) -> None:
        self.cancel_event.set()
        self.status_label.set_text("Cancelling...")

    def _set_controls_enabled(self, enabled: bool) -> None:
        for widget in [
            self.scan_btn,
            self.load_btn,
            self.timeframe_combo,
            self.lookback_spin,
            self.end_date_entry,
            self.within_spin,
            self.macd_check,
            self.macd_fast,
            self.macd_slow,
            self.macd_sig,
            self.ma_check,
            self.ma_fast,
            self.ma_slow,
            self.symbol_text,
        ]:
            widget.set_sensitive(enabled)
        self.cancel_btn.set_sensitive(not enabled)

    def on_run_scan(self, _button: Gtk.Button) -> None:
        if self.scan_thread and self.scan_thread.is_alive():
            return

        if not self.api_key or not self.secret_key:
            self.status_label.set_text("Missing API credentials. Set env vars or use Settings.")
            return

        text_buffer = self.symbol_text.get_buffer()
        raw_symbols = text_buffer.get_text(text_buffer.get_start_iter(), text_buffer.get_end_iter(), True)

        end_date = None
        raw_end_date = self.end_date_entry.get_text().strip()
        if raw_end_date:
            try:
                end_date = date.fromisoformat(raw_end_date)
            except ValueError:
                self.status_label.set_text("Invalid end date format, expected YYYY-MM-DD")
                return

        config = ScanConfig(
            symbols_text=raw_symbols,
            timeframe=self.timeframe_combo.get_selected_item().get_string(),
            lookback_days=self.lookback_spin.get_value_as_int(),
            end_date=end_date,
            within_bars=self.within_spin.get_value_as_int(),
            use_macd=self.macd_check.get_active(),
            macd_fast=self.macd_fast.get_value_as_int(),
            macd_slow=self.macd_slow.get_value_as_int(),
            macd_signal=self.macd_sig.get_value_as_int(),
            use_ma=self.ma_check.get_active(),
            ma_fast=self.ma_fast.get_value_as_int(),
            ma_slow=self.ma_slow.get_value_as_int(),
        )

        if not config.use_macd and not config.use_ma:
            self.status_label.set_text("Enable at least one filter (MACD or MA).")
            return

        self.cancel_event.clear()
        self._set_controls_enabled(False)
        self.status_label.set_text("Starting scan...")
        self.store.remove_all()

        def worker() -> None:
            try:
                provider = AlpacaDataProvider(self.api_key, self.secret_key)
                engine = ScreenerEngine(provider)

                def progress_cb(done: int, total: int, matched: int) -> None:
                    GLib.idle_add(self.status_label.set_text, f"Fetched {done}/{total} symbols, matched {matched}")

                results, invalid, warnings = engine.run_scan(config, self.cancel_event, progress_cb)
                GLib.idle_add(self._on_scan_done, results, invalid, warnings)
            except Exception as exc:
                GLib.idle_add(self._on_scan_error, str(exc))

        self.scan_thread = threading.Thread(target=worker, daemon=True)
        self.scan_thread.start()

    def _on_scan_done(self, results: list[ScanResult], invalid: list[str], warnings: list[str]) -> None:
        self._set_controls_enabled(True)
        for row in sorted(results, key=lambda r: (r.signal_age, r.symbol)):
            self.store.append(ResultRow(row))

        messages = [f"Scan complete. Matches: {len(results)}"]
        if invalid:
            messages.append(f"Invalid symbols skipped: {', '.join(invalid[:10])}")
        if warnings:
            messages.append(f"Warnings: {len(warnings)} (e.g. {warnings[0]})")

        self.status_label.set_text(" | ".join(messages))

    def _on_scan_error(self, message: str) -> None:
        self._set_controls_enabled(True)
        self.status_label.set_text(f"Scan error: {message}")

    def on_result_selected(self, _selection: Gtk.SingleSelection, _param: GObject.ParamSpec) -> None:
        item = self.selection.get_selected_item()
        if item is None:
            self.selected_result = None
            self.detail_label.set_text("Select a row to view details")
            self.sparkline.queue_draw()
            return

        self.selected_result = item.raw
        self.detail_label.set_text(
            f"{item.symbol} • {item.signal_type} • age={item.signal_age} bars\n"
            f"Last close: {item.last_close:.2f} | MACD: {item.macd:.4f} | Signal: {item.signal_line:.4f}"
        )
        self.sparkline.queue_draw()

    def draw_sparkline(self, _area: Gtk.DrawingArea, ctx, width: int, height: int) -> None:
        ctx.set_source_rgb(0.12, 0.12, 0.12)
        ctx.paint()

        if not self.selected_result or len(self.selected_result.close_series) < 2:
            return

        values = self.selected_result.close_series[-120:]
        min_v = min(values)
        max_v = max(values)
        span = max(max_v - min_v, 1e-9)

        def to_xy(i: int, value: float) -> tuple[float, float]:
            x = (i / (len(values) - 1)) * (width - 10) + 5
            y = height - ((value - min_v) / span) * (height - 10) - 5
            return x, y

        ctx.set_source_rgb(0.35, 0.75, 0.95)
        x0, y0 = to_xy(0, values[0])
        ctx.move_to(x0, y0)
        for idx, value in enumerate(values[1:], start=1):
            x, y = to_xy(idx, value)
            ctx.line_to(x, y)
        ctx.set_line_width(2.0)
        ctx.stroke()
