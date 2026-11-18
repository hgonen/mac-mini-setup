# Piranha 2345 — macOS Arka Işık Servisi

> Bu dosya, klavye arka ışığı için kurduğumuz çözümün tam kaydıdır.
> Kaldırmak veya yeniden kurmak için gereken her şey burada.

Son güncelleme: 18 Kasım 2026
Makine: Mac mini (Apple Silicon, Darwin 27.x)

---

## 1. Sorun neydi?

Piranha 2345 klavyesinin arka ışığı macOS'ta yanmıyordu.

**Kök neden:** Klavyenin aydınlatması, HID LED raporundaki **Scroll Lock** bitine bağlı.
Windows'ta Scroll Lock tuşuna basınca işletim sistemi bu biti klavyeye gönderiyor, ışık yanıyor.
**macOS Scroll Lock tuşunu hiç işlemiyor** → LED raporu hiç gönderilmiyor → ışık yanmıyor.

Klavye bozuk değil, sorun macOS'un eksikliği.

### Teknik kanıt (HID rapor tanımlayıcısı)

```
05 01  Usage Page (Generic Desktop)
09 06  Usage (Keyboard)
A1 01  Collection (Application)
  05 08  Usage Page (LEDs)
  19 01  Usage Minimum (Num Lock)
  29 03  Usage Maximum (Scroll Lock)     ← 3 LED: Num, Caps, Scroll
  15 00  Logical Minimum (0)
  25 01  Logical Maximum (1)
  75 01  Report Size (1)
  95 03  Report Count (3)
  91 02  Output (Data,Var,Abs)           ← 1 baytlık LED raporu
  95 05  Report Count (5)
  91 01  Output (Const,Array,Abs)        ← 5 bit dolgu
  ...
```

**LED baytı:** `bit0 = NumLock`, `bit1 = CapsLock`, `bit2 = ScrollLock (arka ışık)`

Çözüm: `0x04` değerini periyodik olarak göndermek. Caps Lock açıksa `0x06` (bit1 korunur).

### Cihaz kimliği

| Alan | Değer |
|---|---|
| VID:PID | `1A2C:2C27` (China Resource Semico çipi) |
| Ürün adı | "USB Keyboard" |
| Hız | Low-speed (1,5 Mbps) |
| Interface | 0 (usagePage 1, usage 6) |

---

## 2. Kurulu bileşenler

| Ne | Nerede | Görev |
|---|---|---|
| Python servisi | `~/bin/piranha-led.py` | 3 sn'de bir LED raporunu tazeler |
| Kontrol komutu | `~/bin/piranha-led` | `on` / `off` / `status` |
| LaunchAgent | `~/Library/LaunchAgents/com.hg.piranha-led.plist` | Login'de otomatik başlatır |
| Bağımlılık | `hidapitester` (Homebrew) | HID raporunu gönderen araç |
| Log | `/tmp/piranha-led.log` | Hata çıktısı (normalde boş) |

Servis durumu: `KeepAlive` + `RunAtLoad` → çökerse tekrar kalkar, açılışta kendiliğinden başlar.

---

## 3. Günlük kullanım

```bash
~/bin/piranha-led status   # çalışıyor mu?
~/bin/piranha-led off      # ışığı kapat + servisi durdur
~/bin/piranha-led on       # tekrar aç
```

