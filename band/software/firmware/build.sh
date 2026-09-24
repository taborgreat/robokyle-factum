#!/bin/sh
# Build the band firmware (Git Bash): sh band/software/firmware/build.sh  -> build/emg_band.uf2
#   PICO_BOARD=pico2_w sh build.sh     (default pico2_w). Delete build/ when switching boards.
set -e
export PICO_SDK_PATH="$HOME/.pico-sdk/sdk/2.2.0"
export PICO_TOOLCHAIN_PATH="$HOME/.pico-sdk/toolchain"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export PATH="$HOME/.pico-sdk/toolchain/bin:$ROOT/.venv/Scripts:$PATH"
mkdir -p "$(dirname "$0")/build" && cd "$(dirname "$0")/build"
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DPICO_BOARD="${PICO_BOARD:-pico2_w}" \
  -Dpioasm_DIR="$HOME/.pico-sdk/tools/2.2.0/pioasm" -Dpicotool_DIR="$HOME/.pico-sdk/picotool/2.2.0/picotool" .. >/dev/null
ninja "$@"
