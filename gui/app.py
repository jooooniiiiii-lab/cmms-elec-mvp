"""
gui/app.py — Main application window for CMMS Desktop App.
Creates the CTk window with tabbed interface containing Dashboard,
Task Manager, and Settings tabs.
"""

import customtkinter as ctk
from typing import Any


class MainApp:
    """Main application orchestrating the 3-tab CMMS interface."""

    def __init__(
        self,
        db_manager: Any,
        whatsapp_handler: Any,
        gemini_agent: Any,
        firebase_bridge: Any,
        config_manager: Any,
    ) -> None:
        # Store manager references
        self.db = db_manager
        self.wh = whatsapp_handler
        self.ga = gemini_agent
        self.fb = firebase_bridge
        self.cfg = config_manager

        # Window setup
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.window = ctk.CTk()
        self.window.title("CMMS - نظام إدارة الصيانة")
        self._center_window(1000, 700)
        self.window.minsize(900, 600)

        # Tab view
        self.tab_view = ctk.CTkTabview(self.window)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        tab_dashboard = self.tab_view.add("لوحة القيادة")   # Dashboard
        tab_tasks = self.tab_view.add("إدارة المهام")        # Task Manager
        tab_settings = self.tab_view.add("الإعدادات")         # Settings

        # Lazy imports to avoid circular dependencies
        from gui.dashboard_tab import DashboardTab
        from gui.task_manager_tab import TaskManagerTab
        from gui.settings_tab import SettingsTab

        # Instantiate tabs
        self.dashboard = DashboardTab(tab_dashboard, self.db, self)
        self.dashboard.pack(fill="both", expand=True)

        self.task_manager = TaskManagerTab(tab_tasks, self.db, self.wh, self)
        self.task_manager.pack(fill="both", expand=True)

        self.settings = SettingsTab(tab_settings, self.cfg, self)
        self.settings.pack(fill="both", expand=True)

    # ── Window management ───────────────────────────────────────

    def _center_window(self, width: int, height: int) -> None:
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    # ── Public API ──────────────────────────────────────────────

    def refresh_all(self) -> None:
        """Refresh all tabs from database."""

        def _do_refresh() -> None:
            try:
                self.dashboard.refresh()
            except Exception:
                pass
            try:
                self.task_manager.refresh()
            except Exception:
                pass
            try:
                self.settings.refresh()
            except Exception:
                pass

        try:
            self.window.after(0, _do_refresh)
        except Exception:
            _do_refresh()

    def show_alert(self, title: str, message: str) -> None:
        """Show a modal alert popup."""

        def _show() -> None:
            popup = ctk.CTkToplevel(self.window)
            popup.title(title)
            popup.geometry("450x220")
            popup.resizable(False, False)
            popup.grab_set()

            popup.update_idletasks()
            pw = self.window.winfo_width()
            ph = self.window.winfo_height()
            px = self.window.winfo_x() + (pw - 450) // 2
            py = self.window.winfo_y() + (ph - 220) // 2
            popup.geometry(f"+{px}+{py}")

            ctk.CTkLabel(
                popup,
                text=message,
                font=ctk.CTkFont(size=15),
                justify="center",
                wraplength=400,
            ).pack(expand=True, pady=30)

            ctk.CTkButton(
                popup,
                text="موافق - OK",
                command=popup.destroy,
                width=120,
                height=35,
            ).pack(pady=(0, 20))

        try:
            self.window.after(0, _show)
        except Exception:
            pass

    def run(self) -> None:
        """Start the GUI main loop."""
        self.window.mainloop()

    def stop(self) -> None:
        """Clean up resources and close window."""
        try:
            self.window.destroy()
        except Exception:
            pass
