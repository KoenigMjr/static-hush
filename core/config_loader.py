#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""!
   _____ __        __  _              __  __             __
  / ___// /_____ _/ /_(_)____        / / / /_  _______  / /
  \__ \/ __/ __ `/ __/ / ___/______ / /_/ / / / / ___/ / __ \
 ___/ / /_/ /_/ / /_/ / /__/______// __  / /_/ (__  ) / / / /
/____/\__/\__,_/\__/_/\___/       /_/ /_/\__,_/____/ /_/ /_/

            RTL_FM Squelch Calibrator "Static-Hush"
@file:        config_loader.py
@description: Lädt/speichert Config und wandelt BOSWatch-Parameter um
"""

import os
import sys
from ruamel.yaml import YAML

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")

yaml = YAML()
yaml.preserve_quotes = True


def parse_frequency(freq_input):
    """
    Wandelt Frequenzangaben wie '172.640M', '172.640', oder '172640000' in Hz (int) um.
    """
    freq_str = str(freq_input).strip().upper()
    if freq_str.endswith('M'):
        return int(float(freq_str[:-1]) * 1_000_000)
    elif freq_str.endswith('K'):
        return int(float(freq_str[:-1]) * 1_000)
    else:
        val = float(freq_str)
        if val < 1000:  # Falls als MHz-Fließkommazahl ohne 'M' angegeben (z.B. 172.64)
            return int(val * 1_000_000)
        return int(val)


def build_rtl_fm_args(sdr_cfg):
    """
    Baut die rtl_fm Argumente exakt analog zur sdrInput.py von BOSWATCH3 auf.
    (Die Parameter -f und -l werden später dynamisch angehängt).
    """
    args = []

    # Hardware & Tuner Parameter wie aus BOSWatch Config
    args.append(f"-d {sdr_cfg.get('device', 0)}")
    args.append(f"-p {sdr_cfg.get('error', 0)}")
    args.append(f"-g {sdr_cfg.get('gain', 100)}")

    # Optionaler FIR-Filter
    if sdr_cfg.get("fir_size") is not None:
        args.append(f"-F {sdr_cfg.get('fir_size')}")

    # Feste BOSWATCH3 Standard-Flags
    args.append("-M fm")
    args.append("-E DC")
    args.append("-s 22050")

    return " ".join(args)


def load_config(path=DEFAULT_CONFIG_PATH):
    try:
        with open(path, 'r', encoding="utf-8") as f:
            config = yaml.load(f)
            if config is None:
                print(f"Fehler: Die Datei {path} ist leer!")
                sys.exit(1)
            return config

    except FileNotFoundError:
        print(f"Fehler: Konfigurationsdatei nicht gefunden unter:\n{path}")
        sys.exit(1)
    except Exception as exc:
        print(f"Fehler: Die config.yaml enthält einen Formatierungsfehler!\nDetails: {exc}")
        sys.exit(1)


def save_config(config, path=DEFAULT_CONFIG_PATH):
    try:
        with open(path, 'w', encoding="utf-8") as f:
            yaml.dump(config, f)
    except Exception as e:
        print(f"Fehler beim Speichern der config.yaml: {e}")
