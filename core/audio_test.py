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


def test_audio_local(device, frequency, squelch, gain, rtl_path):
    """
    Lokaler Audio-Test via Pipe zu aplay
    """
    print("\n[*] Starte lokalen Audio-Test (drücke Ctrl+C zum Stoppen)...\n")

    # FIX 3: Variablen vorab definieren, um UnboundLocalError im except zu vermeiden
    rtl_proc = None
    aplay_proc = None

    try:
        rtl_cmd = [
            rtl_path, "-d", str(device), "-g", str(gain),
            "-M", "fm", "-E", "DC", "-s", "22050",
            "-f", str(frequency), "-l", str(squelch)
        ]

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
        # Sauber aufräumen, egal ob Erfolg oder Fehler
        if rtl_proc:
            rtl_proc.terminate()
        if aplay_proc:
            aplay_proc.terminate()


def prompt_audio_test(sdr_cfg, optimal_squelch):
    """
    Benutzer-Prompt für akustischen Test nach Kalibrierung
    """
    device = sdr_cfg.get('device', 0)
    frequency = sdr_cfg.get('frequency')
    gain = sdr_cfg.get('gain', 100)
    rtl_path = sdr_cfg.get('rtlPath', '/usr/local/bin/rtl_fm')

    conn_type, ssh_host = detect_connection_type()

    if conn_type == 'local':
        print("\n[ℹ] Du bist lokal am Rechner angemeldet.")
        try:
            response = input("\n[?] Willst du den Audiooutput jetzt akustisch testen? (y/n): ").strip().lower()
            if response == 'y':
                test_audio_local(device, frequency, optimal_squelch, gain, rtl_path)
            else:
                print("[*] Audio-Test übersprungen.")
        except KeyboardInterrupt:
            print("\n[!] Abgebrochen.")

    elif conn_type == 'ssh':
        # FIX 4: Zurück zur Copy-Paste Logik, da ein Reverse-SSH-Tunnel fehleranfällig ist.
        print("\n[ℹ] Verbindung erkannt: REMOTE (SSH)")
        print("\nDa du per SSH verbunden bist, kann der Ton nicht direkt über das Terminal ausgegeben werden.")
        print("\nUm den Squelch auf DEINEM PC akustisch zu testen, öffne ein NEUES lokales Terminal")
        print("(auf deinem Desktop-PC, nicht per SSH) und kopiere diesen Befehl:\n")

        user = os.environ.get('SUDO_USER') or os.environ.get('USER') or 'DEIN_USER'
        ip_placeholder = ssh_host if ssh_host else "<IP_DES_SERVERS>"

        print("-" * 75)
        print(f"ssh {user}@{ip_placeholder} \"sudo {rtl_path} -d {device} -g {gain} -M fm -E DC -s 22050 -f {frequency} -l {optimal_squelch}\" | aplay -r 22050 -f S16_LE -t raw")
        print("-" * 75)
        print("\n[*] Fahre mit dem Skript fort...")
