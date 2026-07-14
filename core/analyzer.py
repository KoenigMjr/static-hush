#!/bin/bash
# -*- coding: utf-8 -*-
r"""!
   _____ __        __  _              __  __             __
  / ___// /_____ _/ /_(_)____        / / / /_  _______  / /
  \__ \/ __/ __ `/ __/ / ___/______ / /_/ / / / / ___/ / __ \
 ___/ / /_/ /_/ / /_/ / /__/______// __  / /_/ (__  ) / / / /
/____/\__/\__,_/\__/_/\___/       /_/ /_/\__,_/____/ /_/ /_/

            RTL_FM Squelch Calibrator "Static-Hush"
@file:        analyzer.py
@description:
"""


class BaseAnalyzer:
    """Abstrakte Basisklasse für alle Signal-Analysatoren."""
    def is_silent(self, raw_data: bytes) -> bool:
        raise NotImplementedError


class ByteCountAnalyzer(BaseAnalyzer):
    """Der aktuelle Analysator, der nur das Datenvolumen prüft."""
    def __init__(self, threshold=4000):
        self.threshold = threshold

    def is_silent(self, raw_data: bytes) -> bool:
        # Wenn weniger als 'threshold' Bytes kamen, gilt es als stumm (Squelch zu)
        return len(raw_data) < self.threshold


# =====================================================================
# PLATZHALTER FÜR SPÄTER (Audio-Varianz-Modul)
# =====================================================================
class AudioVarianceAnalyzer(BaseAnalyzer):
    """Zukünftiger Analysator für echte Signal- und Varianzanalyse."""
    def __init__(self):
        pass

    def is_silent(self, raw_data: bytes) -> bool:
        # 1. Konvertiere raw_data (PCM 16-Bit) in ein numpy-Array
        # 2. Berechne Standardabweichung / Varianz
        # 3. Wenn Varianz flach -> Rauschen/Stille -> True
        # 4. Wenn Varianz dynamisch -> Sprache/Signal -> False
        print("     [Analysator] AudioVariance noch nicht aktiv!")
        return True
