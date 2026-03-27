from datetime import datetime
from tkinter import Button, Frame, Label, messagebox

from main import CONFIG_PATH, ConfigManager, MonitorWidget, STYLE_PRESETS


class TestLab:
    def __init__(self) -> None:
        self.app = MonitorWidget(ConfigManager(CONFIG_PATH))
        self.app.title("DEL Monitor - Test Lab")
        self.app.geometry("560x700")
        self.app.minsize(520, 620)
        self.app.resizable(True, True)
        self.app.lift()
        self.app.attributes("-topmost", True)
        self.app.after(1200, lambda: self.app.attributes("-topmost", False))
        self.app.monitor.stop()
        self.app.monitor_watchdog_enabled = False
        self.app.style_btn.configure(command=self.cycle_style)
        self.app.footer.configure(text="Test mode: polling disabled")
        self.control_buttons = []
        self.next_button = None
        self.panel = None
        self.step_info = None
        self.sequence_index = 0
        self.sequence = [
            ("ONLINE notify", self.notify_online),
            ("ONLINE widget", self.widget_online),
            ("UP notify", self.notify_up),
            ("UP widget", self.widget_up),
            ("DOWN notify", self.notify_down),
            ("DOWN widget", self.widget_down),
            ("OFFLINE notify", self.notify_offline),
            ("OFFLINE widget", self.widget_offline),
        ]
        self._build_controls()
        self._sync_controls_theme()
        self.app.notifier.send(
            "DEL Monitor Test",
            f"Тестовый режим запущен. Backend: {self.app.notifier.backend}",
        )
        self._set_snapshot(
            online=False,
            del_usdt=0.0,
            del_rub=0.0,
            chg_usdt=0.0,
            chg_rub=0.0,
            error="manual test",
        )

    def _build_controls(self) -> None:
        self.panel = Frame(self.app.container, bg=self.app.theme["card_bg"])
        self.panel.pack(fill="x", pady=(8, 0))
        self.step_info = Label(
            self.panel,
            text="Step: 0 | Нажми NEXT для пошагового теста уведомлений",
            anchor="w",
            font=("Segoe UI", 8),
            padx=4,
            pady=2,
        )
        self.step_info.grid(row=0, column=0, columnspan=4, sticky="ew", padx=3, pady=(0, 3))

        self.next_button = Button(
            self.panel,
            text="NEXT STEP",
            command=self.next_step,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=8,
            pady=6,
        )
        self.next_button.grid(row=1, column=0, columnspan=4, padx=3, pady=(0, 6), sticky="ew")

        buttons = [
            ("Notify ONLINE", self.notify_online),
            ("Notify OFFLINE", self.notify_offline),
            ("Notify UP", self.notify_up),
            ("Notify DOWN", self.notify_down),
            ("Open Notif Settings", self.app.open_notifications_settings),
            ("Widget ONLINE", self.widget_online),
            ("Widget OFFLINE", self.widget_offline),
            ("Widget UP", self.widget_up),
            ("Widget DOWN", self.widget_down),
        ]
        for style_name in STYLE_PRESETS:
            buttons.append((f"Style {style_name}", lambda s=style_name: self.set_style(s)))
        buttons.append(("Cycle style", self.cycle_style))

        for idx, (text, command) in enumerate(buttons):
            btn = Button(
                self.panel,
                text=text,
                command=command,
                relief="flat",
                bd=0,
                cursor="hand2",
                font=("Segoe UI", 8),
                padx=8,
                pady=3,
            )
            row = (idx // 4) + 2
            col = idx % 4
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            self.control_buttons.append(btn)

        for col in range(4):
            self.panel.grid_columnconfigure(col, weight=1)

    def _sync_controls_theme(self) -> None:
        row_bg = self.app.theme.get("row_bg", self.app.theme["root_bg"])
        button_bg = self.app.theme.get("button_bg", self.app.theme["root_bg"])
        if self.panel is not None:
            self.panel.configure(bg=self.app.theme["card_bg"])
        if self.step_info is not None:
            self.step_info.configure(bg=self.app.theme["card_bg"], fg=self.app.theme["sub_fg"])
        if self.next_button is not None:
            next_bg = self.app.theme.get("accent", button_bg)
            next_fg = self.app.theme.get("accent_fg", self.app.theme["fg"])
            next_active_bg = self.app.theme.get("status_online", row_bg)
            self.next_button.configure(
                bg=next_bg,
                fg=next_fg,
                activebackground=next_active_bg,
                activeforeground=next_fg,
            )
        for btn in self.control_buttons:
            btn.configure(
                bg=button_bg,
                fg=self.app.theme["fg"],
                activebackground=row_bg,
                activeforeground=self.app.theme["fg"],
            )

    def _set_snapshot(
        self,
        *,
        online: bool,
        del_usdt: float,
        del_rub: float,
        chg_usdt: float,
        chg_rub: float,
        error: str | None = None,
    ) -> None:
        self.app.latest_snapshot = {
            "prices": {
                "DEL_USDT": del_usdt,
                "DEL_RUB": del_rub,
            },
            "pair_status": {
                "DEL_USDT": del_usdt > 0,
                "DEL_RUB": del_rub > 0,
            },
            "changes": {
                "DEL_USDT": chg_usdt,
                "DEL_RUB": chg_rub,
            },
            "exchange_online": online,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": error,
        }
        self.app.render()

    def notify_online(self) -> None:
        self.app.notifier.send("DEL Monitor", "Тест: биржа снова доступна.")

    def notify_offline(self) -> None:
        self.app.notifier.send("DEL Monitor", "Тест: биржа недоступна.")

    def notify_up(self) -> None:
        self.app.notifier.send("DEL Monitor", "Тест: DEL_USDT рост +2.5%")

    def notify_down(self) -> None:
        self.app.notifier.send("DEL Monitor", "Тест: DEL_RUB падение -3.1%")

    def next_step(self) -> None:
        title, action = self.sequence[self.sequence_index]
        action()
        self.sequence_index = (self.sequence_index + 1) % len(self.sequence)
        next_title = self.sequence[self.sequence_index][0]
        if self.step_info is not None:
            self.step_info.configure(
                text=f"Step: {self.sequence_index}/{len(self.sequence)} | Выполнено: {title} | Далее: {next_title}"
            )
        # User-visible confirmation for each test step, even if OS suppresses tray toasts.
        transport = self.app.notifier.last_transport
        last_error = self.app.notifier.last_error or "none"
        messagebox.showinfo(
            "Test Step",
            (
                f"Выполнен шаг: {title}\n"
                f"Backend: {self.app.notifier.backend}\n"
                f"Transport: {transport}\n"
                f"Error: {last_error}\n"
                "Проверь уведомление в трее/центре уведомлений."
            ),
        )

    def widget_online(self) -> None:
        self._set_snapshot(
            online=True,
            del_usdt=0.123456,
            del_rub=10.55,
            chg_usdt=0.0,
            chg_rub=0.0,
            error=None,
        )

    def widget_offline(self) -> None:
        self._set_snapshot(
            online=False,
            del_usdt=0.0,
            del_rub=0.0,
            chg_usdt=0.0,
            chg_rub=0.0,
            error="HTTP 403: Forbidden",
        )

    def widget_up(self) -> None:
        self._set_snapshot(
            online=True,
            del_usdt=0.131245,
            del_rub=11.07,
            chg_usdt=2.60,
            chg_rub=1.42,
            error=None,
        )

    def widget_down(self) -> None:
        self._set_snapshot(
            online=True,
            del_usdt=0.117890,
            del_rub=9.78,
            chg_usdt=-3.80,
            chg_rub=-2.25,
            error=None,
        )

    def set_style(self, style: str) -> None:
        if style not in STYLE_PRESETS:
            return
        self.app.set_style(style)
        self._sync_controls_theme()
        self.app.notifier.send("DEL Monitor", f"Тест: стиль переключен на {style}")

    def cycle_style(self) -> None:
        self.app.cycle_style()
        self._sync_controls_theme()

    def run(self) -> None:
        self.app.mainloop()


def main() -> None:
    TestLab().run()


if __name__ == "__main__":
    main()
