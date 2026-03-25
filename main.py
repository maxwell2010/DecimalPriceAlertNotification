import json
import os
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, simpledialog
from typing import Any, Dict, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    from windows_toasts import Toast, WindowsToaster
except ImportError:
    Toast = None
    WindowsToaster = None

try:
    from win11toast import toast as win11toast_send
except ImportError:
    win11toast_send = None

try:
    from notifypy import Notify
except ImportError:
    Notify = None

API_URL = "https://bit.team/trade/api/cmc/ticker"
TARGET_PAIRS = ("DEL_USDT", "DEL_RUB")


def _resolve_user_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        local_appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return local_appdata / "WindowsNotify"
    return Path(__file__).resolve().parent


USER_DATA_DIR = _resolve_user_data_dir()
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

STATE_PATH = USER_DATA_DIR / "state.json"
CONFIG_PATH = USER_DATA_DIR / "config.json"
ICON_RENDER_URL = "https://assets.coinmarketrate.com/assets/coins/decimal/icon_decimal.png"
ICON_PNG_PATH = USER_DATA_DIR / "assets" / "icon.png"

DEFAULT_CONFIG: Dict[str, Any] = {
    "poll_interval_sec": 60,
    "price_step_percent": 1.0,
    "style": "glass",
    "always_on_top": True,
    "window_x": 40,
    "window_y": 40,
}

