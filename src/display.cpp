#include "display.hpp"
#include "branding.hpp"
#include "logo.hpp"
#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstring>
namespace foot {
namespace {
constexpr uint16_t Background = 0x0863, Panel = 0x10e6, Border = 0x2a6b, Text = 0xef7d,
                   Muted = 0x94f3, Accent = 0xb74e, Selected = 0x1b6c, Blue = 0x4e9f,
                   Amber = 0xfd67, Action = 0xb57f;
// Original 5x7 bitmap alphabet, each row encoded in its low five bits.
const uint8_t *glyph(char c) {
    static const uint8_t letters[][7] = {
        {14, 17, 17, 31, 17, 17, 17}, {30, 17, 17, 30, 17, 17, 30}, {14, 17, 16, 16, 16, 17, 14},
        {30, 17, 17, 17, 17, 17, 30}, {31, 16, 16, 30, 16, 16, 31}, {31, 16, 16, 30, 16, 16, 16},
        {14, 17, 16, 23, 17, 17, 15}, {17, 17, 17, 31, 17, 17, 17}, {14, 4, 4, 4, 4, 4, 14},
        {7, 2, 2, 2, 2, 18, 12},      {17, 18, 20, 24, 20, 18, 17}, {16, 16, 16, 16, 16, 16, 31},
        {17, 27, 21, 21, 17, 17, 17}, {17, 25, 21, 19, 17, 17, 17}, {14, 17, 17, 17, 17, 17, 14},
        {30, 17, 17, 30, 16, 16, 16}, {14, 17, 17, 17, 21, 18, 13}, {30, 17, 17, 30, 20, 18, 17},
        {15, 16, 16, 14, 1, 1, 30},   {31, 4, 4, 4, 4, 4, 4},       {17, 17, 17, 17, 17, 17, 14},
        {17, 17, 17, 17, 17, 10, 4},  {17, 17, 17, 21, 21, 21, 10}, {17, 17, 10, 4, 10, 17, 17},
        {17, 17, 10, 4, 4, 4, 4},     {31, 1, 2, 4, 8, 16, 31}};
    static const uint8_t digits[][7] = {{14, 17, 19, 21, 25, 17, 14}, {4, 12, 4, 4, 4, 4, 14},
                                        {14, 17, 1, 2, 4, 8, 31},     {30, 1, 1, 14, 1, 1, 30},
                                        {2, 6, 10, 18, 31, 2, 2},     {31, 16, 16, 30, 1, 1, 30},
                                        {6, 8, 16, 30, 17, 17, 14},   {31, 1, 2, 4, 8, 8, 8},
                                        {14, 17, 17, 14, 17, 17, 14}, {14, 17, 17, 15, 1, 2, 12}};
    static const uint8_t blank[7] = {}, dash[7] = {0, 0, 0, 31, 0, 0, 0},
                         dot[7] = {0, 0, 0, 0, 0, 12, 12}, colon[7] = {0, 12, 12, 0, 12, 12, 0},
                         slash[7] = {1, 2, 2, 4, 8, 8, 16}, greater[7] = {16, 8, 4, 2, 4, 8, 16},
                         star[7] = {0, 21, 14, 31, 14, 21, 0}, plus[7] = {0, 4, 4, 31, 4, 4, 0},
                         equal[7] = {0, 0, 31, 0, 31, 0, 0}, left[7] = {2, 4, 8, 8, 8, 4, 2},
                         right[7] = {8, 4, 2, 2, 2, 4, 8}, underscore[7] = {0, 0, 0, 0, 0, 0, 31},
                         percent[7] = {17, 2, 4, 4, 8, 16, 17},
                         ampersand[7] = {12, 18, 20, 8, 21, 18, 13};
    c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    if (c >= 'A' && c <= 'Z')
        return letters[c - 'A'];
    if (c >= '0' && c <= '9')
        return digits[c - '0'];
    switch (c) {
    case '-':
        return dash;
    case '.':
        return dot;
    case ':':
        return colon;
    case '/':
        return slash;
    case '>':
        return greater;
    case '*':
        return star;
    case '+':
        return plus;
    case '=':
        return equal;
    case '(':
        return left;
    case ')':
        return right;
    case '_':
        return underscore;
    case '%':
        return percent;
    case '&':
        return ampersand;
    default:
        return blank;
    }
}
struct Canvas {
    int y0, height;
    uint16_t *pixels;
    void pixel(int x, int y, uint16_t color) {
        if (x >= 0 && x < DisplayWidth && y >= y0 && y < y0 + height)
            pixels[(y - y0) * DisplayWidth + x] = color;
    }
    void rect(int x, int y, int w, int h, uint16_t color) {
        int x0 = std::max(x, 0), x1 = std::min(x + w, DisplayWidth);
        for (int yy = std::max(y, y0); yy < std::min(y + h, y0 + height); ++yy)
            for (int xx = x0; xx < x1; ++xx)
                pixel(xx, yy, color);
    }
    void round(int x, int y, int w, int h, int r, uint16_t color) {
        for (int yy = std::max(y, y0); yy < std::min(y + h, y0 + height); ++yy)
            for (int xx = std::max(x, 0); xx < std::min(x + w, DisplayWidth); ++xx) {
                int dx = xx < x + r ? x + r - xx : xx >= x + w - r ? xx - (x + w - r - 1) : 0;
                int dy = yy < y + r ? y + r - yy : yy >= y + h - r ? yy - (y + h - r - 1) : 0;
                if (dx * dx + dy * dy <= r * r)
                    pixel(xx, yy, color);
            }
    }
    void text(int x, int y, const char *s, int scale, uint16_t color, int maxChars = 40) {
        if (y + 7 * scale <= y0 || y >= y0 + height)
            return;
        for (int i = 0; s[i] && i < maxChars; ++i) {
            const auto g = glyph(s[i]);
            for (int gy = 0; gy < 7; ++gy)
                for (int gx = 0; gx < 5; ++gx)
                    if (g[gy] & (1 << (4 - gx)))
                        rect(x + i * 6 * scale + gx * scale, y + gy * scale, scale, scale, color);
        }
    }
    void fit(int x, int y, const char *s, uint16_t color, int width = 232) {
        int scale = static_cast<int>(std::strlen(s)) * 12 <= width ? 2 : 1;
        text(x, y + (scale == 1 ? 4 : 0), s, scale, color, width / (6 * scale));
    }
};
void credentials(Canvas &c, const DisplayFrame &v, int y) {
    c.round(16, y, 248, 72, 6, Panel);
    c.text(23, y + 7, "SSID", 1, Muted);
    c.text(60, y + 5, v.ssid, 2, Text, 17);
    c.text(23, y + 31, "KEY", 1, Muted);
    c.text(60, y + 29, v.password, 2, Accent, 16);
    c.text(23, y + 55, "HTTP", 1, Muted);
    c.text(60, y + 53, "192.168.4.1", 2, Text, 16);
}
} // namespace
bool displayWindow(int firstY, int rows, DisplayWindow &window, int rotation) {
    if (firstY < 0 || firstY >= DisplayHeight || rows <= 0 || rows > DisplayHeight - firstY ||
        (rotation != 0 && rotation != 180))
        return false;
    if (rotation == 180)
        firstY = DisplayHeight - firstY - rows;
    int x0 = 20, x1 = 20 + DisplayWidth - 1, y1 = firstY + rows - 1;
    window = {{uint8_t(x0 >> 8), uint8_t(x0), uint8_t(x1 >> 8), uint8_t(x1)},
              {uint8_t(firstY >> 8), uint8_t(firstY), uint8_t(y1 >> 8), uint8_t(y1)}};
    return true;
}
bool prepareDisplayStripe(uint16_t *pixels, int rows, int rotation) {
    if (!pixels || rows <= 0 || rows > DisplayStripeRows || (rotation != 0 && rotation != 180))
        return false;
    const int count = DisplayWidth * rows;
    // Reverse both axes within this stripe; displayWindow places it at the opposite end.
    if (rotation == 180)
        std::reverse(pixels, pixels + count);
    for (int i = 0; i < count; ++i)
        pixels[i] = (pixels[i] >> 8) | (pixels[i] << 8);
    return true;
}
void renderDisplayStripe(const DisplayFrame &v, int firstY, int rows, uint16_t *pixels) {
    if (!pixels || firstY < 0 || firstY >= DisplayHeight || rows <= 0 ||
        rows > DisplayHeight - firstY)
        return;
    Canvas c{firstY, rows, pixels};
    c.rect(0, 0, DisplayWidth, DisplayHeight, Background);
    if (v.screen == Screen::Performance) {
        for (int y = 0; y < LogoHeight; ++y)
            for (int x = 0; x < LogoWidth; ++x) {
                int alpha = LogoAlpha[y * LogoWidth + x];
                if (!alpha) continue;
                int r = (((Text >> 11) & 31) * alpha + ((Background >> 11) & 31) * (255 - alpha) + 127) / 255;
                int g = (((Text >> 5) & 63) * alpha + ((Background >> 5) & 63) * (255 - alpha) + 127) / 255;
                int b = ((Text & 31) * alpha + (Background & 31) * (255 - alpha) + 127) / 255;
                c.pixel(16 + x, 6 + y, uint16_t((r << 11) | (g << 5) | b));
            }
    }
    c.text(v.screen == Screen::Performance ? 48 : 16, 12,
           v.screen == Screen::Performance ? BrandName : v.title, 2, Text, 14);
    if (v.screen == Screen::Performance)
        c.text(16, 28, FirmwareLabel, 1, Muted, 24);
    const char *ble = v.ble == 2 ? "MIDI READY" : v.ble == 1 ? "CONNECTED" : "OFFLINE";
    c.round(190, 10, 74, 19, 5, v.ble == 2 ? Selected : Panel);
    c.text(197, 16, ble, 1, v.ble == 2 ? Accent : Muted, 10);
    c.rect(16, 36, 248, 1, Border);
    if (v.screen == Screen::Performance) {
        c.round(16, 48, 248, 83, 8, Panel);
        c.rect(16, 60, 3, 57, v.activeSwitch > 0 ? Accent : Border);
        char number[16];
        if (v.activeSwitch > 0) {
            if (v.activeLabel[0])
                snprintf(number, sizeof number, "SW %s", v.activeLabel);
            else
                snprintf(number, sizeof number, "SW %02d", v.activeSwitch);
        } else
            snprintf(number, sizeof number, "READY");
        c.text(29, 57, number, 4, v.activeSwitch > 0 ? Accent : Text, 8);
        c.fit(29, 94, v.switchName, Text, 223);
        c.text(29, 116, v.action, 1, Muted, 36);
        for (int i = 0; i < 2; ++i) {
            int x = 16 + i * 128;
            const auto &p = v.pedals[i];
            c.round(x, 143, 120, 63, 6, Panel);
            char label[20], value[8];
            snprintf(label, sizeof label, "PEDAL %d / CC%d", i + 1, p.cc);
            c.text(x + 8, 151, label, 1, Muted, 18);
            if (!p.enabled)
                snprintf(value, sizeof value, "OFF");
            else if (p.value < 0)
                snprintf(value, sizeof value, "---");
            else
                snprintf(value, sizeof value, "%03d", std::clamp(p.value, 0, 127));
            c.text(x + 8, 164, value, 3, p.enabled ? (i ? Blue : Accent) : Muted, 4);
            c.round(x + 8, 192, 104, 5, 2, Border);
            if (p.enabled && p.value >= 0)
                c.round(x + 8, 192, std::max(2, 104 * std::clamp(p.value, 0, 127) / 127), 5, 2,
                        i ? Blue : Accent);
        }
        c.text(17, 214, v.notice, 1, Muted, 40);
    } else if (v.screen == Screen::Browser) {
        c.round(16, 54, 248, 80, 7, Panel);
        c.text(28, 68, "BROWSER EDITING", 2, Accent, 19);
        c.text(28, 95, "Changes are saved in the browser.", 1, Text, 36);
        c.text(28, 113, "Hold encoder to take over.", 1, Muted, 36);
        credentials(c, v, 145);
    } else {
        c.text(17, 44, v.breadcrumb, 1, Muted, 40);
        int rowHeight = v.showWifiCredentials ? 20 : 22;
        for (int i = 0; i < std::min(v.rowCount, MenuRows); ++i) {
            int y = 60 + i * rowHeight;
            bool selected = i == v.selectedRow;
            if (selected) {
                c.round(16, y - 3, 248, rowHeight - 1, 5, Selected);
                c.rect(16, y + 1, 3, rowHeight - 9, v.editing ? Amber : Accent);
            }
            auto kind = v.rowKinds[i];
            uint16_t color = kind == MenuRowKind::Action ? Action : selected ? Text : Muted;
            if (kind == MenuRowKind::Message) {
                if (!strncmp(v.rows[i], "PC", 2))
                    color = Blue;
                if (!strncmp(v.rows[i], "CC", 2))
                    color = Amber;
            }
            if (kind == MenuRowKind::Parameter) {
                c.fit(26, y, v.rows[i], color, MenuValueX - 32);
                const char *value = v.values[i];
                size_t length = std::strlen(value);
                uint16_t valueColor = selected && v.editing ? Amber : Text;
                // All scalar values share one column. Long names wrap inside that column.
                int scale = length <= 7 ? 2 : 1;
                c.text(MenuValueX, y + (scale == 1 && length <= 14 ? 4 : 0), value, scale,
                       valueColor, scale == 2 ? 7 : 14);
                if (length > 14)
                    c.text(MenuValueX, y + 11, value + 14, 1, valueColor, 14);
            } else
                c.fit(26, y, v.rows[i], color, 222);
            if (selected)
                c.text(253, y + 3, v.editing ? "*" : ">", 1, v.editing ? Amber : Accent, 1);
        }
        if (v.totalRows > MenuRows) {
            int y = 59 + 145 * v.firstRow / v.totalRows;
            int h = std::max(6, 145 * MenuRows / v.totalRows);
            c.rect(270, 59, 2, 147, Panel);
            c.rect(270, y, 2, h, Accent);
        }
        if (v.showWifiCredentials)
            credentials(c, v, 145);
        else
            c.text(17, 215, v.notice, 1, Muted, 40);
    }
    c.rect(16, 227, 248, 1, Border);
    c.text(40, 230, v.footer, 1, Accent, 33);
}
} // namespace foot
