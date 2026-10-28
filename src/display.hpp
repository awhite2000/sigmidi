#pragma once
#include <cstdint>
namespace foot {
constexpr int DisplayWidth = 280, DisplayHeight = 240, DisplayStripeRows = 16;
constexpr int MenuRows = 7, DisplayText = 41;
enum class Screen { Performance, Menu, Browser };
enum class MenuRowKind { Navigation, Parameter, Action, Message };
constexpr int MenuValueX = 164;
struct DisplayPedal {
    int value = -1, cc = 11;
    bool enabled = false;
};
struct DisplayFrame {
    Screen screen = Screen::Performance;
    int ble = 0, activeSwitch = 0, switchCount = 10;
    int displayRotation = 0;
    char title[DisplayText]{}, breadcrumb[DisplayText]{}, notice[DisplayText]{},
        footer[DisplayText]{};
    char activeLabel[8]{}, switchName[25]{}, action[DisplayText]{};
    char rows[MenuRows][DisplayText]{};
    char values[MenuRows][25]{};
    MenuRowKind rowKinds[MenuRows]{};
    int rowCount = 0, selectedRow = 0, firstRow = 0, totalRows = 0;
    bool editing = false, showWifiCredentials = false;
    char ssid[33]{}, password[17]{};
    DisplayPedal pedals[2]{};
};
struct DisplayWindow {
    uint8_t columns[4]{}, rows[4]{};
};
bool displayWindow(int firstY, int rows, DisplayWindow &, int rotation = 0);
// Convert logical RGB565 pixels to SPI byte order and the selected physical direction.
bool prepareDisplayStripe(uint16_t *pixels, int rows, int rotation);
// Pure host-testable RGB565 renderer. Only one 8.75KiB DMA stripe is needed.
void renderDisplayStripe(const DisplayFrame &, int firstY, int rows, uint16_t *pixels);
} // namespace foot