Servis çalışırken **Scroll Lock ışığı kapatamaz** (3 sn'de bir geri açılıyor).
Kalıcı olarak kapatmak için: `~/bin/piranha-led off`

---

## 4. KALDIRMA (uninstall) — sırayla

```bash
# 1) Servisi durdur ve ışığı söndür
~/bin/piranha-led off

# 2) LaunchAgent'ı kaldır
rm ~/Library/LaunchAgents/com.hg.piranha-led.plist

# 3) Scriptleri sil
rm ~/bin/piranha-led.py ~/bin/piranha-led

# 4) (İsteğe bağlı) hidapitester'ı kaldır
brew uninstall hidapitester

# 5) Doğrula — hiçbir çıktı olmamalı
launchctl print gui/$(id -u)/com.hg.piranha-led 2>&1 | head -2
ls ~/bin/piranha-led* 2>&1
```

`hidapitester`'ı kaldırmazsan diskte ~200 KB durur, zararsız.

---

## 5. YENİDEN KURMA (reinstall)

```bash
# 1) Bağımlılık
brew install hidapitester
```

### 5.1. `~/bin/piranha-led.py`

```python
#!/usr/bin/env python3
"""Piranha 2345 arka isik koruyucu (Scroll Lock LED biti = 0x04)."""

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
```

### 5.2. `~/bin/piranha-led`

```bash
#!/bin/bash
# Piranha 2345 isik servisi kontrolu:  on | off | status
LABEL=com.hg.piranha-led
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_N=$(id -u)

case "${1:-status}" in
  on)
    launchctl bootstrap "gui/$UID_N" "$PLIST" 2>/dev/null
    launchctl kickstart -k "gui/$UID_N/$LABEL" 2>/dev/null
    echo "isik servisi ACIK"
    ;;
  off)
    launchctl bootout "gui/$UID_N/$LABEL" 2>/dev/null
    /opt/homebrew/bin/hidapitester --vidpid 1A2C:2C27 --usagePage 1 --usage 6 \
      -l 1 --nonexclusive --open --send-output 0 -q >/dev/null 2>&1
    echo "isik servisi KAPALI"
    ;;
  *)
    if launchctl print "gui/$UID_N/$LABEL" >/dev/null 2>&1; then
      echo "durum: CALISIYOR (pid $(launchctl print "gui/$UID_N/$LABEL" 2>/dev/null | awk '/pid =/{print $3; exit}'))"
    else
      echo "durum: KAPALI"
    fi
    ;;
esac
```

### 5.3. `~/Library/LaunchAgents/com.hg.piranha-led.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hg.piranha-led</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/hg/bin/piranha-led.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ThrottleInterval</key>
    <integer>10</integer>
    <key>ProcessType</key>
    <string>Background</string>
    <key>StandardOutPath</key>
    <string>/tmp/piranha-led.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/piranha-led.log</string>
</dict>
</plist>
```

### 5.4. Aktifleştir

```bash
chmod +x ~/bin/piranha-led.py ~/bin/piranha-led
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hg.piranha-led.plist
~/bin/piranha-led status
```

---

## 6. Bilinen tuzaklar / notlar

- **Scroll Lock artık çalışmıyor** (bilinçli): servis 3 sn'de bir biti geri yazıyor.
- **Num Lock biti yönetilmiyor.** Numpad'i Num Lock ile kullanıyorsan `LED_NUM 0x01` bitini de eklemek gerekir.
- **Caps Lock LED'i korunuyor:** `CGEventSourceKeyState(1, 57)` ile okunup rapora ekleniyor.
- **Klavye başka porta takılırsa** sorun yok — script VID:PID ile arıyor, port yolu kullanmıyor.
- **Klavye çıkarılırsa** sessizce başarısız olur, başka cihaza dokunmaz.
- **Başka klavye takılırsa** script ona hiçbir şey göndermez. Tek istisna: aynı `1A2C:2C27` kimliğine sahip başka bir ucuz klavye (çok yaygın çip) — o zaman onun da Scroll Lock LED'i yanar, zararsız.
- **Yük:** %0,16 CPU, ~11 MB RAM, 3 sn'de 1 bayt USB. Ölçüldü, ihmal edilebilir.
- **Bağlantı:** Klavye şu an 3 kademe hub zinciri arkasında (USB3 Gen2 Hub → USB2 Hub → USB2.0 HUB). Çalışıyor ama doğrudan Mac'e takmak daha sağlıklı.
- **LED ışık = ek güç:** Bus-powered hub'da ışıklı klavye + LAN + dongle birlikte güç bütçesini zorlayabilir.

---

## 7. İlgisiz ama not düşelim: Harici HDD

Aynı gün yapılan inceleme (hatırlamak için):

| Konu | Durum |
|---|---|
| Disk | 500 GB mekanik 3,5", USB, JMicron `152d:0561` köprüsü |
| Yapı | Win11: EFI + MSR + 499 GB Basic Data + WinRE |
| Şifreleme | **BitLocker** (`-FVE-FS-` imzası) → macOS bağlayamıyor |
| Hız | 92,2 / 77,5 / 46,1 MB/s (dış / orta / iç kenar) |
| Yorum | Tutarlı, sağlıklı ama yavaş model (5400 rpm veya SMR sınıfı) |

⚠️ **Önemli:** `smartctl -d jms56x` bu köprüde **sistemi dondurdu**. Tekrar deneme.
SMART gerekirse diski doğrudan SATA'ya tak veya Windows'ta CrystalDiskInfo kullan.

📌 **Sonraki iş:** Diski yedek/arşiv + "bulut gibi" senaryo için kullanma planı
(restic/borg + rclone, ya da SMB paylaşımı). BitLocker kurtarma anahtarı olmadan veri erişimi yok.