STYLE_PRESETS: Dict[str, Dict[str, Any]] = {
    "minimal": {
        "root_bg": "#111318",
        "card_bg": "#191D24",
        "row_bg": "#141821",
        "button_bg": "#202736",
        "fg": "#E8EDF7",
        "sub_fg": "#9AA8C2",
        "ok": "#1E8F5A",
        "bad": "#AE2C45",
        "up": "#25C27E",
        "down": "#FF5A76",
        "chip_fg": "#FFFFFF",
        "alpha": 1.0,
    },
    "glass": {
        "root_bg": "#0B1220",
        "card_bg": "#111A2E",
        "row_bg": "#1A2743",
        "button_bg": "#1A2743",
        "fg": "#EEF4FF",
        "sub_fg": "#95A7CA",
        "ok": "#2F9F7F",
        "bad": "#BF3E5A",
        "up": "#5DE8AB",
        "down": "#FF7A9A",
        "chip_fg": "#FFFFFF",
        "alpha": 0.97,
    },
    "neon": {
        "root_bg": "#080A14",
        "card_bg": "#0E1326",
        "row_bg": "#121A34",
        "button_bg": "#1A2750",
        "fg": "#E7FAFF",
        "sub_fg": "#7FB0CF",
        "ok": "#23D18B",
        "bad": "#FF4F74",
        "up": "#22F2A4",
        "down": "#FF6A8B",
        "chip_fg": "#041218",
        "alpha": 0.98,
    },
    "sunset": {
        "root_bg": "#1A0F14",
        "card_bg": "#2A151F",
        "row_bg": "#3A1D2C",
        "button_bg": "#4D2638",
        "fg": "#FFEFE2",
        "sub_fg": "#F5B7A8",
        "ok": "#2EA86B",
        "bad": "#D6425D",
        "up": "#63F0A8",
        "down": "#FF7D9A",
        "chip_fg": "#FFFFFF",
        "alpha": 1.0,
    },
    "ocean": {
        "root_bg": "#08131A",
        "card_bg": "#0C1E2A",
        "row_bg": "#133042",
        "button_bg": "#18435B",
        "fg": "#EAFBFF",
        "sub_fg": "#88C1D6",
        "ok": "#1B9AAA",
        "bad": "#C4455D",
        "up": "#4DE4C7",
        "down": "#FF7A8C",
        "chip_fg": "#FFFFFF",
        "alpha": 1.0,
    },
    "forest": {
        "root_bg": "#0D170F",
        "card_bg": "#142419",
        "row_bg": "#1A3322",
        "button_bg": "#22462D",
        "fg": "#EFF9EE",
        "sub_fg": "#9DC7A4",
        "ok": "#2EAD67",
        "bad": "#C64756",
        "up": "#7FF5A8",
        "down": "#FF8B97",
        "chip_fg": "#FFFFFF",
        "alpha": 1.0,
    },
    "forest-tr": {
        "root_bg": "#0E1810",
        "card_bg": "#16271B",
        "row_bg": "#1D3525",
        "button_bg": "#25462F",
        "fg": "#EFF8EF",
        "sub_fg": "#A0C8A8",
        "ok": "#2DAB67",
        "bad": "#C74958",
        "up": "#7DF4A7",
        "down": "#FF8A96",
        "chip_fg": "#FFFFFF",
        "alpha": 0.75,
    },
    "graphite": {
        "root_bg": "#16171B",
        "card_bg": "#1F2128",
        "row_bg": "#2A2E39",
        "button_bg": "#353B4A",
        "fg": "#F0F1F5",
        "sub_fg": "#AAB0C1",
        "ok": "#38A374",
        "bad": "#D14B64",
        "up": "#6EF6B8",
        "down": "#FF8AA1",
        "chip_fg": "#FFFFFF",
        "alpha": 0.98,
    },
    "latte": {
        "root_bg": "#F2E6D9",
        "card_bg": "#E8D7C4",
        "row_bg": "#E0CBB5",
        "button_bg": "#D7BEA4",
        "fg": "#2E221A",
        "sub_fg": "#735C49",
        "ok": "#2F9153",
        "bad": "#B23A48",
        "up": "#1E9E60",
        "down": "#C64155",
        "chip_fg": "#FFFFFF",
        "alpha": 1.0,
    },
    "ice": {
        "root_bg": "#EAF6FF",
        "card_bg": "#D9EEFF",
        "row_bg": "#C8E6FF",
        "button_bg": "#B5DCFF",
        "fg": "#102433",
        "sub_fg": "#3D6580",
        "ok": "#2B9BCB",
        "bad": "#D44D68",
        "up": "#14AFA1",
        "down": "#DE5F78",
        "chip_fg": "#FFFFFF",
        "alpha": 0.99,
    },
    "ice-tr": {
        "root_bg": "#DCEFFF",
        "card_bg": "#CAE5FF",
        "row_bg": "#BADBFF",
        "button_bg": "#A8D0FA",
        "fg": "#11293A",
        "sub_fg": "#3E6885",
        "ok": "#2795C9",
        "bad": "#D14C67",
        "up": "#11AFA1",
        "down": "#DF5D79",
        "chip_fg": "#FFFFFF",
        "alpha": 0.74,
    },
    "cyber": {
        "root_bg": "#111016",
        "card_bg": "#1B1626",
        "row_bg": "#2B1E3A",
        "button_bg": "#3C2752",
        "fg": "#F9F0FF",
        "sub_fg": "#C5A5E3",
        "ok": "#3DDC97",
        "bad": "#FF4D7A",
        "up": "#62FFD0",
        "down": "#FF8AAC",
        "chip_fg": "#120C1D",
        "alpha": 0.97,
    },
    "transparent": {
        "root_bg": "#0E1116",
        "card_bg": "#1A1F2A",
        "row_bg": "#232A38",
        "button_bg": "#2D374A",
        "fg": "#E7F0FF",
        "sub_fg": "#A6B8D6",
        "ok": "#28A168",
        "bad": "#C24562",
        "up": "#54E8A5",
        "down": "#FF86A2",
        "chip_fg": "#FFFFFF",
        "alpha": 0.74,
    },
}

STYLE_LABELS: Dict[str, str] = {
    "minimal": "minimal",
    "glass": "glass",
    "neon": "neon",
    "sunset": "sunset",
    "ocean": "ocean",
    "forest": "forest",
    "forest-tr": "for-tr",
    "graphite": "graph",
    "latte": "latte",
    "ice": "ice",
    "ice-tr": "ice-tr",
    "cyber": "cyber",
    "transparent": "transp",
}


