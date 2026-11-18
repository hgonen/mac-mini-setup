# mac-mini-setup

Mac mini'mde yaptığım sistem ayarlarının ve kurulumların kaydı.
Amaç: bir şey bozulursa / makine değişirse buradan aynısını kurabilmek.

## İçerik

| Yol | Ne |
|---|---|
| `docs/piranha-2345-macos.md` | Piranha 2345 klavye arka ışığı çözümü — tam kurulum/kaldırma rehberi + harici HDD notları |
| `scripts/piranha-led.py` | LED raporunu 3 sn'de bir tazeleyen servis |
| `scripts/piranha-led` | `on` / `off` / `status` kontrol komutu |
| `launchd/com.hg.piranha-led.plist` | Login'de otomatik başlatan LaunchAgent |

## Hızlı kurulum (yeni makine)

```bash
brew install hidapitester
mkdir -p ~/bin
cp scripts/piranha-led.py scripts/piranha-led ~/bin/
chmod +x ~/bin/piranha-led.py ~/bin/piranha-led
cp launchd/com.hg.piranha-led.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hg.piranha-led.plist
~/bin/piranha-led status
```

> `plist` içindeki `/Users/hg/bin/piranha-led.py` yolu kullanıcı adına bağlı —
> farklı kullanıcı adıyla kurarsan düzelt.

## Hızlı kaldırma

```bash
~/bin/piranha-led off
rm ~/Library/LaunchAgents/com.hg.piranha-led.plist ~/bin/piranha-led.py ~/bin/piranha-led
```

Detaylar ve teknik açıklama: [`docs/piranha-2345-macos.md`](docs/piranha-2345-macos.md)

## Not

`~/bin` (canlı dosyalar) ile bu repo arasında otomatik senkron **yok**.
Canlı dosyada değişiklik yaparsan buradaki kopyayı da güncelle.
