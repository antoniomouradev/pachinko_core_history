#!/bin/bash

set -e  # Encerra se qualquer comando falhar

# Nome final do binário
OUTPUT_NAME="app_server"
OUTPUT_DIR="bin"

# Caminho do script principal
MAIN_SCRIPT="app/app.py"

# Nome base do script sem extensão
BASE_NAME=$(basename "$MAIN_SCRIPT" .py)

# Limpa compilações anteriores
rm -rf "$OUTPUT_NAME" "$OUTPUT_NAME.exe" "$BASE_NAME".build "$BASE_NAME".dist "$BASE_NAME".onefile-build

# Garante que a pasta bin exista
mkdir -p "$OUTPUT_DIR"

# Compila usando Nuitka
nuitka \
  --standalone \
  --include-package=redis \
  --follow-imports \
  --onefile \
  --static-libpython=no \
  --output-filename="$OUTPUT_NAME" \
  "$MAIN_SCRIPT"

# Move o executável final para a pasta bin
if [ -f "$OUTPUT_NAME" ] || [ -f "$OUTPUT_NAME.exe" ]; then
  mv "$OUTPUT_NAME"* "$OUTPUT_DIR/"
fi

# Remove todas as pastas temporárias do Nuitka
rm -rf "$BASE_NAME".build "$BASE_NAME".dist "$BASE_NAME".onefile-build

echo "✅ Compilação concluída. Binário gerado em $OUTPUT_DIR/$OUTPUT_NAME"