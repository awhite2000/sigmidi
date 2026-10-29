#include "config.hpp"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <climits>
namespace {
void num(cJSON *j, const char *k, double v) { cJSON_AddNumberToObject(j, k, v); }
void boolean(cJSON *j, const char *k, bool v) { cJSON_AddBoolToObject(j, k, v); }
bool integer(const cJSON *j, const char *k, int &v) {
    auto x = cJSON_GetObjectItemCaseSensitive(j, k);
    if (!cJSON_IsNumber(x) || !std::isfinite(x->valuedouble) ||
        x->valuedouble != std::floor(x->valuedouble) || x->valuedouble < INT_MIN ||
        x->valuedouble > INT_MAX)
        return false;
    v = x->valueint;
    return true;
}
bool real(const cJSON *j, const char *k, float &v) {
    auto x = cJSON_GetObjectItemCaseSensitive(j, k);
    if (!cJSON_IsNumber(x) || !std::isfinite(x->valuedouble))
        return false;
    v = x->valuedouble;
    return true;
}
bool flag(const cJSON *j, const char *k, bool &v) {
    auto x = cJSON_GetObjectItemCaseSensitive(j, k);
    if (!cJSON_IsBool(x))
        return false;
    v = cJSON_IsTrue(x);
    return true;
}
cJSON *sequence(const foot::Sequence &s) {
    auto a = cJSON_CreateArray();
    for (int i = 0; i < s.count; i++) {
        auto j = cJSON_CreateObject();
        auto m = s.messages[i];
        num(j, "type", m.type);
        num(j, "pcMode", m.pcMode);
        num(j, "channel", m.channel);
        num(j, "number", m.number);
        num(j, "value", m.value);
        num(j, "delayMs", m.delayMs);
        num(j, "counterId", m.counterId);
        cJSON_AddItemToArray(a, j);
    }
    return a;
}
bool sequenceRead(const cJSON *a, foot::Sequence &s) {
    if (!cJSON_IsArray(a) || cJSON_GetArraySize(a) > 32)
        return false;
    s.count = cJSON_GetArraySize(a);
    for (int i = 0; i < s.count; i++) {
        auto j = cJSON_GetArrayItem(a, i);
        auto &m = s.messages[i];
        m = foot::Message{};
        if (!integer(j, "type", m.type) || !integer(j, "channel", m.channel) ||
            !integer(j, "number", m.number) || !integer(j, "value", m.value) ||
            !integer(j, "delayMs", m.delayMs))
            return false;
        for (auto field : {"pcMode", "counterId"}) {
            int &value = !strcmp(field, "pcMode") ? m.pcMode : m.counterId;
            if (cJSON_GetObjectItemCaseSensitive(j, field) && !integer(j, field, value))
                return false;
        }
    }
    return true;
}
} // namespace
cJSON *configJson(const foot::Config &c) {
    auto j = cJSON_CreateObject();
    num(j, "version", c.version);
    num(j, "switchCount", c.switchCount);
    num(j, "debounceMs", c.debounceMs);
    num(j, "pcOffset", c.pcOffset);
    num(j, "windowMv", c.windowMv);
    auto ladder = cJSON_AddArrayToObject(j, "ladder");
    for (auto v : c.ladder)
        cJSON_AddItemToArray(ladder, cJSON_CreateNumber(v));
    auto switches = cJSON_AddArrayToObject(j, "switches");
    for (auto &s : c.switches) {
        auto o = cJSON_CreateObject();
        cJSON_AddStringToObject(o, "name", s.name);
        cJSON_AddItemToObject(o, "press", sequence(s.press));
        cJSON_AddItemToObject(o, "release", sequence(s.release));
        num(o, "led", s.led);
        boolean(o, "toggle", s.toggle);
        cJSON_AddItemToArray(switches, o);
    }
    auto pedals = cJSON_AddArrayToObject(j, "pedals");
    for (auto &p : c.pedals) {
        auto o = cJSON_CreateObject();
        boolean(o, "enabled", p.enabled);
        boolean(o, "resistor", p.resistor);
        boolean(o, "invert", p.invert);
        boolean(o, "logarithmic", p.logarithmic);
        num(o, "channel", p.channel);
        num(o, "cc", p.cc);
        num(o, "outMin", p.outMin);
        num(o, "outMax", p.outMax);
        num(o, "maxOhms", p.maxOhms);
        num(o, "heel", p.heel);
        num(o, "toe", p.toe);
        num(o, "curve", p.curve);
        cJSON_AddItemToArray(pedals, o);
    }
    auto leds = cJSON_AddObjectToObject(j, "leds");
    boolean(leds, "enabled", c.leds.enabled);
    num(leds, "brightness", c.leds.brightness);
    num(leds, "colorOrder", c.leds.colorOrder);
    num(leds, "protocol", c.leds.protocol);
    num(j, "ladderLayout", c.ladderLayout);
    num(j, "enclosureVariant", c.enclosureVariant);
    num(j, "nextCounterId", c.nextCounterId);
    return j;
}
bool configParse(const cJSON *j, foot::Config &c, char *e, size_t n) {
    auto bad = [&]() {
        snprintf(e, n, "Missing or incorrectly typed configuration field");
        return false;
    };
    if (!cJSON_IsObject(j) || !integer(j, "version", c.version) ||
        !integer(j, "debounceMs", c.debounceMs) || !integer(j, "pcOffset", c.pcOffset) ||
        !real(j, "windowMv", c.windowMv))
        return bad();
    int sourceVersion = c.version;
    // Version 1 had no switch count; versions 1/2 had no LED configuration.
    if (c.version == 1) {
        if (cJSON_GetObjectItemCaseSensitive(j, "switchCount"))
            return bad();
        c.switchCount = foot::MaxSwitches;
    } else if ((c.version != 2 && c.version != 3 && c.version != 4 && c.version != 5 && c.version != 6) ||
               !integer(j, "switchCount", c.switchCount)) {
        return bad();
    }
    // Old wiring must retain its original tap numbering; no silent remapping.
    c.ladderLayout = 0;
    if (sourceVersion >= 4 && !integer(j, "ladderLayout", c.ladderLayout))
        return bad();
    c.version = 6;
    c.nextCounterId = 1;
    if (cJSON_GetObjectItemCaseSensitive(j, "nextCounterId") &&
        !integer(j, "nextCounterId", c.nextCounterId))
        return bad();
    // One selector controls both screen direction and switch presentation.
    c.enclosureVariant = 0;
    if (cJSON_GetObjectItemCaseSensitive(j, "enclosureVariant")) {
        if (!integer(j, "enclosureVariant", c.enclosureVariant))
            return bad();
    } else if (cJSON_GetObjectItemCaseSensitive(j, "displayRotation")) {
        int rotation = 0;
        if (!integer(j, "displayRotation", rotation) || (rotation != 0 && rotation != 180))
            return bad();
        c.enclosureVariant = rotation == 180 ? 1 : 0;
    }
    c.leds = foot::LedConfig{};
    if (sourceVersion >= 3) {
        auto leds = cJSON_GetObjectItemCaseSensitive(j, "leds");
        if (!cJSON_IsObject(leds) || !flag(leds, "enabled", c.leds.enabled) ||
            !integer(leds, "brightness", c.leds.brightness) ||
            !integer(leds, "colorOrder", c.leds.colorOrder) ||
            !integer(leds, "protocol", c.leds.protocol))
            return bad();
    }
    auto a = cJSON_GetObjectItemCaseSensitive(j, "ladder");
    if (!cJSON_IsArray(a) || cJSON_GetArraySize(a) != foot::MaxSwitches + 1)
        return bad();
    for (int i = 0; i <= foot::MaxSwitches; i++) {
        auto v = cJSON_GetArrayItem(a, i);
        if (!cJSON_IsNumber(v) || !std::isfinite(v->valuedouble))
            return bad();
        c.ladder[i] = v->valuedouble;
    }
    a = cJSON_GetObjectItemCaseSensitive(j, "switches");
    if (!cJSON_IsArray(a) || cJSON_GetArraySize(a) != foot::MaxSwitches)
        return bad();
    for (int i = 0; i < foot::MaxSwitches; i++) {
        auto o = cJSON_GetArrayItem(a, i);
        auto name = cJSON_GetObjectItemCaseSensitive(o, "name");
        if (!cJSON_IsString(name) || strlen(name->valuestring) > 24)
            return bad();
        strcpy(c.switches[i].name, name->valuestring);
        c.switches[i].toggle = false;
        if ((sourceVersion >= 6 || cJSON_GetObjectItemCaseSensitive(o, "toggle")) &&
            !flag(o, "toggle", c.switches[i].toggle))
            return bad();
        c.switches[i].led = i + 1;
        if (sourceVersion >= 3 && !integer(o, "led", c.switches[i].led))
            return bad();
        if (!sequenceRead(cJSON_GetObjectItemCaseSensitive(o, "press"), c.switches[i].press) ||
            !sequenceRead(cJSON_GetObjectItemCaseSensitive(o, "release"), c.switches[i].release))
            return bad();
    }
    a = cJSON_GetObjectItemCaseSensitive(j, "pedals");
    if (!cJSON_IsArray(a) || cJSON_GetArraySize(a) != 2)
        return bad();
    for (int i = 0; i < 2; i++) {
        auto o = cJSON_GetArrayItem(a, i);
        auto &p = c.pedals[i];
        if (!flag(o, "enabled", p.enabled) || !flag(o, "resistor", p.resistor) ||
            !flag(o, "invert", p.invert) || !flag(o, "logarithmic", p.logarithmic) ||
            !integer(o, "channel", p.channel) || !integer(o, "cc", p.cc) ||
            !integer(o, "outMin", p.outMin) || !integer(o, "outMax", p.outMax) ||
            !real(o, "maxOhms", p.maxOhms) || !real(o, "heel", p.heel) || !real(o, "toe", p.toe) ||
            !real(o, "curve", p.curve))
            return bad();
    }
    if (!foot::assignCounterIds(c))
        return bad();
    return foot::validate(c, e, n);
}
