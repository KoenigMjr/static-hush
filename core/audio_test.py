#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""!
   _____ __        __  _              __  __             __
  / ___// /_____ _/ /_(_)____        / / / /_  _______  / /
  \__ \/ __/ __ `/ __/ / ___/______ / /_/ / / / / ___/ / __ \
 ___/ / /_/ /_/ / /_/ / /__/______// __  / /_/ (__  ) / / / /
/____/\__/\__,_/\__/_/\___/       /_/ /_/\__,_/____/ /_/ /_/

             RTL_FM Squelch Calibrator "Static-Hush"
@file:        audio_test.py
@description: Acoustic verification after calibration
"""

import os
import platform
import subprocess  # <-- FIX 1: Hier fehlte der Import!


def detect_connection_type(max_levels=10):
    """
    Robustere Erkennung, ob local oder per SSH verbunden.
    """
    if platform.system() == "Linux":
        pid = os.getpid()
        try:
            for _ in range(max_levels):
                status_path = f"/proc/{pid}/status"
                try:
                    with open(status_path, "r") as f:
                        ppid = None
                        for line in f:
                            if line.startswith("PPid:"):
                                parts = line.split()
                                if len(parts) >= 2:
                                    ppid = int(parts[1])
                                break
                        if ppid is None:
                            break
                except FileNotFoundError:
                    break
                except Exception:
                    break

                try:
                    with open(f"/proc/{ppid}/comm", "r") as fc:
                        comm = fc.read().strip()
                        if comm in ("sshd", "dropbear", "ssh"):
                            # FIX 2: Gib None zurück, damit ppid nicht später als Host-IP interpretiert wird
                            return "ssh", None
                except Exception:
                    pass

                pid = ppid
                if pid <= 1:
                    break
        except Exception:
            pass

    if os.environ.get("SSH_CLIENT") or os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY"):
        ssh_client = os.environ.get("SSH_CLIENT", "").split()[0] if os.environ.get("SSH_CLIENT") else None
        return "ssh", ssh_client

    return "local", None


def test_audio_local(device, frequencies, max_squelch, gain, rtl_path):
    """
    Lokaler Audio-Test via Pipe zu aplay
    Testet alle Frequenzen gleichzeitig mit dem höchsten Squelch-Wert
    """
    print("\n[*] Starte lokalen Audio-Test (drücke Ctrl+C zum Stoppen)...\n")
    print(f"[*] Teste {len(frequencies)} Frequenzen mit Squelch={max_squelch}\n")

    rtl_proc = None
    aplay_proc = None

    try:
        # Baue rtl_fm Befehl mit mehrfachen -f Parametern
        rtl_cmd = [rtl_path, "-d", str(device), "-g", str(gain), "-M", "fm", "-E", "DC", "-s", "22050"]

        for freq in frequencies:
            rtl_cmd.extend(["-f", str(freq)])

        rtl_cmd.extend(["-l", str(max_squelch)])

        aplay_cmd = ["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw"]

        rtl_proc = subprocess.Popen(rtl_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        aplay_proc = subprocess.Popen(aplay_cmd, stdin=rtl_proc.stdout, stderr=subprocess.DEVNULL)

        rtl_proc.stdout.close()
        aplay_proc.wait()
        rtl_proc.terminate()

        print("\n[+] Audio-Test beendet.")

    except KeyboardInterrupt:
        print("\n[!] Test abgebrochen.")
    except Exception as e:
        print(f"[ERROR] Audio-Test fehlgeschlagen: {e}")
    finally:
        if rtl_proc:
            rtl_proc.terminate()
        if aplay_proc:
            aplay_proc.terminate()


def prompt_audio_test(sdr_cfg, optimal_squelch):
    """
    Benutzer-Prompt für akustischen Test nach Kalibrierung
    Unterstützt Multi-Frequency mit mehrfachen -f Parametern
    Nutzt den MAXIMALEN Squelch-Wert für -l
    """
    from core.config_loader import parse_frequencies

    device = sdr_cfg.get('device', 0)
    frequency_input = sdr_cfg.get('frequency')
    frequencies = parse_frequencies(frequency_input)
    gain = sdr_cfg.get('gain', 100)
    rtl_path = sdr_cfg.get('rtlPath', '/usr/local/bin/rtl_fm')

    # optimal_squelch kann jetzt eine Liste sein
    if isinstance(optimal_squelch, list):
        squelch_values = optimal_squelch
        max_squelch = max(squelch_values)
    else:
        squelch_values = [optimal_squelch]
        max_squelch = optimal_squelch

    conn_type, ssh_host = detect_connection_type()

    if conn_type == 'local':
        print("\n[ℹ] Du bist lokal am Rechner angemeldet.")
        try:
            response = input("\n[?] Willst du den Audiooutput jetzt akustisch testen? (y/n): ").strip().lower()
            if response == 'y':
                test_audio_local(device, frequencies, max_squelch, gain, rtl_path)
            else:
                print("[*] Audio-Test übersprungen.")
        except KeyboardInterrupt:
            print("\n[!] Abgebrochen.")

    elif conn_type == 'ssh':
        print("\n[ℹ] Verbindung erkannt: REMOTE (SSH)")
        print("\nDa du per SSH verbunden bist, kann der Ton nicht direkt über das Terminal ausgegeben werden.")
        print("\nUm den Squelch auf DEINEM PC akustisch zu testen, öffne ein NEUES lokales Terminal")
        print("(auf deinem Desktop-PC, nicht per SSH) und kopiere diesen Befehl:\n")

        user = os.environ.get('SUDO_USER') or os.environ.get('USER') or 'DEIN_USER'
        ip_placeholder = ssh_host if ssh_host else "<IP_DES_SERVERS>"

        # Baue rtl_fm Befehl mit mehrfachen -f Parametern
        freq_args = " ".join(f"-f {freq}" for freq in frequencies)

        ssh_cmd = f"ssh {user}@{ip_placeholder} \"sudo {rtl_path} -d {device} -g {gain} -M fm -E DC -s 22050 {freq_args} -l {max_squelch}\" | aplay -r 22050 -f S16_LE -t raw"

        print("-" * 75)
        print(ssh_cmd)
        print("-" * 75)
        print("\n[*] Fahre mit dem Skript fort...")
