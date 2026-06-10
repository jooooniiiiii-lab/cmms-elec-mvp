"""
gui/settings_tab.py — Settings tab for CMMS Desktop App.
Tab 3 of 3: Configuration management for API keys and service credentials.
"""

import customtkinter as ctk
from typing import Any


class SettingsTab(ctk.CTkFrame):
    """Settings tab for managing API keys and service configuration."""

    CONFIG_KEYS = [
        ("GEMINI_API_KEY", "Gemini API Key", True),
        ("META_ACCESS_TOKEN", "Meta WhatsApp Access Token", True),
        ("WHATSAPP_PHONE_ID", "WhatsApp Phone Number ID", False),
        ("FIREBASE_DB_URL", "Firebase Database URL", False),
    ]

    def __init__(self, parent: ctk.CTkFrame, config_manager: Any, app_ref: Any) -> None:
        super().__init__(parent)
        self.config_manager = config_manager
        self.app_ref = app_ref
        self.entry_widgets: dict[str, ctk.CTkEntry] = {}
        self.status_labels: dict[str, ctk.CTkLabel] = {}

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Build the settings tab UI."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="الإعدادات - Settings",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        header.pack(pady=(20, 10), anchor="w", padx=20)

        # Settings Form Section
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=20, pady=(0, 10))
        form_frame.grid_columnconfigure(0, weight=1)

        for idx, (key, label_text, is_secret) in enumerate(self.CONFIG_KEYS):
            # Label
            label = ctk.CTkLabel(form_frame, text=label_text, font=ctk.CTkFont(size=13))
            label.grid(row=idx * 2, column=0, sticky="w", padx=15, pady=(15 if idx == 0 else 5, 0))

            # Entry
            entry = ctk.CTkEntry(
                form_frame,
                show="*" if is_secret else "",
                width=500,
                font=ctk.CTkFont(size=13),
            )
            entry.grid(row=idx * 2 + 1, column=0, sticky="ew", padx=15, pady=(0, 5))
            self.entry_widgets[key] = entry

        # Save Button
        save_btn = ctk.CTkButton(
            form_frame,
            text="حفظ الإعدادات - Save Settings",
            command=self._on_save,
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
        )
        save_btn.grid(row=len(self.CONFIG_KEYS) * 2, column=0, pady=20, padx=15, sticky="ew")

        # Status Section
        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill="x", padx=20, pady=(0, 20))
        status_frame.grid_columnconfigure(0, weight=1)

        status_header = ctk.CTkLabel(
            status_frame,
            text="حالة الإعدادات - Configuration Status",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        status_header.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10))

        for idx, (key, label_text, _) in enumerate(self.CONFIG_KEYS):
            status_label = ctk.CTkLabel(
                status_frame,
                text="",
                font=ctk.CTkFont(size=13),
                anchor="w",
            )
            status_label.grid(row=idx + 1, column=0, sticky="ew", padx=15, pady=3)
            self.status_labels[key] = status_label

    def _on_save(self) -> None:
        """Handle save button click."""
        for key, _, _ in self.CONFIG_KEYS:
            entry = self.entry_widgets[key]
            value = entry.get().strip()
            self.config_manager.set(key, value)

        self.config_manager.save()

        # Show success popup
        self._show_success_popup()

        # Refresh all tabs
        if hasattr(self.app_ref, "refresh_all"):
            self.app_ref.refresh_all()
        else:
            self.refresh()

    def _show_success_popup(self) -> None:
        """Show a success confirmation popup."""
        popup = ctk.CTkToplevel(self)
        popup.title("تم الحفظ - Saved")
        popup.geometry("400x200")
        popup.resizable(False, False)
        popup.grab_set()

        # Center on parent
        self._center_window(popup, 400, 200)

        msg = ctk.CTkLabel(
            popup,
            text="✅ تم حفظ الإعدادات\nSettings Saved Successfully",
            font=ctk.CTkFont(size=16),
            justify="center",
        )
        msg.pack(expand=True, pady=30)

        close_btn = ctk.CTkButton(
            popup,
            text="موافق - OK",
            command=popup.destroy,
            width=120,
            height=35,
        )
        close_btn.pack(pady=(0, 20))

    def _center_window(self, window: ctk.CTkToplevel, width: int, height: int) -> None:
        """Center a window on the parent."""
        window.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()

        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def refresh(self) -> None:
        """Refresh all entry fields and status display from config."""
        def _do_refresh() -> None:
            for key, _, _ in self.CONFIG_KEYS:
                entry = self.entry_widgets[key]
                value = self.config_manager.get(key, "")
                entry.delete(0, "end")
                entry.insert(0, value)

                status_label = self.status_labels[key]
                if self.config_manager.get(key):
                    status_label.configure(
                        text=f"{key}: ✅ متاح",
                        text_color="#4caf50",
                    )
                else:
                    status_label.configure(
                        text=f"{key}: ❌ غير مضبوط",
                        text_color="#f44336",
                    )

        # Thread-safe UI update
        toplevel = self.winfo_toplevel()
        if toplevel:
            toplevel.after(0, _do_refresh)