def ensure_icon_asset() -> Optional[Path]:
    try:
        ICON_PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if ICON_PNG_PATH.exists() and ICON_PNG_PATH.stat().st_size > 0:
            return ICON_PNG_PATH
        req_png = Request(
            ICON_RENDER_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DELMonitor/1.0"},
        )
        with urlopen(req_png, timeout=8) as resp_png:
            png_content = resp_png.read()
        if png_content:
            with ICON_PNG_PATH.open("wb") as f:
                f.write(png_content)
            return ICON_PNG_PATH
    except Exception:
        pass
    if ICON_PNG_PATH.exists() and ICON_PNG_PATH.stat().st_size > 0:
        return ICON_PNG_PATH
    return None


class JsonStore:
    @staticmethod
    def load(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
        if not path.exists():
            return dict(default)
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    result = dict(default)
                    result.update(data)
                    return result
        except (OSError, json.JSONDecodeError):
            pass
        return dict(default)

    @staticmethod
    def save(path: Path, data: Dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class ConfigManager:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._cfg = JsonStore.load(path, DEFAULT_CONFIG)
        self._cfg["style"] = self._normalize_style(self._cfg.get("style"))
        self._cfg["poll_interval_sec"] = max(15, int(self._cfg.get("poll_interval_sec", 60)))
        self._cfg["price_step_percent"] = max(0.1, float(self._cfg.get("price_step_percent", 1.0)))
        self._cfg["always_on_top"] = bool(self._cfg.get("always_on_top", True))
        JsonStore.save(self.path, self._cfg)

    @staticmethod
    def _normalize_style(value: Any) -> str:
        return value if value in STYLE_PRESETS else "glass"

    def get(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._cfg)

    def update(self, patch: Dict[str, Any]) -> None:
        with self._lock:
            self._cfg.update(patch)
            self._cfg["style"] = self._normalize_style(self._cfg.get("style"))
            self._cfg["poll_interval_sec"] = max(15, int(self._cfg.get("poll_interval_sec", 60)))
            self._cfg["price_step_percent"] = max(0.1, float(self._cfg.get("price_step_percent", 1.0)))
            self._cfg["always_on_top"] = bool(self._cfg.get("always_on_top", True))
            JsonStore.save(self.path, self._cfg)


class ToastNotifier:
    def __init__(self, icon_path: Optional[Path] = None) -> None:
        self.backend = "stdout"
        self.icon_path = icon_path if icon_path and icon_path.exists() else None
        self._toaster = None
        if win11toast_send is not None:
            self.backend = "win11toast"
            return
        if WindowsToaster is not None and Toast is not None:
            try:
                self._toaster = WindowsToaster("DEL Monitor")
                self.backend = "windows-toasts"
                return
            except Exception:
                self._toaster = None
        if Notify is not None:
            self.backend = "notifypy"

    def send(self, title: str, message: str) -> None:
        if self.backend == "windows-toasts" and self._toaster is not None and Toast is not None:
            try:
                toast = Toast()
                toast.text_fields = [title, message]
                self._toaster.show_toast(toast)
                return
            except Exception:
                pass
        if self.backend == "win11toast" and win11toast_send is not None:
            try:
                if self.icon_path is not None:
                    try:
                        win11toast_send(title, message, icon=str(self.icon_path))
                        return
                    except Exception:
                        pass
                win11toast_send(title, message)
                return
            except Exception:
                pass
        if Notify is not None:
            try:
                notification = Notify()
                notification.application_name = "DEL Monitor"
                notification.title = title
                notification.message = message
                if self.icon_path is not None:
                    notification.icon = str(self.icon_path)
                notification.send()
                return
            except Exception:
                pass
        print(f"[notify] {title}: {message}")


class PriceMonitor:
    def __init__(
        self,
        config: ConfigManager,
        state_path: Path,
        notifier: ToastNotifier,
        on_update,
    ) -> None:
        self.config = config
        self.state_path = state_path
        self.notifier = notifier
        self.on_update = on_update
        self._state = JsonStore.load(
            state_path,
            {
                "exchange_online": None,
                "last_prices": {pair: 0.0 for pair in TARGET_PAIRS},
                "pair_status": {pair: False for pair in TARGET_PAIRS},
                "alert_anchors": {pair: 0.0 for pair in TARGET_PAIRS},
                "last_update": None,
                "error": None,
            },
        )
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _fetch_prices(self) -> Dict[str, Any]:
        try:
            req = Request(
                API_URL,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DELMonitor/1.0"
                },
            )
            with urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
            payload = json.loads(raw)
            prices: Dict[str, float] = {}
            pair_status: Dict[str, bool] = {}
            for pair in TARGET_PAIRS:
                value = self._safe_float((payload.get(pair) or {}).get("last_price", 0))
                is_ok = value > 0
                prices[pair] = value
                pair_status[pair] = is_ok
            online = all(pair_status.values())
            return {
                "ok": True,
                "prices": prices,
                "pair_status": pair_status,
                "exchange_online": online,
                "error": None,
            }
        except (URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
            return {
                "ok": False,
                "prices": {pair: 0.0 for pair in TARGET_PAIRS},
                "pair_status": {pair: False for pair in TARGET_PAIRS},
                "exchange_online": False,
                "error": str(exc),
            }

    @staticmethod
    def _calc_change_percent(current: float, base: float) -> float:
        if current <= 0 or base <= 0:
            return 0.0
        return (current - base) / base * 100

    def _notify_status_change(self, previous: Optional[bool], current: bool) -> None:
        if previous is None or previous == current:
            return
        if current:
            self.notifier.send("DEL Monitor", "Биржа снова доступна: котировки обновляются.")
            return
        self.notifier.send("DEL Monitor", "Биржа недоступна: обновления временно остановлены.")

    def _notify_price_steps(
        self,
        prices: Dict[str, float],
        threshold_percent: float,
        alert_anchors: Dict[str, float],
    ) -> Dict[str, float]:
        next_anchors = dict(alert_anchors)
        for pair in TARGET_PAIRS:
            current = prices.get(pair, 0.0)
            anchor = self._safe_float(next_anchors.get(pair, 0.0))
            if current <= 0:
                continue
            if anchor <= 0:
                next_anchors[pair] = current
                continue
            diff_percent = self._calc_change_percent(current, anchor)
            if abs(diff_percent) < threshold_percent:
                continue
            direction = "рост" if diff_percent > 0 else "падение"
            sign = "+" if diff_percent > 0 else ""
            self.notifier.send(
                "DEL Monitor",
                f"{pair}: {direction} {sign}{diff_percent:.1f}% | цена {current:.6f}",
            )
            next_anchors[pair] = current
        return next_anchors

    def _build_snapshot(self, fetched: Dict[str, Any], previous_prices: Dict[str, float]) -> Dict[str, Any]:
        changes = {}
        for pair in TARGET_PAIRS:
            changes[pair] = self._calc_change_percent(
                fetched["prices"].get(pair, 0.0),
                self._safe_float(previous_prices.get(pair, 0.0)),
            )
        return {
            "prices": fetched["prices"],
            "pair_status": fetched["pair_status"],
            "exchange_online": fetched["exchange_online"],
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "changes": changes,
            "error": fetched["error"],
        }

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            cfg = self.config.get()
            fetched = self._fetch_prices()
            previous_online = self._state.get("exchange_online")
            previous_prices = dict(self._state.get("last_prices", {}))

            snapshot = self._build_snapshot(fetched, previous_prices)
            self._notify_status_change(previous_online, snapshot["exchange_online"])

            anchors = dict(self._state.get("alert_anchors", {}))
            if fetched["exchange_online"]:
                anchors = self._notify_price_steps(
                    fetched["prices"],
                    float(cfg["price_step_percent"]),
                    anchors,
                )

            self._state = {
                "exchange_online": snapshot["exchange_online"],
                "last_prices": fetched["prices"],
                "pair_status": fetched["pair_status"],
                "alert_anchors": anchors,
                "last_update": snapshot["last_update"],
                "error": snapshot["error"],
            }
            JsonStore.save(self.state_path, self._state)
            self.on_update(snapshot)

            interval = max(15, int(cfg["poll_interval_sec"]))
            self._stop_event.wait(timeout=interval)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)


class MonitorWidget(tk.Tk):
    def __init__(self, config: ConfigManager) -> None:
        super().__init__()
        self.config_manager = config
        self.current_cfg = self.config_manager.get()
        self.theme = STYLE_PRESETS[self.current_cfg["style"]]
        self.latest_snapshot: Dict[str, Any] = {
            "prices": {pair: 0.0 for pair in TARGET_PAIRS},
            "pair_status": {pair: False for pair in TARGET_PAIRS},
            "changes": {pair: 0.0 for pair in TARGET_PAIRS},
            "exchange_online": False,
            "last_update": "n/a",
            "error": None,
        }
        self.pending_snapshot: Optional[Dict[str, Any]] = None
        self.snapshot_lock = threading.Lock()
        self.drag_start = (0, 0)
        self.icon_path = ensure_icon_asset()
        self._icon_image = None

        self._build_window()
        self._build_ui()
        self._build_menu()
        self.apply_style()
        self.render()

        self.notifier = ToastNotifier(self.icon_path)
        self.monitor = PriceMonitor(
            config=self.config_manager,
            state_path=STATE_PATH,
            notifier=self.notifier,
            on_update=self.enqueue_snapshot,
        )
        self.monitor.start()
        self.after(300, self.consume_snapshot)
        self.protocol("WM_DELETE_WINDOW", self.shutdown)

    def _build_window(self) -> None:
        self.title("DEL Monitor")
        self.geometry(f"350x230+{int(self.current_cfg['window_x'])}+{int(self.current_cfg['window_y'])}")
        self.resizable(False, False)
        self.attributes("-topmost", bool(self.current_cfg["always_on_top"]))
        if self.icon_path is not None and self.icon_path.exists() and self.icon_path.suffix.lower() == ".png":
            try:
                self._icon_image = tk.PhotoImage(file=str(self.icon_path))
                self.iconphoto(True, self._icon_image)
            except Exception:
                self._icon_image = None

    def _build_ui(self) -> None:
        self.container = tk.Frame(self, bd=0, highlightthickness=0, padx=12, pady=12)
        self.container.pack(fill="both", expand=True)

        self.header = tk.Frame(self.container, bd=0, highlightthickness=0)
        self.header.pack(fill="x")

        self.title_label = tk.Label(self.header, text="DEL Monitor", font=("Segoe UI Semibold", 15), anchor="w")
        self.title_label.pack(side="left")

        self.style_btn = tk.Button(
            self.header,
            text="Style",
            font=("Segoe UI", 9),
            relief="flat",
            bd=0,
            command=self.cycle_style,
            cursor="hand2",
            padx=10,
            pady=3,
            width=14,
        )
        self.style_btn.pack(side="right")

        self.threshold_btn = tk.Button(
            self.header,
            text="Alert >= 1.0%",
            font=("Segoe UI", 9),
            relief="flat",
            bd=0,
            command=self.set_threshold,
            cursor="hand2",
            padx=10,
            pady=3,
        )
        self.threshold_btn.pack(side="right", padx=(0, 6))

        self.status_chip = tk.Label(
            self.container,
            text="Checking...",
            font=("Segoe UI", 9),
            padx=10,
            pady=3,
            anchor="w",
        )
        self.status_chip.pack(fill="x", pady=(10, 8))

        self.rows: Dict[str, Dict[str, tk.Widget]] = {}
        for pair in TARGET_PAIRS:
            row = tk.Frame(self.container, bd=0, highlightthickness=0, padx=10, pady=8)
            row.pack(fill="x", pady=4)
            pair_label = tk.Label(row, text=pair, font=("Segoe UI Semibold", 10), anchor="w")
            pair_label.pack(side="left")
            value_label = tk.Label(row, text="0.000000", font=("Consolas", 11), anchor="e")
            value_label.pack(side="right")
            change_label = tk.Label(row, text="0.00%", font=("Segoe UI", 9), width=8)
            change_label.pack(side="right", padx=(0, 8))
            self.rows[pair] = {
                "row": row,
                "pair": pair_label,
                "value": value_label,
                "change": change_label,
            }

        self.footer = tk.Label(self.container, text="Updated: n/a", font=("Segoe UI", 8), anchor="w")
        self.footer.pack(fill="x", pady=(12, 0))

        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.save_position)
        self.container.bind("<ButtonPress-1>", self.start_drag)
        self.container.bind("<B1-Motion>", self.on_drag)
        self.container.bind("<ButtonRelease-1>", self.save_position)
        self.header.bind("<ButtonPress-1>", self.start_drag)
        self.header.bind("<B1-Motion>", self.on_drag)
        self.header.bind("<ButtonRelease-1>", self.save_position)

    def _build_menu(self) -> None:
        self.popup = tk.Menu(self, tearoff=0)
        self.popup.add_command(label="Set threshold %", command=self.set_threshold)
        self.popup.add_command(label="Set interval sec", command=self.set_interval)
        self.popup.add_command(label="Toggle topmost", command=self.toggle_topmost)
        self.popup.add_separator()
        self.style_menu = tk.Menu(self.popup, tearoff=0)
        for style_name in STYLE_PRESETS:
            self.style_menu.add_command(
                label=STYLE_LABELS.get(style_name, style_name),
                command=lambda s=style_name: self.set_style(s),
            )
        self.popup.add_cascade(label="Styles", menu=self.style_menu)
        self.popup.add_separator()
        self.popup.add_command(label="Exit", command=self.shutdown)
        self.bind("<Button-3>", self.show_menu)

    def enqueue_snapshot(self, snapshot: Dict[str, Any]) -> None:
        with self.snapshot_lock:
            self.pending_snapshot = snapshot

    def consume_snapshot(self) -> None:
        with self.snapshot_lock:
            snapshot = self.pending_snapshot
            self.pending_snapshot = None
        if snapshot:
            self.latest_snapshot = snapshot
            self.render()
        self.after(300, self.consume_snapshot)

    def apply_style(self) -> None:
        self.current_cfg = self.config_manager.get()
        self.theme = STYLE_PRESETS[self.current_cfg["style"]]
        window_alpha = max(0.45, min(1.0, float(self.theme.get("alpha", 1.0))))
        row_bg = self.theme.get("row_bg", self.theme["root_bg"])
        button_bg = self.theme.get("button_bg", self.theme["root_bg"])

        self.attributes("-alpha", window_alpha)
        self.configure(bg=self.theme["root_bg"])
        self.container.configure(bg=self.theme["card_bg"])
        self.header.configure(bg=self.theme["card_bg"])
        self.title_label.configure(bg=self.theme["card_bg"], fg=self.theme["fg"])
        self.status_chip.configure(bg=self.theme["root_bg"], fg=self.theme["chip_fg"])
        self.style_btn.configure(
            bg=button_bg,
            fg=self.theme["fg"],
            activebackground=button_bg,
            activeforeground=self.theme["fg"],
            text=f"Style: {STYLE_LABELS.get(self.current_cfg['style'], self.current_cfg['style'])}",
        )
        self.threshold_btn.configure(
            bg=button_bg,
            fg=self.theme["fg"],
            activebackground=button_bg,
            activeforeground=self.theme["fg"],
        )
        self.footer.configure(bg=self.theme["card_bg"], fg=self.theme["sub_fg"])
        for row_items in self.rows.values():
            row_items["row"].configure(bg=row_bg)
            row_items["pair"].configure(bg=row_bg, fg=self.theme["sub_fg"])
            row_items["value"].configure(bg=row_bg, fg=self.theme["fg"])
            row_items["change"].configure(
                bg=row_bg,
                fg=self.theme["sub_fg"],
                relief="flat",
                bd=0,
            )
        self.render()

    def render(self) -> None:
        snap = self.latest_snapshot
        online = bool(snap["exchange_online"])
        status_bg = self.theme["ok"] if online else self.theme["bad"]
        status_text = "Exchange: ONLINE" if online else "Exchange: OFFLINE"
        self.status_chip.configure(
            text=status_text,
            bg=status_bg,
            fg=self.theme["chip_fg"],
        )

        for pair, row_items in self.rows.items():
            price = float(snap["prices"].get(pair, 0.0))
            ok = bool(snap["pair_status"].get(pair, False))
            change = float(snap["changes"].get(pair, 0.0))
            if ok:
                price_text = f"{price:.6f}"
            else:
                price_text = "--"
            sign = "+" if change > 0 else ""
            change_text = f"{sign}{change:.2f}%"
            change_fg = self.theme["up"] if change > 0 else self.theme["down"] if change < 0 else self.theme["sub_fg"]
            row_items["value"].configure(text=price_text)
            row_items["change"].configure(text=change_text, fg=change_fg)

        updated = snap.get("last_update") or "n/a"
        footer_text = f"Updated: {updated}"
        if snap.get("error"):
            footer_text = f"{footer_text} | err"
        self.footer.configure(text=footer_text)
        step_percent = float(self.config_manager.get().get("price_step_percent", 1.0))
        self.threshold_btn.configure(text=f"Alert >= {step_percent:.1f}%")

    def show_menu(self, event) -> None:
        self.popup.tk_popup(event.x_root, event.y_root)

    def set_threshold(self) -> None:
        value = simpledialog.askfloat(
            "Threshold",
            "Step percent for alerts (e.g. 1.0):",
            minvalue=0.1,
            maxvalue=100.0,
        )
        if value is None:
            return
        next_value = float(value)
        self.config_manager.update({"price_step_percent": next_value})
        self.threshold_btn.configure(text=f"Alert >= {next_value:.1f}%")
        messagebox.showinfo("Saved", f"New threshold: {value:.1f}%")

    def set_interval(self) -> None:
        value = simpledialog.askinteger(
            "Interval",
            "Polling interval in seconds (minimum 15):",
            minvalue=15,
            maxvalue=3600,
        )
        if value is None:
            return
        self.config_manager.update({"poll_interval_sec": int(value)})
        messagebox.showinfo("Saved", f"New interval: {value} sec")

    def toggle_topmost(self) -> None:
        next_value = not bool(self.config_manager.get()["always_on_top"])
        self.config_manager.update({"always_on_top": next_value})
        self.attributes("-topmost", next_value)

    def set_style(self, style: str) -> None:
        self.config_manager.update({"style": style})
        self.apply_style()

    def cycle_style(self) -> None:
        styles = list(STYLE_PRESETS.keys())
        current = self.config_manager.get()["style"]
        idx = styles.index(current)
        self.set_style(styles[(idx + 1) % len(styles)])

    def start_drag(self, event) -> None:
        self.drag_start = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())

    def on_drag(self, event) -> None:
        next_x = event.x_root - self.drag_start[0]
        next_y = event.y_root - self.drag_start[1]
        self.geometry(f"+{next_x}+{next_y}")

    def save_position(self, _event=None) -> None:
        self.config_manager.update({"window_x": int(self.winfo_x()), "window_y": int(self.winfo_y())})

    def shutdown(self) -> None:
        self.monitor.stop()
        self.destroy()


def main() -> None:
    ensure_icon_asset()
    config = ConfigManager(CONFIG_PATH)
    app = MonitorWidget(config)
    app.mainloop()


if __name__ == "__main__":
    main()
