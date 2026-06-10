"""
gui/dashboard_tab.py — Dashboard tab for CMMS Desktop App.
Tab 1 of 3: Worker status grid, active tasks, summary stats.
"""

import customtkinter as ctk
from datetime import date
from typing import Any


class DashboardTab(ctk.CTkFrame):
    """Dashboard showing technician status, active tasks, and summary."""

    def __init__(self, parent: ctk.CTkFrame, db_manager: Any, app_ref: Any) -> None:
        super().__init__(parent)
        self.db = db_manager
        self.app_ref = app_ref

        # Containers for dynamic content
        self.workers_container: ctk.CTkFrame | None = None
        self.tasks_container: ctk.CTkFrame | None = None
        self.summary_container: ctk.CTkFrame | None = None

        self._build_ui()
        self.refresh()

    # ── Build static UI structure ───────────────────────────────

    def _build_ui(self) -> None:
        # Header
        header = ctk.CTkLabel(
            self,
            text="لوحة القيادة - Dashboard",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        header.pack(pady=(15, 5), anchor="w", padx=20)

        # Scrollable main area
        self.scroll_area = ctk.CTkScrollableFrame(self)
        self.scroll_area.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Workers section header
        workers_header = ctk.CTkLabel(
            self.scroll_area,
            text="حالة الفنيين - Worker Status",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        workers_header.pack(anchor="w", pady=(10, 5))

        self.workers_frame = ctk.CTkFrame(self.scroll_area)
        self.workers_frame.pack(fill="x", pady=(0, 15))

        # Tasks section header
        tasks_header = ctk.CTkLabel(
            self.scroll_area,
            text="المهام النشطة - Active Tasks",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        tasks_header.pack(anchor="w", pady=(10, 5))

        self.tasks_frame = ctk.CTkFrame(self.scroll_area)
        self.tasks_frame.pack(fill="x", pady=(0, 15))

        # Summary bar (bottom, outside scroll)
        self.summary_bar = ctk.CTkFrame(self, height=50)
        self.summary_bar.pack(fill="x", padx=15, pady=(0, 10))

    # ── Refresh ─────────────────────────────────────────────────

    def refresh(self) -> None:
        """Rebuild dynamic content from database."""

        def _refresh() -> None:
            # Clear dynamic content
            for w in self.workers_frame.winfo_children():
                w.destroy()
            for w in self.tasks_frame.winfo_children():
                w.destroy()
            for w in self.summary_bar.winfo_children():
                w.destroy()

            self._build_workers_section()
            self._build_tasks_section()
            self._build_summary_bar()

        try:
            self.winfo_toplevel().after(0, _refresh)
        except Exception:
            _refresh()

    # ── Workers section ─────────────────────────────────────────

    def _build_workers_section(self) -> None:
        workers = self.db.get_workers()
        today = date.today().isoformat()

        grid = ctk.CTkFrame(self.workers_frame)
        grid.pack(fill="x", padx=10, pady=10)

        # Column headers
        cols = ["الاسم - Name", "الهاتف - Phone", "العقد - Contract",
                "نهاية العقد - End Date", "الحالة - Status", "الإجراءات - Actions"]
        for ci, col_name in enumerate(cols):
            lbl = ctk.CTkLabel(
                grid, text=col_name,
                font=ctk.CTkFont(size=13, weight="bold"),
            )
            lbl.grid(row=0, column=ci, padx=8, pady=5, sticky="w")

        for ri, w in enumerate(workers):
            phone = w["phone"]
            name = w["name"]
            ctype = w["contract_type"]
            end = w["contract_end_date"]
            is_active = w["is_active"]

            # Determine status
            expired = (ctype == "CDD" and end <= today)
            if expired:
                status_text = "⚫ منتهي العقد - Expired"
                status_color = "#616161"
            elif not is_active:
                status_text = "🔴 يوم استرداد - Recovery"
                status_color = "#f44336"
            else:
                status_text = "🟢 متاح - Available"
                status_color = "#4caf50"

            row_fg = "#1e1e1e" if ri % 2 == 0 else "#2d2d2d"
            for ci, val in enumerate([name, phone, ctype, end]):
                lbl = ctk.CTkLabel(
                    grid, text=str(val),
                    font=ctk.CTkFont(size=12),
                    fg_color=row_fg,
                )
                lbl.grid(row=ri + 1, column=ci, padx=8, pady=3, sticky="w")

            # Status label
            status_lbl = ctk.CTkLabel(
                grid, text=status_text,
                font=ctk.CTkFont(size=12),
                text_color=status_color,
                fg_color=row_fg,
            )
            status_lbl.grid(row=ri + 1, column=4, padx=8, pady=3, sticky="w")

            # Action button
            if not expired and is_active:
                btn = ctk.CTkButton(
                    grid, text="منح يوم استرداد",
                    font=ctk.CTkFont(size=11),
                    fg_color="#e65100",
                    hover_color="#bf360c",
                    width=130, height=28,
                    command=lambda p=phone: self._grant_recovery(p),
                )
                btn.grid(row=ri + 1, column=5, padx=8, pady=3)
            else:
                placeholder = ctk.CTkLabel(
                    grid, text="—", fg_color=row_fg, font=ctk.CTkFont(size=12)
                )
                placeholder.grid(row=ri + 1, column=5, padx=8, pady=3)

    def _grant_recovery(self, phone: str) -> None:
        self.db.set_recovery_day(phone)
        self.refresh()

    # ── Tasks section ───────────────────────────────────────────

    def _build_tasks_section(self) -> None:
        all_tasks = self.db.get_tasks()
        active_tasks = [t for t in all_tasks if t["status"] in ("PENDING", "IN_PROGRESS")]

        if not active_tasks:
            lbl = ctk.CTkLabel(
                self.tasks_frame,
                text="لا توجد مهام نشطة - No active tasks",
                font=ctk.CTkFont(size=13, slant="italic"),
                text_color="#888888",
            )
            lbl.pack(pady=20)
            return

        for task in active_tasks:
            card = ctk.CTkFrame(self.tasks_frame, border_width=1, corner_radius=8)
            card.pack(fill="x", padx=10, pady=5)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=8)

            # Task description
            desc = ctk.CTkLabel(
                inner, text=task["task_description"],
                font=ctk.CTkFont(size=13, weight="bold"),
                wraplength=500, justify="right",
            )
            desc.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 5))

            # Workers + duration
            info = ctk.CTkLabel(
                inner,
                text=f"👥 {task['assigned_workers']}  |  ⏱ {task['estimated_duration']} دقيقة",
                font=ctk.CTkFont(size=11),
                text_color="#aaaaaa",
            )
            info.grid(row=1, column=0, sticky="w")

            # Progress bar
            progress = ctk.CTkProgressBar(inner, width=200)
            progress.grid(row=1, column=1, padx=10)
            if task["status"] == "IN_PROGRESS":
                progress.set(0.5)
            else:
                progress.set(0.0)

            # Status badge
            if task["status"] == "PENDING":
                badge_color = "#f9a825"
                badge_text = "PENDING"
            else:
                badge_color = "#1e88e5"
                badge_text = "IN PROGRESS"

            badge = ctk.CTkLabel(
                inner, text=badge_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=badge_color,
            )
            badge.grid(row=1, column=2, sticky="e")

    # ── Summary bar ─────────────────────────────────────────────

    def _build_summary_bar(self) -> None:
        workers = self.db.get_workers()
        today = date.today().isoformat()
        stats = self.db.get_task_statistics()

        total = len(workers)
        active = sum(1 for w in workers if w["is_active"]
                     and not (w["contract_type"] == "CDD" and w["contract_end_date"] <= today))
        on_recovery = sum(1 for w in workers if not w["is_active"]
                          and not (w["contract_type"] == "CDD" and w["contract_end_date"] <= today))
        expired = sum(1 for w in workers
                      if w["contract_type"] == "CDD" and w["contract_end_date"] <= today)

        texts = [
            f"👥 الإجمالي: {total}",
            f"🟢 النشطون: {active}",
            f"🔴 استرداد: {on_recovery}",
            f"⚫ منتهيون: {expired}",
            f"📋 المهام: {stats['total']} | ⏳ {stats['pending']} | 🔄 {stats['in_progress']} | ✅ {stats['completed']} | ❌ {stats['failed']}",
        ]

        for i, text in enumerate(texts):
            lbl = ctk.CTkLabel(
                self.summary_bar,
                text=text,
                font=ctk.CTkFont(size=12),
                padx=12,
            )
            lbl.pack(side="left", padx=5, pady=10)
