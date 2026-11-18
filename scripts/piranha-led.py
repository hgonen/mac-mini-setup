#!/usr/bin/env python3
"""
Piranha 2345 arka isik koruyucu.

Neden gerekli:
  Klavyenin arka isigi, HID LED raporundaki "Scroll Lock" bitine bagli
  (bit2 / 0x04). Windows Scroll Lock tusuna basinca bu biti gonderiyor,
  macOS Scroll Lock'u hic islemedigi icin isik yanmiyor.
  Ayrica macOS Caps Lock degisiminde LED raporunu bastan yazip bitimizi
  siliyor -> bu yuzden periyodik olarak yeniden gonderiyoruz.
"""

import ctypes
import subprocess
import time

HIDA = "/opt/homebrew/bin/hidapitester"
VIDPID = "1A2C:2C27"
INTERVAL = 3          # saniye
CAPS_KEYCODE = 57     # kVK_CapsLock
LED_SCROLL = 0x04     # arka isik
LED_CAPS = 0x02       # caps gostergesi

CG = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
CG.CGEventSourceKeyState.restype = ctypes.c_bool
CG.CGEventSourceKeyState.argtypes = [ctypes.c_int, ctypes.c_ushort]


def led_byte() -> int:
    """Scroll Lock biti + mevcut Caps Lock durumu."""
    b = LED_SCROLL
    try:
        if CG.CGEventSourceKeyState(1, CAPS_KEYCODE):  # 1 = HID system state
            b |= LED_CAPS
    except Exception:
        pass
    return b


def send(value: int) -> bool:
    try:
        r = subprocess.run(
            [HIDA, "--vidpid", VIDPID, "--usagePage", "1", "--usage", "6",
             "-l", "1", "--nonexclusive", "--open", "--send-output", str(value), "-q"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


def main() -> None:
    while True:
        send(led_byte())
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
