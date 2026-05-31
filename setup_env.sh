#!/bin/bash
set -e

echo "Creando entorno virtual: .venv"
python3 -m venv .venv
source .venv/bin/activate

echo "Instalando dependencias de requirements.txt"
pip install --upgrade pip
pip install -r requirements.txt

echo "Compilando e instalando todo el sistema (setup.py / CMake)"
pip install .

echo ""
echo "¡Listo! Para usar el sistema, activa tu entorno:"
echo "source .venv/bin/activate"
