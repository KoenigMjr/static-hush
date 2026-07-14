# 🤫 Static-Hush

> **Der automatische RTL_FM Squelch-Kalibrator**

**Static-Hush** ist ein modulares, python-basiertes Tool zur automatischen Ermittlung des optimalen Rauschsperren-Werts (Squelch) für RTL-SDR Empfänger (`rtl_fm`). 

Anstatt mühsam jeden Kanal manuell einzurauschen, nutzt **Static-Hush** eine hocheffiziente **Halbintervallsuche (Binäre Suche)** kombiniert mit einem intelligenten **Belegt-Schutz**, einem **doppelten Redundanz-Check** und einer **optionalen akustischen Verifizierung**.

---

## ✨ Features

* ⚡ **Binäre Suche:** Reduziert die Kalibrierungszeit pro Kanal um bis zu 80% (ca. 15s statt 60s pro Frequenz).
* 🚦 **Belegt-Schutz:** Erkennt, wenn auf einer Frequenz gerade aktiv gesprochen wird, wartet automatisch auf einen freien Kanal und kalibriert erst bei Stille.
* 🛡️ **Doppelter Redundanz-Check:** Verifiziert den gefundenen Squelch-Wert mehrfach. Zittert die Rauschgrenze, wird automatisch eine Sicherheitsmarge aufgeschlagen.
* 🎧 **Akustische Verifizierung:** Nach der Kalibrierung kann der Audio-Output direkt am Empfänger getestet werden – unterstützt lokale und SSH-Verbindungen.
* 🔌 **Modularer Aufbau:** Saubere Trennung von Hardware-Receiver, Analyse-Logik und Suchstrategie.
* 📦 **Schlüsselfertige Installation:** Vollautomatisches Bash-Installationsskript inklusive Kompilierung der neuesten RTL-SDR-Bibliotheken und Einrichtung eines Python `venv`.

---

## 🛠️ Systemanforderungen

* Ein Debian-basiertes Linux-System (z. B. Linux Mint, Debian, Ubuntu, Raspberry Pi OS).
* Ein kompatibler RTL-SDR USB-Dongle.
* Für akustische Verifizierung: `aplay` (Teil von `alsa-utils`, meist vorinstalliert).
* Root-Rechte (für das Installationsskript und die Geräteverwaltung).

---

## 🚀 Installation & Setup

Dank des Installationsskripts ist das Setup in wenigen Schritten erledigt:

1. **Repository klonen oder herunterladen:**
   ```bash
   # TESTING
   git clone https://github.com/KoenigMjr/static-hush.git
   # PRODUKTIV
   wget https://github.com/KoenigMjr/static-hush/raw/master/install.sh
   cd static-hush
   ```

1b. **Installationsskript ausführbar machen:**
   ```bash
   chmod +x install.sh
   # ENTFÄLLT PRODUKTIV
   ```

2. **Installation starten:**
   Das Skript aktualisiert dein System, kompiliert `rtl-sdr` frisch aus den Quellen, richtet das Python `venv` ein und sperrt kollidierende DVB-T-Standardtreiber.
   ```bash
   sudo ./install.sh
   # PRODUKTIV
   sudo bash install.sh
   ```
   *(Tipp: Mit `sudo ./install.sh -r` startet das System nach erfolgreicher Installation direkt automatisch neu).*

3. **System neustarten:**
   Falls du das System nicht automatisch hast neustarten lassen, führe jetzt einen Reboot durch. Das ist zwingend erforderlich, damit die SDR-Udev-Regeln und die Treiber-Sperren greifen:
   ```bash
   sudo reboot
   ```

---

## ⚙️ Konfiguration

Nach der Installation liegt das Programm im Verzeichnis `/opt/static-hush`. Die Frequenzen und globalen Parameter werden in der `config.yaml` gepflegt.

Öffne die Konfiguration mit deinem Lieblings-Editor:
```bash
sudo nano /opt/static-hush/config.yaml
```

### Beispiel `config.yaml`:
```yaml
global:
  max_squelch: 150                 # Suchbereich für die Binärsuche (0 bis 150)
  test_duration: 2.0               # Testdauer pro Kalibrierungsschritt in Sek.
  step_size: 5                     # Sicherheitsaufschlag bei grenzwertigem Rauschen

# DIRECT BOSWATCH3 INPUT SOURCE BLOCK:
inputSource:
  sdr:
    device: 0                      # Gerätenummer (0 = erstes, 1 = zweites Gerät, etc.)
    frequency: 85M                 # Erkennt automatisch 'M' (MHz), 'K' (kHz) oder Rohwerte
    error: 0                       # PPM-Fehler für Frequenzabweichung
    squelch: 0                     # Wird von Static-Hush ermittelt und direkt überschrieben!
    gain: 100                      # Gain-Wert für rtl_fm (0-49)
    rtlPath: /usr/local/bin/rtl_fm # Pfad zu rtl_fm
```

**Hinweis:** Das `device`-Feld wird erkannt und an `rtl_fm` übergeben (z.B. `-d 0` oder `-d 1` für mehrere Sticks). Falls du mehrere Geräte hast, musst du derzeit das Script mehrfach mit unterschiedlichen Config-Dateien aufrufen oder die Device-ID manuell anpassen.

---

## 🏃 Quickstart (Programm ausführen)

Um die Kalibrierung zu starten, führst du einfach das Hauptskript aus. Da `rtl_fm` direkten Zugriff auf die USB-Schnittstelle benötigt, muss das Skript mit Root-Rechten gestartet werden:

