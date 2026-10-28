#include "app.hpp"
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <vector>
static cJSON *tree = nullptr;
static std::vector<int> path;
static int selected = 0, rootRow = 0;
static bool browsing = false, editing = false;
static int charIndex = 0;
static unsigned seenRevision = 0;
static cJSON *beforeEdit = nullptr;
static int actionMessage = -1, actionRow = 0;
static cJSON *newMessage() {
    auto m = cJSON_CreateObject();
    for (auto key : {"type", "channel", "number", "value", "delayMs"})
        cJSON_AddNumberToObject(m, key,
                                !strcmp(key, "channel") ? 1 : !strcmp(key, "delayMs") ? 5 : 0);
    return m;
}
static int treeNumber(const char *key) {
    auto v = cJSON_GetObjectItemCaseSensitive(tree, key);
    return cJSON_IsNumber(v) ? v->valueint : 0;
}
static bool treeMirrored() { return treeNumber("enclosureVariant") == 1; }
static int storageIndex(cJSON *parent, int index) {
    if (!parent || !parent->string)
        return index;
    bool switches = !strcmp(parent->string, "switches"), ladder = !strcmp(parent->string, "ladder");
    if (!switches && !ladder)
        return index;
    if (ladder && index == 0)
        return 0;
    int tap = foot::switchTap(treeNumber("ladderLayout"), treeNumber("switchCount"),
                              index + (switches ? 1 : 0), treeMirrored());
    return tap < 0 ? -1 : tap - (switches ? 1 : 0);
}
static void treeLabel(cJSON *parent, int index, char *out, size_t size) {
    int storage = storageIndex(parent, index);
    bool switches = parent && parent->string && !strcmp(parent->string, "switches");
    foot::switchLabel(treeNumber("ladderLayout"), treeNumber("switchCount"),
                      storage + (switches ? 1 : 0), out, size);
}
static cJSON *visibleChild(cJSON *parent, int index);
static cJSON *node() {
    cJSON *n = tree;
    for (auto i : path)
        n = visibleChild(n, i);
    return n;
}
static bool hidden(cJSON *parent, cJSON *child) {
    auto switchCount = cJSON_GetObjectItemCaseSensitive(tree, "switchCount");
    if (parent && parent->string && cJSON_IsNumber(switchCount) &&
        (!strcmp(parent->string, "switches") || !strcmp(parent->string, "ladder"))) {
        int index = 0;
        for (auto v = parent->child; v && v != child; v = v->next)
            ++index;
        int visible = switchCount->valueint + (!strcmp(parent->string, "ladder") ? 1 : 0);
        if (index >= visible)
            return true;
    }
    auto type = cJSON_GetObjectItemCaseSensitive(parent, "type");
    return cJSON_IsNumber(type) && type->valueint == 1 && child->string &&
           !strcmp(child->string, "value");
}
static cJSON *visibleChild(cJSON *parent, int index) {
    if (parent && parent->string &&
        (!strcmp(parent->string, "switches") || !strcmp(parent->string, "ladder")))
        return cJSON_GetArrayItem(parent, storageIndex(parent, index));
    for (auto child = parent ? parent->child : nullptr; child; child = child->next) {
        if (!hidden(parent, child) && index-- == 0)
            return child;
    }
    return nullptr;
}
static cJSON *item() { return visibleChild(node(), selected); }
static int count() {
    int result = 0;
    for (auto child = node()->child; child; child = child->next)
        if (!hidden(node(), child))
            result++;
    return result;
}
static void refresh() {
    cJSON_Delete(tree);
    tree = configJson(state.draft);
    path.clear();
    actionMessage = -1;
    selected = 0;
    editing = false;
    seenRevision = state.revision;
}
static bool syncDraft() {
    auto c = new foot::Config;
    char error[80];
    bool ok = configParse(tree, *c, error, sizeof error);
    if (ok) {
        state.draft = *c;
        state.revision++;
        seenRevision = state.revision;
    } else
        snprintf(state.notice, sizeof state.notice, "%s", error);
    delete c;
    return ok;
}
static void finish(bool save) {
    if (save) {
        if (!syncDraft())
            return;
        if (!saveConfig(state.draft)) {
            strcpy(state.notice, "Save failed");
            return;
        }
        state.saved = state.draft;
    } else
        state.draft = state.saved;
    state.revision++;
    state.owner.clear();
    state.setup = false;
    browsing = false;
    editing = false;
    strcpy(state.notice, save ? "Saved" : "Discarded");
}
void uiStep(int rotation, int click) {
    if (!state.setup)
        return;
    if (!tree || seenRevision != state.revision)
        refresh();
    bool owned = !state.owner.empty() && (int32_t)(state.leaseUntil - nowMs()) > 0;
    if (owned) {
        if (click == 2) {
            state.owner.clear();
            state.draft = state.saved;
            state.revision++;
            refresh();
            strcpy(state.notice, "Browser draft discarded");
        }
        return;
    }
    if (!browsing) {
        rootRow = std::clamp(rootRow + rotation, 0, 3);
        if (click == 1) {
            switch (rootRow) {
            case 0:
                browsing = true;
                path.clear();
                selected = 0;
                break;
            case 1:
                if (syncDraft()) {
                    if (state.wifi)
                        strcpy(state.notice, "WiFi already running");
                    else if (!wifiStart())
                        strcpy(state.notice, "WiFi start failed");
                }
                break;
            case 2:
                finish(true);
                break;
            case 3:
                finish(false);
                break;
            }
        }
        return;
    }
    if (actionMessage >= 0) {
        if (click == 2) {
            actionMessage = -1;
            return;
        }
        actionRow = std::clamp(actionRow + rotation, 0, 2);
        if (click != 1)
            return;
        auto list = node();
        int index = actionMessage;
        if (actionRow == 0) {
            path.push_back(index);
            selected = 0;
        } else if (actionRow == 1) {
            if (cJSON_GetArraySize(list) >= 32) {
                strcpy(state.notice, "Maximum 32 messages");
                return;
            }
            cJSON_InsertItemInArray(list, index, newMessage());
            path.push_back(index);
            selected = 0;
        } else {
            cJSON_DeleteItemFromArray(list, index);
            selected = std::min(index, cJSON_GetArraySize(list));
        }
        actionMessage = -1;
        return;
    }
    if (click == 2) {
        if (editing) {
            auto current = item();
            if (beforeEdit) {
                if (current->string)
                    cJSON_ReplaceItemInObjectCaseSensitive(node(), current->string, beforeEdit);
                else
                    cJSON_ReplaceItemInArray(node(), storageIndex(node(), selected), beforeEdit);
                beforeEdit = nullptr;
            }
            editing = false;
            return;
        }
        if (path.empty()) {
            if (syncDraft())
                browsing = false;
        } else {
            selected = path.back();
            path.pop_back();
        }
        return;
    }
    auto n = node();
    int size = count();
    bool array = cJSON_IsArray(n);
    bool sequence =
        array && n->string && (!strcmp(n->string, "press") || !strcmp(n->string, "release"));
    bool message = !path.empty() && n && cJSON_GetObjectItem(n, "delayMs");
    int extra = sequence ? 2 : (message ? 3 : 0);
    if (editing) {
        auto v = item();
        if (cJSON_IsNumber(v) && rotation) {
            double step = 1;
            if (v->string && !strcmp(v->string, "maxOhms"))
                step = 100;
            if (v->string && !strcmp(v->string, "switchCount"))
                cJSON_SetNumberValue(
                    v, std::clamp(v->valueint + rotation * (treeNumber("ladderLayout") ? 2 : 1),
                                  foot::MinSwitches, foot::MaxSwitches));
            else if (v->string && !strcmp(v->string, "ladderLayout")) {
                cJSON_SetNumberValue(v, std::clamp(v->valueint + rotation, 0, 1));
            } else if (v->string && !strcmp(v->string, "type"))
                cJSON_SetNumberValue(v, std::clamp(v->valueint + rotation, 0, 1));
            else if (v->string && !strcmp(v->string, "led"))
                cJSON_SetNumberValue(v, std::clamp(v->valueint + rotation, 0, foot::MaxSwitches));
            else if (v->string && !strcmp(v->string, "brightness"))
                cJSON_SetNumberValue(v, std::clamp(v->valueint + rotation, 0, 255));
            else if (v->string && !strcmp(v->string, "colorOrder"))
                cJSON_SetNumberValue(v, std::clamp(v->valueint + rotation, 0, 5));
            else if (v->string && !strcmp(v->string, "protocol"))
                cJSON_SetNumberValue(v, std::clamp(v->valueint + rotation, 0, 2));
            else if (v->string && !strcmp(v->string, "enclosureVariant"))
                cJSON_SetNumberValue(v, std::clamp(v->valueint + rotation, 0, 1));
            else
                cJSON_SetNumberValue(v, v->valuedouble + rotation * step);
        } else if (cJSON_IsBool(v) && rotation) {
            v->type = cJSON_IsTrue(v) ? cJSON_False : cJSON_True;
        } else if (cJSON_IsString(v)) {
            char text[25];
            snprintf(text, sizeof text, "%-24.24s", v->valuestring);
            static const char alphabet[] = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_";
            char *p = strchr((char *)alphabet, text[charIndex]);
            int idx = p ? p - alphabet : 0;
            idx = (idx + rotation % (int)(sizeof alphabet - 1) + (int)sizeof alphabet - 1) %
                  (sizeof alphabet - 1);
            text[charIndex] = alphabet[idx];
            cJSON_SetValuestring(v, text);
            if (click == 1) {
                charIndex++;
                if (charIndex >= 24) {
                    charIndex = 0;
                    editing = false;
                }
            }
            return;
        }
        if (click == 1) {
            if (v->string && !strcmp(v->string, "ladderLayout") && v->valueint == 1) {
                auto count = cJSON_GetObjectItemCaseSensitive(tree, "switchCount");
                if (count->valueint % 2)
                    cJSON_SetNumberValue(count, count->valueint + 1);
            }
            editing = false;
        }
        return;
    }
    selected = std::clamp(selected + rotation, 0, std::max(0, size + extra - 1));
    if (click != 1)
        return;
    if (selected >= size) {
        if (sequence) {
            if (selected == size + 1) {
                extern bool queueTest(int, bool);
                if (syncDraft() && path.size() >= 3) {
                    bool ok = queueTest(foot::switchTap(treeNumber("ladderLayout"),
                                                        treeNumber("switchCount"),
                                                        path[path.size() - 2] + 1, treeMirrored()) -
                                            1,
                                        !strcmp(n->string, "release"));
                    snprintf(state.notice, sizeof state.notice, "%s",
                             ok ? "Test queued" : "BLE offline or busy");
                }
                return;
            }
            if (size >= 32) {
                strcpy(state.notice, "Maximum 32 messages");
                return;
            }
            cJSON_AddItemToArray(n, newMessage());
            path.push_back(size);
            selected = 0;
            return;
        } else if (message) {
            int action = selected - size;
            int index = path.back();
            path.pop_back();
            auto parent = node();
            auto removed = cJSON_DetachItemFromArray(parent, index);
            if (action == 0) {
                cJSON_Delete(removed);
                selected = std::max(0, index - 1);
            } else {
                int dest =
                    std::clamp(index + (action == 1 ? -1 : 1), 0, cJSON_GetArraySize(parent));
                cJSON_InsertItemInArray(parent, dest, removed);
                selected = dest;
            }
        }
        return;
    }
    auto v = item();
    if (sequence) {
        actionMessage = selected;
        actionRow = 0;
        return;
    }
    if (cJSON_IsObject(v) || cJSON_IsArray(v)) {
        path.push_back(selected);
        selected = 0;
    } else {
        cJSON_Delete(beforeEdit);
        beforeEdit = cJSON_Duplicate(v, true);
        editing = true;
        charIndex = 0;
    }
}
static const char *parameterName(cJSON *parent, const char *key) {
    if (!strcmp(key, "number") && cJSON_GetObjectItemCaseSensitive(parent, "type"))
        return cJSON_GetObjectItemCaseSensitive(parent, "type")->valueint == 1 ? "PROGRAM"
                                                                               : "CONTROL";
    static const char *names[][2] = {{"switchCount", "SWITCHES"},
                                     {"ladderLayout", "LADDER"},
                                     {"debounceMs", "DEBOUNCE MS"},
                                     {"pcOffset", "PC OFFSET"},
                                     {"enclosureVariant", "ENCLOSURE"},
                                     {"windowMv", "WINDOW MV"},
                                     {"delayMs", "DELAY MS"},
                                     {"logarithmic", "LOG CURVE"},
                                     {"maxOhms", "MAX OHMS"},
                                     {"outMin", "MIN VALUE"},
                                     {"outMax", "MAX VALUE"},
                                     {"channel", "CHANNEL"},
                                     {"enabled", "ENABLED"},
                                     {"resistor", "RESISTOR"},
                                     {"invert", "INVERT"},
                                     {"type", "TYPE"},
                                     {"value", "VALUE"},
                                     {"name", "NAME"},
                                     {"version", "SCHEMA"},
                                     {"cc", "CONTROL"},
                                     {"heel", "HEEL"},
                                     {"toe", "TOE"},
                                     {"curve", "CURVE"},
                                     {"led", "LED NO."},
                                     {"leds", "LED CHAIN"},
                                     {"brightness", "BRIGHTNESS"},
                                     {"colorOrder", "RGB ORDER"},
                                     {"protocol", "PROTOCOL"}};
    for (const auto &name : names)
        if (!strcmp(key, name[0]))
            return name[1];
    return key;
}
static void label(cJSON *parent, cJSON *v, int index, char *out, size_t len,
                  char *valueOut = nullptr, size_t valueLen = 0) {
    const char *k = v->string;
    bool scalar = cJSON_IsNumber(v) || cJSON_IsBool(v) || cJSON_IsString(v);
    if (!k && !scalar) {
        auto type = cJSON_GetObjectItemCaseSensitive(v, "type");
        auto number = cJSON_GetObjectItemCaseSensitive(v, "number");
        auto channel = cJSON_GetObjectItemCaseSensitive(v, "channel");
        auto value = cJSON_GetObjectItemCaseSensitive(v, "value");
        if (type && number && channel && value) {
            if (type->valueint == 1)
                snprintf(out, len, "PC%d/%d", number->valueint, channel->valueint);
            else
                snprintf(out, len, "CC%d:%d/%d", number->valueint, value->valueint,
                         channel->valueint);
            return;
        }
        if (parent && parent->string && !strcmp(parent->string, "switches"))
            treeLabel(parent, index, out, len);
        else
            snprintf(out, len, "%d", index + 1);
        return;
    }
    char name[foot::DisplayText]{}, value[25]{};
    if (k)
        snprintf(name, sizeof name, "%s", parameterName(parent, k));
    else if (index == 0)
        strcpy(name, "IDLE MV");
    else {
        char sw[8];
        treeLabel(parent, index, sw, sizeof sw);
        snprintf(name, sizeof name, "SW %s MV", sw);
    }
    if (cJSON_IsNumber(v) && k && !strcmp(k, "ladderLayout"))
        snprintf(value, sizeof value, "%s", v->valueint ? "MODULAR" : "LINEAR");
    else if (cJSON_IsNumber(v) && k && !strcmp(k, "enclosureVariant"))
        snprintf(value, sizeof value, "%s", v->valueint ? "LEFT" : "RIGHT");
    else if (cJSON_IsNumber(v) && k && !strcmp(k, "type"))
        snprintf(value, sizeof value, "%s", v->valueint == 1 ? "PC" : "CC");
    else if (cJSON_IsNumber(v) && k && !strcmp(k, "colorOrder"))
        snprintf(value, sizeof value, "%s", foot::LedOrders[std::clamp(v->valueint, 0, 5)]);
    else if (cJSON_IsNumber(v) && k && !strcmp(k, "protocol"))
        snprintf(value, sizeof value, "%s", foot::LedProtocols[std::clamp(v->valueint, 0, 2)]);
    else if (cJSON_IsNumber(v) && k && !strcmp(k, "led") && v->valueint == 0)
        strcpy(value, "OFF");
    else if (cJSON_IsNumber(v))
        snprintf(value, sizeof value, "%.0f", v->valuedouble);
    else if (cJSON_IsBool(v))
        snprintf(value, sizeof value, "%s", cJSON_IsTrue(v) ? "ON" : "OFF");
    else if (cJSON_IsString(v))
        snprintf(value, sizeof value, "%s", v->valuestring);
    if (valueOut) {
        snprintf(out, len, "%s", name);
        snprintf(valueOut, valueLen, "%s", value);
    } else if (scalar)
        snprintf(out, len, "%s %s", name, value);
    else
        snprintf(out, len, "%s", name);
}
void uiView(foot::DisplayFrame &view) {
    view = foot::DisplayFrame{};
    view.displayRotation = state.saved.leftVariant() ? 180 : 0;
    view.ble = bleReady() ? 2 : bleConnected() ? 1 : 0;
    view.switchCount = state.saved.switchCount;
    view.activeSwitch =
        std::max(0, foot::switchNumber(state.saved.ladderLayout, state.saved.switchCount, state.key,
                                       state.saved.leftVariant()));
    foot::switchLabel(state.saved.ladderLayout, state.saved.switchCount, state.key,
                      view.activeLabel, sizeof view.activeLabel);
    snprintf(view.ssid, sizeof view.ssid, "%s", state.ssid);
    snprintf(view.password, sizeof view.password, "%s", state.password);
    snprintf(view.notice, sizeof view.notice, "%.40s", state.notice);
    for (int i = 0; i < 2; ++i) {
        view.pedals[i].value = state.pedal[i];
        view.pedals[i].enabled = state.saved.pedals[i].enabled;
        view.pedals[i].cc = state.saved.pedals[i].cc;
    }
    if (!state.setup) {
        view.screen = foot::Screen::Performance;
        if (view.activeSwitch > 0) {
            const auto &sw = state.saved.switches[state.key - 1];
            snprintf(view.switchName, sizeof view.switchName, "%s", sw.name);
            snprintf(view.action, sizeof view.action, "PRESS %d / RELEASE %d MESSAGES",
                     sw.press.count, sw.release.count);
        } else {
            snprintf(view.switchName, sizeof view.switchName, "%d SWITCHES / BLE MIDI",
                     state.saved.switchCount);
            snprintf(view.action, sizeof view.action, "PRESS A FOOTSWITCH TO PLAY");
        }
        strcpy(view.footer, "CLICK ENCODER: SETUP");
        return;
    }
    bool owned = !state.owner.empty() && (int32_t)(state.leaseUntil - nowMs()) > 0;
    if (owned) {
        view.screen = foot::Screen::Browser;
        strcpy(view.title, "WI-FI EDITOR");
        strcpy(view.footer, "HOLD: TAKE OVER (DISCARDS DRAFT)");
        return;
    }
    view.screen = foot::Screen::Menu;
    strcpy(view.title, "SETUP");
    strcpy(view.footer, "TURN: CHOOSE / CLICK: SELECT");
    if (!browsing) {
        view.showWifiCredentials = state.wifi;
        const char *menu[] = {"EDIT CONFIG", "WI-FI SETUP", "SAVE & EXIT", "DISCARD & EXIT"};
        view.rowCount = view.totalRows = 4;
        view.selectedRow = rootRow;
        strcpy(view.breadcrumb, "CONFIGURATION / CONNECTION");
        for (int i = 0; i < 4; ++i) {
            strcpy(view.rows[i], menu[i]);
            view.rowKinds[i] = i == 0 ? foot::MenuRowKind::Navigation : foot::MenuRowKind::Action;
        }
        return;
    }
    if (!tree)
        refresh();
    auto n = node();
    if (actionMessage >= 0) {
        strcpy(view.title, "MESSAGE ACTION");
        label(n, cJSON_GetArrayItem(n, actionMessage), actionMessage, view.breadcrumb,
              sizeof view.breadcrumb);
        const char *actions[] = {"EDIT", "INSERT BEFORE", "DELETE"};
        view.rowCount = view.totalRows = 3;
        view.selectedRow = actionRow;
        for (int i = 0; i < 3; ++i) {
            strcpy(view.rows[i], actions[i]);
            view.rowKinds[i] = foot::MenuRowKind::Action;
        }
        strcpy(view.footer, "CLICK: SELECT / HOLD: BACK");
        return;
    }
    auto parent = tree;
    char breadcrumb[96]{};
    for (size_t depth = 0; depth < path.size(); ++depth) {
        auto next = visibleChild(parent, path[depth]);
        char segment[28]{};
        if (next->string)
            snprintf(segment, sizeof segment, "%s", next->string);
        else if (parent->string && !strcmp(parent->string, "switches"))
            treeLabel(parent, path[depth], segment, sizeof segment);
        else
            snprintf(segment, sizeof segment, "%d", path[depth] + 1);
        size_t len = strlen(breadcrumb);
        snprintf(breadcrumb + len, sizeof breadcrumb - len, "%s%s", len ? " / " : "", segment);
        parent = next;
    }
    snprintf(view.breadcrumb, sizeof view.breadcrumb, "%.40s",
             path.empty() ? "CONTROLLER SETTINGS" : breadcrumb);
    bool sequence = cJSON_IsArray(n) && n->string &&
                    (!strcmp(n->string, "press") || !strcmp(n->string, "release"));
    bool message = cJSON_GetObjectItem(n, "delayMs");
    if (sequence)
        strcpy(view.title, !strcmp(n->string, "press") ? "ON PRESS" : "ON RELEASE");
    else if (message)
        strcpy(view.title, "MIDI MESSAGE");
    else if (n->string && !strcmp(n->string, "leds"))
        strcpy(view.title, "LED CHAIN");
    int size = count();
    view.totalRows = size + (sequence ? 2 : message ? 3 : 0);
    view.firstRow =
        std::clamp(selected - foot::MenuRows / 2, 0, std::max(0, view.totalRows - foot::MenuRows));
    view.rowCount = std::min(foot::MenuRows, view.totalRows - view.firstRow);
    view.selectedRow = selected - view.firstRow;
    view.editing = editing;
    strcpy(view.footer, editing ? "CLICK: ACCEPT / HOLD: CANCEL" : "CLICK: SELECT / HOLD: BACK");
    for (int row = 0; row < view.rowCount; ++row) {
        int index = view.firstRow + row;
        if (index < size) {
            auto child = visibleChild(n, index);
            bool parameter = !cJSON_IsObject(child) && !cJSON_IsArray(child);
            view.rowKinds[row] =
                parameter ? foot::MenuRowKind::Parameter
                          : sequence ? foot::MenuRowKind::Message : foot::MenuRowKind::Navigation;
            label(n, child, index, view.rows[row], sizeof view.rows[row],
                  parameter ? view.values[row] : nullptr, sizeof view.values[row]);
        } else {
            view.rowKinds[row] = foot::MenuRowKind::Action;
            if (sequence)
                strcpy(view.rows[row], index == size ? "APPEND MSG" : "TEST SEQ");
            else
                strcpy(view.rows[row],
                       index == size ? "DELETE" : index == size + 1 ? "MOVE UP" : "MOVE DOWN");
        }
    }
}
void uiRender(char lines[10][24]) {
    // Legacy text adapter: tests exercise the same view used by the color renderer.
    foot::DisplayFrame view{};
    uiView(view);
    snprintf(lines[0], 24, "%.23s", view.title);
    for (int i = 0; i < view.rowCount; ++i) {
        char prefix = i == view.selectedRow ? (view.editing ? '*' : '>') : ' ';
        if (view.rowKinds[i] == foot::MenuRowKind::Parameter)
            snprintf(lines[i + 1], 24, "%c%.11s %.9s", prefix, view.rows[i], view.values[i]);
        else
            snprintf(lines[i + 1], 24, "%c%.22s", prefix, view.rows[i]);
    }
}
