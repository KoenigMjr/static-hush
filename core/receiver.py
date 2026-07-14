#!/bin/bash
# -*- coding: utf-8 -*-
r"""!
   _____ __        __  _              __  __             __
  / ___// /_____ _/ /_(_)____        / / / /_  _______  / /
  \__ \/ __/ __ `/ __/ / ___/______ / /_/ / / / / ___/ / __ \
 ___/ / /_/ /_/ / /_/ / /__/______// __  / /_/ (__  ) / / / /
/____/\__/\__,_/\__/_/\___/       /_/ /_/\__,_/____/ /_/ /_/

            RTL_FM Squelch Calibrator "Static-Hush"
@file:        receiver.py
@description:
"""

import subprocess
import threading
# import time


class RtlFmReceiver:
    def __init__(self, global_config):
        self.global_cfg = global_config
        self.proc = None
        self.buffer = bytearray()
        self.lock = threading.Lock()
        self._stop_signal = False

    def _reader_worker(self):
        """Liest den stdout-Stream asynchron in einen internen Buffer."""
        while not self._stop_signal and self.proc:
            data = self.proc.stdout.read(4096)
            if not data:
                break
            with self.lock:
                self.buffer.extend(data)

    def start_capture(self, frequency, squelch_val):
        """Startet den rtl_fm Prozess für eine bestimmte Zeit."""
        self.buffer.clear()
        self._stop_signal = False

        extra_args = self.global_cfg.get('rtl_fm_args', '').split()
        cmd = ["rtl_fm", "-f", str(frequency), "-l", str(squelch_val)] + extra_args + ["-"]

        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        # Lese-Thread starten
        self.worker_thread = threading.Thread(target=self._reader_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def stop_capture(self):
        """Stoppt den Prozess und gibt die gesammelten Rohdaten zurück."""
        self._stop_signal = True
        if self.proc:
            self.proc.terminate()
            self.proc.wait()
        if self.worker_thread:
            self.worker_thread.join(timeout=0.5)

        with self.lock:
            captured_data = bytes(self.buffer)
            self.buffer.clear()

        return captured_data
