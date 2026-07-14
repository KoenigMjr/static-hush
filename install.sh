#!/bin/bash
# -*- coding: utf-8 -*-
#   _____ __        __  _              __  __             __
#  / ___// /_____ _/ /_(_)____        / / / /_  _______  / /_
#  \__ \/ __/ __ `/ __/ / ___/______ / /_/ / / / / ___/ / __ \
# ___/ / /_/ /_/ / /_/ / /__/______// __  / /_/ (__  ) / / / /
#/____/\__/\__,_/\__/_/\___/       /_/ /_/\__,_/____/ /_/ /_/ #
#
#            RTL_FM Squelch Calibrator "Static-Hush"
#@file:        install.sh
#@description: Dediziertes Installationsskript für Static-Hush

# ============================================================================
# KONFIGURATION UND FUNKTIONEN
# ============================================================================

set -u  # Fehler bei ungesetzten Variablen

# Farbcodes für bessere Lesbarkeit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Globale Variablen
target_path="/opt/static-hush"
install_tmp_path="/opt/static-hush-install"
reboot=false
log_file=""

# Funktion: Fehlerbehandlung
exitcodefunction() {
  local errorcode=$1
  local action=$2
  local module=$3

  if [ $errorcode -ne 0 ]; then
    echo -e "${RED}[FEHLER] Action '${action}' für '${module}' fehlgeschlagen (Exit-Code: ${errorcode})${NC}" | tee -a "$log_file"
    exit 1
  else
    echo -e "${GREEN}[OK]${NC} ${action} für ${module}" | tee -a "$log_file"
  fi
}

# Funktion: Fortschrittsanzeige (einfach, zuverlässig)
print_step() {
  local step=$1
  local total=$2
  local message=$3
  local percent=$((step * 100 / total))
  
  echo ""
  echo -e "${BLUE}[${step}/${total}]${NC} ${message}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

# ASCII-Art Banner (nur mit echo, keine Probleme mit Escaping)
clear

echo ""
echo "   _____ __        __  _              __  __             __  "
echo "  / ___// /_____ _/ /_(_)____        / / / /_  _______  / /_ "
echo "  \__ \/ __/ __ \`/ __/ / ___/______ / /_/ / / / / ___/ / __ \\"
echo " ___/ / /_/ /_/ / /_/ / /__/______// __  / /_/ (__  ) / / / /"
echo "/____/\__/\__,_/\__/_/\___/       /_/ /_/\__,_/____/ /_/ /_/ "
echo ""
echo "              Static-Hush - RTL_FM Squelch Calibrator          "
echo ""
echo ""

# Prüfung auf Root-Rechte
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}[FEHLER] Dieses Skript muss als root ausgeführt werden!${NC}"
   echo "Bitte ausführen mit: sudo bash install.sh"
   exit 1
fi

# Tatsächlichen Benutzer ermitteln (für spätere Rechtevergabe)
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_GROUP=$(id -gn "$ACTUAL_USER")
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Argumente parsen
while [[ $# -gt 0 ]]; do
  case $1 in
    -r|--reboot)
      reboot=true
      shift
      ;;
    -p|--path)
      target_path="$2"
      echo -e "${YELLOW}[WARNUNG] Installiere in alternatives Verzeichnis: ${target_path}${NC}"
      shift 2
      ;;
    *)
      echo -e "${RED}[FEHLER] Unbekannter Parameter: $1${NC}"
      echo "Verwendung: sudo bash install.sh [-r|--reboot] [-p|--path <pfad>]"
      exit 1
      ;;
  esac
done

# Verzeichnisse erstellen
mkdir -p "$install_tmp_path"
mkdir -p "$target_path"
VENV_PATH="${target_path}/venv"
log_file="${install_tmp_path}/setup_log.txt"

echo -e "${BLUE}[INFO]${NC} Installation startet. Logs unter: ${log_file}"
echo ""

# ============================================================================
# SCHRITT 1: System Update
# ============================================================================
print_step 1 7 "System Update (apt-get update)"
apt-get update -y > "$log_file" 2>&1
exitcodefunction $? "apt-get update" "Paketmanager"

# ============================================================================
# SCHRITT 2: Build-Tools und Systembibliotheken
# ============================================================================
print_step 2 7 "Installiere Build-Tools und USB-Bibliotheken"
apt-get -y install git cmake build-essential libusb-1.0-0-dev >> "$log_file" 2>&1
exitcodefunction $? "Paketinstallation" "Compiler-Tools"

# ============================================================================
# SCHRITT 3: Python installieren
# ============================================================================
print_step 3 7 "Installiere Python 3 und Virtual Environment"
apt-get -y install python3 python3-pip python3-venv >> "$log_file" 2>&1
exitcodefunction $? "Paketinstallation" "Python3"

# ============================================================================
# SCHRITT 4: RTL-SDR klonen und kompilieren
# ============================================================================
print_step 4 7 "Klone und kompiliere rtl-sdr von GitHub"
cd "$install_tmp_path"
git clone --branch master https://github.com/osmocom/rtl-sdr.git rtl-sdr >> "$log_file" 2>&1
exitcodefunction $? "git clone" "rtl-sdr Repository"

