#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
TEST_BIN=$(mktemp /tmp/midi-foot-test.XXXXXX)
trap 'rm -f "$TEST_BIN"' EXIT
c++ -std=c++17 -Wall -Wextra -Werror -Isrc src/core.cpp tests/core_test.cpp -o "$TEST_BIN"
"$TEST_BIN"
COUNTER_BIN=$(mktemp /tmp/midi-foot-counter.XXXXXX)
trap 'rm -f "$TEST_BIN" "$COUNTER_BIN"' EXIT
c++ -std=c++17 -Wall -Wextra -Werror -Isrc src/core.cpp src/counters.cpp tests/counter_test.cpp -o "$COUNTER_BIN"
"$COUNTER_BIN"
rm -f "$COUNTER_BIN"
DISPLAY_BIN=$(mktemp /tmp/midi-foot-display.XXXXXX)
trap 'rm -f "$TEST_BIN" "$DISPLAY_BIN"' EXIT
c++ -std=c++17 -Wall -Wextra -Werror -Isrc src/display.cpp tests/display_test.cpp -o "$DISPLAY_BIN"
"$DISPLAY_BIN"
LED_BIN=$(mktemp /tmp/midi-foot-led.XXXXXX)
trap 'rm -f "$TEST_BIN" "$DISPLAY_BIN" "$LED_BIN"' EXIT
c++ -std=c++17 -Wall -Wextra -Werror -Isrc src/core.cpp src/leds.cpp tests/led_test.cpp -o "$LED_BIN"
"$LED_BIN"
JSON_DIR="${IDF_PATH:-${PLATFORMIO_CORE_DIR:-/tmp/midi-foot-toolchain}/packages/framework-espidf}/components/json/cJSON"
if [ -f "$JSON_DIR/cJSON.c" ]; then
    JSON_OBJ=$(mktemp /tmp/midi-foot-json.XXXXXX)
    CONFIG_BIN=$(mktemp /tmp/midi-foot-config.XXXXXX)
    trap 'rm -f "$TEST_BIN" "$DISPLAY_BIN" "$LED_BIN" "$JSON_OBJ" "$CONFIG_BIN"' EXIT
    cc -x c -c "$JSON_DIR/cJSON.c" -o "$JSON_OBJ"
    c++ -std=c++17 -Wall -Wextra -Werror -Isrc -I"$JSON_DIR" src/core.cpp src/config.cpp tests/config_test.cpp "$JSON_OBJ" -o "$CONFIG_BIN"
    "$CONFIG_BIN"
    UI_BIN=$(mktemp /tmp/midi-foot-ui.XXXXXX)
    trap 'rm -f "$TEST_BIN" "$DISPLAY_BIN" "$LED_BIN" "$JSON_OBJ" "$CONFIG_BIN" "$UI_BIN"' EXIT
    c++ -std=c++17 -Wall -Wextra -Werror -Isrc -Itests/stubs -I"$JSON_DIR" src/core.cpp src/config.cpp src/ui.cpp tests/ui_test.cpp "$JSON_OBJ" -o "$UI_BIN"
    "$UI_BIN"
    c++ -std=c++17 -Wall -Wextra -Werror -Isrc -Itests/stubs -I"$JSON_DIR" src/core.cpp src/config.cpp src/ui.cpp tests/modular_test.cpp "$JSON_OBJ" -o "$UI_BIN"
    "$UI_BIN"
    c++ -std=c++17 -Wall -Wextra -Werror -Isrc -Itests/stubs -I"$JSON_DIR" src/core.cpp src/config.cpp src/ui.cpp tests/mirrored_test.cpp "$JSON_OBJ" -o "$UI_BIN"
    "$UI_BIN"
else
    echo 'Config roundtrip tests skipped: set IDF_PATH or PLATFORMIO_CORE_DIR to an installed ESP-IDF.'
fi
if [ -n "${NODE:-}" ]; then
    JS_FILE=$(mktemp /tmp/midi-foot-editor.XXXXXX.js)
    python3 - "$JS_FILE" <<'PY'
from pathlib import Path
import sys
Path(sys.argv[1]).write_text(Path('web/index.html').read_text().split('<script>')[1].split('</script>')[0])
PY
    "$NODE" --check "$JS_FILE"
    "$NODE" tests/editor_test.js
    rm -f "$JS_FILE"
fi

python3 tests/flasher_test.py
if [ -n "${NODE:-}" ] && [ -f distribution/web-flasher/release.json ]; then
    "$NODE" --check flasher/app.js
    "$NODE" --check flasher/release.js
    "$NODE" tests/flasher_test.mjs
else
    echo "Web-flasher integration tests: build the firmware and set NODE to enable."
fi
