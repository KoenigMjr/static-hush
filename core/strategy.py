#!/bin/bash
# -*- coding: utf-8 -*-
r"""!
   _____ __        __  _              __  __             __
  / ___// /_____ _/ /_(_)____        / / / /_  _______  / /
  \__ \/ __/ __ `/ __/ / ___/______ / /_/ / / / / ___/ / __ \
 ___/ / /_/ /_/ / /_/ / /__/______// __  / /_/ (__  ) / / / /
/____/\__/\__,_/\__/_/\___/       /_/ /_/\__,_/____/ /_/ /_/

            RTL_FM Squelch Calibrator "Static-Hush"
@file:        strategy.py
@description:
"""

import time


class SquelchOptimizer:
    def __init__(self, receiver, analyzer, global_config):
        self.receiver = receiver
        self.analyzer = analyzer
        self.cfg = global_config

    def run_measurement(self, freq, squelch):
        """Hilfsfunktion: Startet die Hardware, wartet, stoppt und analysiert."""
        self.receiver.start_capture(freq, squelch)
        time.sleep(self.cfg.get('test_duration', 2.0))
        data = self.receiver.stop_capture()
        return self.analyzer.is_silent(data), len(data)

    def wait_for_free_channel(self, freq):
        max_sq = self.cfg['max_squelch']
        while True:
            is_silent, data_len = self.run_measurement(freq, max_sq)
            if is_silent:
                break
            print(f"   [!] Kanal belegt ({data_len} Bytes bei Squelch {max_sq}). Warte 5s...")
            time.sleep(5)

    def binary_search(self, freq):
        low = 0
        high = self.cfg['max_squelch']
        optimal_squelch = high

        print("   [->] Starte Binäre Suche...")
        while low <= high:
            mid = (low + high) // 2
            is_silent, _ = self.run_measurement(freq, mid)

            if is_silent:
                print(f"        Squelch {mid:3d}: STUMM")
                optimal_squelch = mid
                high = mid - 1
            else:
                print(f"        Squelch {mid:3d}: OFFEN")
                low = mid + 1
        return optimal_squelch

    def verify(self, freq, squelch_val):
        print(f"   [->] Redundanz-Check für Squelch {squelch_val}...")
        for i in range(2):
            is_silent, _ = self.run_measurement(freq, squelch_val)
            if not is_silent:
                return False
            print(f"        Check {i+1}/2: OK")
        return True