cd "$install_tmp_path/rtl-sdr/"
git checkout 2659e2df31e592d74d6dd264a4f5ce242c6369c8 >> "$log_file" 2>&1

mkdir -p build && cd build
echo -e "${BLUE}[*]${NC} Führe cmake aus..."
cmake ../ -DINSTALL_UDEV_RULES=ON >> "$log_file" 2>&1
exitcodefunction $? "cmake" "rtl-sdr"

echo -e "${BLUE}[*]${NC} Kompiliere (make)..."
make >> "$log_file" 2>&1
exitcodefunction $? "make" "rtl-sdr"

echo -e "${BLUE}[*]${NC} Installiere..."
make install >> "$log_file" 2>&1
exitcodefunction $? "make install" "rtl-sdr"

ldconfig >> "$log_file" 2>&1
exitcodefunction $? "ldconfig" "Systembibliotheken"

# ============================================================================
# SCHRITT 5: Eigene Programmdateien kopieren
# ============================================================================
print_step 5 7 "Kopiere Programmdateien nach ${target_path}"
mkdir -p "$target_path"
cp -r "${SCRIPT_DIR}/core" "${target_path}/" >> "$log_file" 2>&1
exitcodefunction $? "Kopieren (core/)" "Static-Hush Module"

cp "${SCRIPT_DIR}/main.py" "${target_path}/" >> "$log_file" 2>&1
exitcodefunction $? "Kopieren (main.py)" "Static-Hush"

cp "${SCRIPT_DIR}/config.yaml" "${target_path}/" >> "$log_file" 2>&1
exitcodefunction $? "Kopieren (config.yaml)" "Static-Hush"

cp "${SCRIPT_DIR}/requirements.txt" "${target_path}/" >> "$log_file" 2>&1
exitcodefunction $? "Kopieren (requirements.txt)" "Static-Hush"

# ============================================================================
# SCHRITT 6: Python Virtual Environment einrichten
# ============================================================================
print_step 6 7 "Richte Python Virtual Environment ein"
python3 -m venv "$VENV_PATH" >> "$log_file" 2>&1
exitcodefunction $? "python3 -m venv" "Python venv"

echo -e "${BLUE}[*]${NC} Installiere pip-Abhängigkeiten..."
"${VENV_PATH}/bin/pip" install --upgrade pip >> "$log_file" 2>&1
"${VENV_PATH}/bin/pip" install -r "${target_path}/requirements.txt" >> "$log_file" 2>&1
exitcodefunction $? "pip install" "Python Pakete"

# ============================================================================
# SCHRITT 7: Treiber-Blacklist konfigurieren
# ============================================================================
print_step 7 7 "Konfiguriere DVB-T Treiber Blacklist"
cat > /etc/modprobe.d/static_hush_blacklist.conf << 'BLACKLIST'
# Static-Hush - Verhindere Konflikte mit DVB-T Standardtreibern
blacklist dvb_usb_rtl28xxu
blacklist rtl2830
blacklist dvb_usb_v2
blacklist dvb_core
BLACKLIST
exitcodefunction $? "Treiber-Blacklist schreiben" "Modprobe"

# ============================================================================
# BERECHTIGUNGEN ANPASSEN
# ============================================================================
echo -e "${BLUE}[*]${NC} Passe Dateiberechtigungen an..."
chown -R "${ACTUAL_USER}:${ACTUAL_GROUP}" "$target_path" >> "$log_file" 2>&1
chmod +x "${target_path}/main.py" >> "$log_file" 2>&1
chmod 664 "${target_path}/config.yaml" >> "$log_file" 2>&1

# ============================================================================
# ERFOLGSMELDUNG
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ Static-Hush wurde erfolgreich installiert!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}WICHTIG:${NC} Das System MUSS nun neu gestartet werden,"
echo "damit die Treiber-Sperren und Udev-Regeln aktiviert werden!"
echo ""
echo -e "${BLUE}Installationsverzeichnis:${NC}"
echo "  ${target_path}"
echo ""
echo -e "${BLUE}Starten des Programms (nach Reboot):${NC}"
echo "  sudo ${VENV_PATH}/bin/python3 ${target_path}/main.py"
echo ""
echo -e "${BLUE}Logs dieser Installation:${NC}"
echo "  ${log_file}"
echo ""

# ============================================================================
# CLEANUP & OPTIONALER REBOOT
# ============================================================================
mkdir -p "${target_path}/log/install"
if [ -f "$log_file" ]; then
  cp "$log_file" "${target_path}/log/install/"
fi
rm -rf "$install_tmp_path"

if [ "$reboot" = true ]; then
  echo -e "${YELLOW}[INFO] System wird in 10 Sekunden neu gestartet...${NC}"
  sleep 10
  /sbin/reboot
else
  echo -e "${YELLOW}[INFO] Zum Neustarten ausführen:${NC} sudo reboot"
  echo ""
fi
