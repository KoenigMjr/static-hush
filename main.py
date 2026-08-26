#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""!
   _____ __        __  _              __  __             __
  / ___// /_____ _/ /_(_)____        / / / /_  _______  / /
  \__ \/ __/ __ `/ __/ / ___/______ / /_/ / / / / ___/ / __ \
 ___/ / /_/ /_/ / /_/ / /__/______// __  / /_/ (__  ) / / / /
/____/\__/\__,_/\__/_/\___/       /_/ /_/\__,_/____/ /_/ /_/

             RTL_FM Squelch Calibrator "Static-Hush"
@file:        main.py
@description:
"""

import sys
from core.config_loader import load_config, save_config, build_rtl_fm_args, parse_frequencies
from core.receiver import RtlFmReceiver
from core.analyzer import ByteCountAnalyzer  # Später: AudioVarianceAnalyzer
from core.strategy import SquelchOptimizer
from core.audio_test import prompt_audio_test


def main():
    # 1. Konfiguration laden
    config = load_config()
    global_cfg = config.get('global', {})

    print("=" * 60)
    print(" MODULARES RTL_FM SQUELCH KALIBRIERUNGS-TOOL ")
    print("=" * 60)

    # 2. BOSWatch3 Block verarbeiten
    if "inputSource" not in config or "sdr" not in config["inputSource"]:
        print("Fehler: Kein 'inputSource -> sdr' Block in der config.yaml gefunden!")
        sys.exit(1)

    sdr_cfg = config["inputSource"]["sdr"]

    # Werte extrahieren und umwandeln
    rtl_binary = sdr_cfg.get("rtlPath", "/usr/local/bin/rtl_fm")
    frequencies = parse_frequencies(sdr_cfg.get("frequency"))  # ← JETZT Liste!
    base_args = build_rtl_fm_args(sdr_cfg)

    print("[*] BOSWatch3 Konfiguration erkannt!")
    for idx, freq_hz in enumerate(frequencies, 1):
        print(f"    ➔ Frequenz {idx}/{len(frequencies)}:  {freq_hz / 1e6:.4f} MHz")
    print(f"    ➔ Basis-Cmd: {rtl_binary} {base_args}\n")

    # Trick: Wir schreiben base_args und rtlPath temporär in global_cfg,
    # damit RtlFmReceiver sie wie gewohnt findet, ohne dass wir receiver.py ändern müssen.
    global_cfg['rtl_fm_args'] = base_args
    global_cfg['rtlPath'] = rtl_binary

    # 3. Module initialisieren (BOSWatch Style Dependency Injection)
    receiver = RtlFmReceiver(global_cfg)
    analyzer = ByteCountAnalyzer(threshold=4000)
    # Wenn du später wechseln willst, tauschst du einfach die Zeile aus gegen:
    # analyzer = AudioVarianceAnalyzer()

    optimizer = SquelchOptimizer(receiver, analyzer, global_cfg)

    # 4. Kalibrierung für JEDE Frequenz abarbeiten
    squelch_results = {}  # Speichere alle Ergebnisse

    for idx, freq_hz in enumerate(frequencies, 1):
        name = f"BOSWatch SDR (Gerät {sdr_cfg.get('device', 0)}, Frequenz {idx}/{len(frequencies)})"
        print(f"\n[*] Starte Kalibrierung für: {name} ({freq_hz / 1e6:.4f} MHz)")

        # Schritt A: Warten bis frei
        optimizer.wait_for_free_channel(freq_hz)

        # Schritt B: Squelch via Binärsuche finden
        optimal_val = optimizer.binary_search(freq_hz)

        # Schritt C: Verifizieren
        if not optimizer.verify(freq_hz, optimal_val):
            optimal_val = min(optimal_val + global_cfg.get('step_size', 5), global_cfg.get('max_squelch', 150))
            print("   [!] Ergebnis unsicher. Sicherheitsaufschlag angewendet.")

        print(f"[=>] Fertig für {name}: Optimaler Squelch = {optimal_val}")
        squelch_results[freq_hz] = optimal_val

    # 5. Ergebnisse sichern
    # Falls mehrere Frequenzen: Speichere eine Liste mit Squelch-Werte pro Frequenz
    if len(frequencies) == 1:
        sdr_cfg['squelch'] = squelch_results[frequencies[0]]
    else:
        sdr_cfg['squelch'] = list(squelch_results.values())

    save_config(config)
    print("\n[+] Squelch erfolgreich in config.yaml kalibriert und gespeichert!")

    # 6. Akustischer Test anbieten
    # Übergib die squelch_results direkt (als Liste bei Multi-Freq)
    if len(frequencies) == 1:
        prompt_audio_test(sdr_cfg, squelch_results[frequencies[0]])
    else:
        prompt_audio_test(sdr_cfg, list(squelch_results.values()))


if __name__ == "__main__":
    main()