```bash
sudo /opt/static-hush/venv/bin/python3 /opt/static-hush/main.py
```

### Was passiert während des Laufs?
1. **Belegt-Check:** Das Tool prüft die Frequenz bei maximalem Squelch. Fließen Daten, wird gewartet.
2. **Suche:** Per Halbintervallsuche springt das Tool logarithmisch durch die Squelch-Ebenen, bis die exakte Rauschgrenze gefunden ist.
3. **Verify:** Der Wert wird doppelt geprüft. Bei Instabilität wird automatisch eine Sicherheitsmarge addiert.
4. **Save:** Die ermittelten Werte werden direkt in deine `/opt/static-hush/config.yaml` zurückgeschrieben.
5. **Audio-Test (optional):** Nach erfolgreicher Kalibrierung kannst du den Audio-Output akustisch verifizieren:
   ```
   [ℹ] Du bist lokal am Rechner angemeldet.
   [?] Willst du den Audiooutput jetzt akustisch testen? (y/n): _
   ```
   - Antworte mit `y` zum Starten des Audio-Streams (Ctrl+C zum Stoppen).
   - Antworte mit `n` oder drücke Enter zum Überspringen.

### Audio-Verifizierung: Lokal vs. SSH
Das Tool erkennt automatisch, ob du lokal oder per SSH angemeldet bist:
- **Lokal:** Audio-Stream wird direkt über deine Soundkarte ausgegeben.
- **SSH:** Der Remote-`rtl_fm`-Prozess wird gestartet, der Audio-Stream wird zu deinem lokalen `aplay` gepipet.

---

## 📂 Projektstruktur

```text
/opt/static-hush/
├── config.yaml          # Deine Frequenzen und Ergebnisse
├── main.py              # Core-Orchestrator (Main Entry Point)
├── requirements.txt     # Python-Abhängigkeiten (pyyaml, ruamel.yaml)
├── venv/                # Isoliertes Python Virtual Environment
└── core/                # Modul-Ordner
    ├── __init__.py
    ├── config_loader.py # YAML Reader/Writer + Frequenz-Konvertierung
    ├── receiver.py      # Steuerung des rtl_fm Prozesses
    ├── analyzer.py      # Signal-Analysatoren (erweiterbar!)
    ├── strategy.py      # Binäre Suchlogik & Verifizierung
    └── audio_test.py    # Akustische Verifizierung (lokal & SSH)
```

---

## 🔌 Modulare Erweiterung (Entwickler)

### Custom Analyzer schreiben
In `core/analyzer.py` findest du die Klasse `BaseAnalyzer`. Standardmäßig liest der `ByteCountAnalyzer` stumpf das Datenvolumen aus der Pipe aus.

Wenn du eine fortgeschrittenere Methode (wie z. B. eine **Audio-Varianz-Analyse** zur Unterscheidung von monotonem Rauschen und dynamischer Sprache) einbinden möchtest:

1. Schreibe einen neuen Analysator in `core/analyzer.py`, der von `BaseAnalyzer` erbt.
2. Tausche in `main.py` die Instanziierung des `analyzers` aus. 
3. *Fertig!* Der gesamte Rest des Programms (Prozesshandling, Binärsuche, YAML-Verarbeitung) bleibt völlig unberührt.

```python
# Beispiel: Custom Analyzer
class AudioVarianceAnalyzer(BaseAnalyzer):
    def analyze(self, data):
        # Deine Custom-Logik hier
        return signal_detected
```

### Dependency Injection Pattern
Static-Hush nutzt konsequent **Dependency Injection** für maximale Modularität:
- `RtlFmReceiver` – Hardware-Abstraktionsschicht
- `BaseAnalyzer` – Signal-Analyse (austauschbar)
- `SquelchOptimizer` – Suchstrategie

Diese können unabhängig getestet und ausgetauscht werden.

---

## 🐛 Troubleshooting

### `rtl_fm: command not found`
Stelle sicher, dass das Installationsskript erfolgreich durchgelaufen ist und `rtl-sdr` korrekt kompiliert wurde:
```bash
which rtl_fm
/usr/local/bin/rtl_fm  # sollte so aussehen
```

### `Permission denied: /dev/bus/usb/...`
Die udev-Regeln wurden nicht korrekt gesetzt. Führe einen Reboot durch:
```bash
sudo reboot
```

### Audio-Test zeigt Fehler unter SSH
Stelle sicher, dass `aplay` auf deinem lokalen System installiert ist:
```bash
sudo apt install alsa-utils
```

---

## 📝 Lizenz

Dieses Projekt ist Open Source. Beiträge sind willkommen!

### Transparenzhinweis & KI-Unterstützung (EU-KI-Gesetz / AI Act)
Die Inhalte, der Quellcode und die Dokumentation dieses Repositories wurden teilweise unter der Mitarbeit von künstlicher Intelligenz (KI) generiert, optimiert und debugged. 

Im Einklang mit den Transparenzanforderungen des EU-KI-Gesetzes (EU AI Act) weisen wir darauf hin, dass:
* **Menschliche Kontrolle:** Alle durch KI erzeugten oder bearbeiteten Inhalte und Codefragmente wurden von einem Menschen sorgfältig geprüft, verifiziert und getestet.
* **Letztverantwortung:** Die finale redaktionelle und technische Verantwortung liegt vollständig beim menschlichen Betreiber dieses Repositories.
