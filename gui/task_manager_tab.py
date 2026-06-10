"""
gui/task_manager_tab.py — Task Manager tab for CMMS Desktop App.
Tab 2 of 3: Create and dispatch tasks to technicians via WhatsApp.
"""

import customtkinter as ctk
import tkinter.messagebox as tkmb
from typing import Any


class TaskManagerTab(ctk.CTkFrame):
    """Task creation form, worker assignment, and dispatch via WhatsApp."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        db_manager: Any,
        whatsapp_handler: Any,
        app_ref: Any,
    ) -> None:
        super().__init__(parent)
        self.db = db_manager
        self.wh = whatsapp_handler
        self.app_ref = app_ref

        self.worker_checkboxes: list[tuple[str, str, ctk.CTkCheckBox]] = []
        self.recent_tasks_container: ctk.CTkFrame | None = None

        self._build_ui()
        self.refresh()

    # ── Build UI ────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Header
        header = ctk.CTkLabel(
            self,
            text="إدارة المهام - Task Manager",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        header.pack(pady=(15, 10), anchor="w", padx=20)

        # ── Creation form ──
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=20, pady=(0, 15))

        # Task description
        ctk.CTkLabel(
            form, text="وصف المهمة - Task Description",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=10, pady=(10, 2))

        self.task_text = ctk.CTkTextbox(form, height=100, wrap="word")
        self.task_text.pack(fill="x", padx=10, pady=(0, 8))

        # Duration
        ctk.CTkLabel(
            form, text="المدة المقدرة (دقائق) - Estimated Duration (minutes)",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=10, pady=(5, 2))

        self.duration_entry = ctk.CTkEntry(form, width=150)
        self.duration_entry.pack(anchor="w", padx=10, pady=(0, 8))
        self.duration_entry.insert(0, "30")

        # Worker checkboxes section
        ctk.CTkLabel(
            form, text="تعيين الفنيين - Assign Workers",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(5, 2))

        self.checkbox_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.checkbox_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Dispatch button
        self.dispatch_btn = ctk.CTkButton(
            form,
            text="إرسال المهمة - Dispatch Task",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            height=40,
            command=self._dispatch_task,
        )
        self.dispatch_btn.pack(fill="x", padx=10, pady=(0, 12))

        # ── Recent tasks section ──
        recent_header = ctk.CTkLabel(
            self,
            text="آخر المهام - Recent Tasks",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        recent_header.pack(anchor="w", padx=20, pady=(5, 5))

        self.recent_scroll = ctk.CTkScrollableFrame(self, height=200)
        self.recent_scroll.pack(fill="x", padx=20, pady=(0, 15), expand=False)

    # ── Refresh ─────────────────────────────────────────────────

    def refresh(self) -> None:
        """Rebuild worker checkboxes and recent tasks list."""

        def _do_refresh() -> None:
            self._rebuild_checkboxes()
            self._rebuild_recent_tasks()

        try:
            self.winfo_toplevel().after(0, _do_refresh)
        except Exception:
            _do_refresh()

    def _rebuild_checkboxes(self) -> None:
        for w in self.checkbox_frame.winfo_children():
            w.destroy()

        self.worker_checkboxes = []
        workers = self.db.get_active_workers()
        if not workers:
            ctk.CTkLabel(
                self.checkbox_frame,
                text="لا يوجد فنيين نشطين - No active workers",
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color="#888888",
            ).pack(anchor="w")
            return

        row_frame = ctk.CTkFrame(self.checkbox_frame, fg_color="transparent")
        row_frame.pack(anchor="w")

        for i, w in enumerate(workers):
            cb = ctk.CTkCheckBox(
                row_frame,
                text=f"{w['name']} ({w['phone']})",
                font=ctk.CTkFont(size=12),
            )
            cb.grid(row=i // 3, column=i % 3, padx=(0, 20), pady=3, sticky="w")
            self.worker_checkboxes.append((w["phone"], w["name"], cb))

    def _rebuild_recent_tasks(self) -> None:
        for w in self.recent_scroll.winfo_children():
            w.destroy()

        tasks = self.db.get_tasks()[:10]
        if not tasks:
            ctk.CTkLabel(
                self.recent_scroll,
                text="لا توجد مهام - No tasks yet",
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color="#888888",
            ).pack(pady=20)
            return

        for task in tasks:
            card = ctk.CTkFrame(self.recent_scroll, border_width=1, corner_radius=6)
            card.pack(fill="x", padx=5, pady=3)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=6)

            # Description
            ctk.CTkLabel(
                inner,
                text=task["task_description"],
                font=ctk.CTkFont(size=12, weight="bold"),
                wraplength=500, justify="right",
            ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 2))

            # Info row
            ctk.CTkLabel(
                inner,
                text=f"👥 {task['assigned_workers']} | ⏱ {task['estimated_duration']} min | {task['created_at']}",
                font=ctk.CTkFont(size=10),
                text_color="#aaaaaa",
            ).grid(row=1, column=0, sticky="w")

            # Status badge
            status = task["status"]
            colors = {
                "PENDING": "#f9a825",
                "IN_PROGRESS": "#1e88e5",
                "COMPLETED": "#4caf50",
                "FAILED": "#f44336",
            }
            ctk.CTkLabel(
                inner,
                text=status,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=colors.get(status, "#ffffff"),
            ).grid(row=1, column=1, padx=(10, 0))

    # ── Dispatch logic ──────────────────────────────────────────

    def _dispatch_task(self) -> None:
        description = self.task_text.get("1.0", "end").strip()
        duration_str = self.duration_entry.get().strip()

        # Validation
        if not description:
            tkmb.showwarning("تنبيه - Warning", "الرجاء إدخال وصف المهمة\nPlease enter a task description.")
            return

        try:
            duration = int(duration_str)
            if duration <= 0:
                raise ValueError
        except ValueError:
            tkmb.showwarning("تنبيه - Warning", "الرجاء إدخال مدة صالحة (رقم موجب)\nPlease enter a valid duration (positive number).")
            return

        selected = [(phone, name) for phone, name, cb in self.worker_checkboxes if cb.get() == 1]
        if not selected:
            tkmb.showwarning("تنبيه - Warning", "الرجاء اختيار فني واحد على الأقل\nPlease select at least one worker.")
            return

        # Create task in DB
        phones_str = ",".join(phone for phone, _ in selected)
        task_id = self.db.add_task(description, phones_str, duration)
        if task_id is None:
            tkmb.showerror("خطأ - Error", "فشل إنشاء المهمة في قاعدة البيانات\nFailed to create task in database.")
            return

        # Send WhatsApp messages
        failures = []
        for phone, name in selected:
            success = self.wh.send_task_assignment(phone, name, description, duration)
            if not success:
                failures.append(name)

        # Show result
        if not failures:
            self._show_success_popup("✅ تم إنشاء المهمة وإرسالها بنجاح\nTask created and dispatched successfully!")
        else:
            names = ", ".join(failures)
            self._show_success_popup(
                f"⚠️ تم إنشاء المهمة ولكن فشل إرسال واتساب إلى:\n{names}\n"
                "Task created but WhatsApp sending failed for some workers."
            )

        # Clear form
        self.task_text.delete("1.0", "end")
        self.duration_entry.delete(0, "end")
        self.duration_entry.insert(0, "30")
        for _, _, cb in self.worker_checkboxes:
            cb.deselect()

        self.refresh()

    def _show_success_popup(self, message: str) -> None:
        popup = ctk.CTkToplevel(self)
        popup.title("النتيجة - Result")
        popup.geometry("450x200")
        popup.resizable(False, False)
        popup.grab_set()

        popup.update_idletasks()
        px = self.winfo_rootx() + (self.winfo_width() - 450) // 2
        py = self.winfo_rooty() + (self.winfo_height() - 200) // 2
        popup.geometry(f"+{px}+{py}")

        ctk.CTkLabel(
            popup,
            text=message,
            font=ctk.CTkFont(size=14),
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
