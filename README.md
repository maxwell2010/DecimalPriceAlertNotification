# WindowsNotify

Лёгкий монитор для Windows: виджет на рабочем столе + системные уведомления по `DEL_USDT` и `DEL_RUB`.

## Что делает

- Раз в `poll_interval_sec` секунд (по умолчанию 60) запрашивает `https://bit.team/trade/api/cmc/ticker`.
- Сохраняет состояние в `state.json`:
  - `exchange_online`
  - `last_prices`
  - `pair_status`
  - `alert_anchors`
  - `last_update`
  - `error`
- Сохраняет настройки пользователя в `config.json`:
  - `price_step_percent`
  - `style` (любая из 13 тем)
  - `poll_interval_sec`
  - `always_on_top`
  - `window_x`, `window_y`
- Уведомляет только когда:
  - изменился статус биржи (`ONLINE`/`OFFLINE`);
  - цена прошла заданный шаг в `%` (рост/падение).
- Использует более качественный backend уведомлений с fallback:
  - `Windows-Toasts` (основной)
  - `win11toast`
  - `notifypy`
- Показывает компактный виджет с цветовой индикацией:
  - зелёный для роста;
  - красный для падения;
  - кнопка `Alert >= ...%` в окне для изменения порога уведомлений;
  - 13 тем оформления: `minimal`, `glass`, `neon`, `sunset`, `ocean`, `forest`, `forest-tr`, `graphite`, `latte`, `ice`, `ice-tr`, `cyber`, `transparent`.
  - стиль `transparent` использует полупрозрачный фон окна.
  - переключение стиля через кнопку `Style` или меню правой кнопкой.
- Иконка уведомлений/окна загружается из:
  - `https://assets.coinmarketrate.com/assets/coins/decimal/icon_decimal.png`
  - сохраняется локально в `assets/icon.png`.

## Где хранятся настройки

- При запуске через `python main.py`:
  - `config.json` и `state.json` сохраняются в папке проекта.
- При запуске через `WindowsNotify.exe`:
  - данные сохраняются в `%LOCALAPPDATA%\WindowsNotify\`
  - это сохраняет выбранную тему, порог алертов, позицию окна и интервал между перезапусками.

## Запуск

```powershell
cd C:\Users\Maximus\PycharmProjects\WindowsNotify
pip install -r requirements.txt
python main.py
```

## Тестовый режим (уведомления + виджет)

```powershell
cd C:\Users\Maximus\PycharmProjects\WindowsNotify
python test_lab.py
```

`test_lab.py` запускает виджет в режиме без реального polling и добавляет кнопки для проверки:
- уведомлений `ONLINE/OFFLINE`;
- уведомлений роста/падения;
- визуальных состояний виджета;
- всех 13 стилей.

## Сборка в EXE

```powershell
pip install pyinstaller
python -c "from main import ensure_icon_asset; ensure_icon_asset()"
if (Test-Path dist) { Remove-Item dist -Recurse -Force }
if (Test-Path build) { Remove-Item build -Recurse -Force }
python -m PyInstaller --clean --noconfirm --onefile --windowed --name WindowsNotify --icon assets/icon.ico main.py
```

Готовый файл: `dist\WindowsNotify.exe`

## Авто-сборка в GitHub Actions

- При пуше в `main` workflow собирает `WindowsNotify.exe` и публикует его как artifact.
- При пуше тега вида `v*` (например, `v1.0.0`) workflow дополнительно прикрепляет `WindowsNotify.exe` к GitHub Release.

## Автозапуск

1. Нажать `Win + R` и выполнить `shell:startup`.
2. Положить ярлык на `dist\WindowsNotify.exe` в эту папку.

