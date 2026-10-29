#include "config.hpp"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
int main() {
    auto c = foot::defaults();
    assert(c.leftVariant() && foot::Config{}.leftVariant());
    c.enclosureVariant = 1;
    c.switches[3].press.count = 1;
    c.switches[3].press.messages[0] = {1, 16, 127, 0, 50};
    c.pedals[1].enabled = true;
    c.pedals[1].resistor = false;
    c.pedals[1].logarithmic = true;
    c.leds = {true, 96, 4, 2};
    c.switches[3].led = 7;
    auto j = configJson(c);
    assert(j);
    char *text = cJSON_PrintUnformatted(j);
    assert(text);
    auto roundtrip = cJSON_Parse(text);
    auto parsed = foot::defaults();
    char error[100];
    assert(configParse(roundtrip, parsed, error, sizeof error));
    assert(parsed.enclosureVariant == 1 && parsed.switches[3].press.messages[0].number == 127 &&
           parsed.switches[3].press.messages[0].channel == 16 && parsed.pedals[1].enabled &&
           parsed.pedals[1].logarithmic && parsed.leds.enabled && parsed.leds.brightness == 96 &&
           parsed.leds.colorOrder == 4 && parsed.leds.protocol == 2 && parsed.switches[3].led == 7);
    cJSON_Delete(roundtrip);
    free(text);
    cJSON_SetNumberValue(cJSON_GetObjectItem(j, "debounceMs"), 2.5);
    assert(!configParse(j, parsed, error, sizeof error));
    cJSON_SetNumberValue(cJSON_GetObjectItem(j, "debounceMs"), 10);
    cJSON_DeleteItemFromObject(j, "pedals");
    assert(!configParse(j, parsed, error, sizeof error));
    cJSON_Delete(j);
    // Old NVS/backups default to 0 even when the destination previously used 180.
    for (int version : {1, 2, 3, 4}) {
        j = configJson(c);
        cJSON_SetNumberValue(cJSON_GetObjectItem(j, "version"), version);
        if (version == 1)
            cJSON_DeleteItemFromObject(j, "switchCount");
        cJSON_DeleteItemFromObject(j, "enclosureVariant");
        parsed.enclosureVariant = 1;
        assert(configParse(j, parsed, error, sizeof error));
        assert(parsed.enclosureVariant == 0 && parsed.switches[3].press.messages[0].number == 127);
        cJSON_Delete(j);
    }
    for (double rotation : {-1.0, 2.0, 90.0, 180.5, 180.0}) {
        j = configJson(c);
        cJSON_SetNumberValue(cJSON_GetObjectItem(j, "enclosureVariant"), rotation);
        assert(!configParse(j, parsed, error, sizeof error));
        cJSON_Delete(j);
    }
    for (auto value : {"\"180\"", "true", "null", "{}", "[]"}) {
        j = configJson(c);
        cJSON_ReplaceItemInObjectCaseSensitive(j, "enclosureVariant", cJSON_Parse(value));
        assert(!configParse(j, parsed, error, sizeof error));
        cJSON_Delete(j);
    }
    // Existing standalone rotation settings become the matching unified variant.
    for (int version : {1, 2, 3, 4}) {
        for (int rotation : {0, 180}) {
            j = configJson(c);
            cJSON_SetNumberValue(cJSON_GetObjectItem(j, "version"), version);
            if (version == 1)
                cJSON_DeleteItemFromObject(j, "switchCount");
            cJSON_DeleteItemFromObject(j, "enclosureVariant");
            cJSON_AddNumberToObject(j, "displayRotation", rotation);
            assert(configParse(j, parsed, error, sizeof error));
            assert(parsed.enclosureVariant == (rotation == 180 ? 1 : 0));
            assert(parsed.switches[3].press.messages[0].number == 127);
            auto exported = configJson(parsed);
            assert(!cJSON_GetObjectItem(exported, "displayRotation"));
            assert(!cJSON_GetObjectItem(exported, "mirroredLayout"));
            assert(cJSON_GetObjectItem(exported, "enclosureVariant")->valueint ==
                   parsed.enclosureVariant);
            cJSON_Delete(exported);
            cJSON_Delete(j);
        }
    }
    for (auto value : {"90", "-180", "180.5", "\"180\"", "true", "null"}) {
        j = configJson(c);
        cJSON_DeleteItemFromObject(j, "enclosureVariant");
        cJSON_AddItemToObject(j, "displayRotation", cJSON_Parse(value));
        assert(!configParse(j, parsed, error, sizeof error));
        cJSON_Delete(j);
    }
    // The explicit new selector takes precedence over a stale legacy rotation field.
    j = configJson(c);
    cJSON_AddNumberToObject(j, "displayRotation", 0);
    assert(configParse(j, parsed, error, sizeof error) && parsed.enclosureVariant == 1);
    cJSON_Delete(j);
    // All variants keep the full capacity in JSON, including hidden mappings.
    for (int count = foot::MinSwitches; count <= foot::MaxSwitches; ++count) {
        c = foot::defaults();
        c.switchCount = count;
        c.ladderLayout = 0;
        c.switches[9].release.count = 1;
        c.switches[9].release.messages[0] = {1, 16, 103, 0, 5};
        c.ladder[10] = 1321;
        j = configJson(c);
        assert(cJSON_GetArraySize(cJSON_GetObjectItem(j, "switches")) == 10);
        assert(cJSON_GetArraySize(cJSON_GetObjectItem(j, "ladder")) == 11);
        assert(configParse(j, parsed, error, sizeof error));
        assert(parsed.version == 5 && parsed.switchCount == count);
        assert(parsed.switches[9].release.messages[0].number == 103);
        assert(parsed.ladder[10] == 1321);
        auto field = cJSON_GetObjectItem(j, "switchCount");
        for (double bad : {3.0, 11.0, 6.5}) {
            cJSON_SetNumberValue(field, bad);
            assert(!configParse(j, parsed, error, sizeof error));
        }
        cJSON_ReplaceItemInObjectCaseSensitive(j, "switchCount", cJSON_CreateString("6"));
        assert(!configParse(j, parsed, error, sizeof error));
        cJSON_DeleteItemFromObject(j, "switchCount");
        assert(!configParse(j, parsed, error, sizeof error)); // mandatory in v2/v3
        cJSON_SetNumberValue(cJSON_GetObjectItem(j, "version"), 1);
        assert(configParse(j, parsed, error, sizeof error)); // old backup/NVS migration
        assert(parsed.version == 5 && parsed.switchCount == 10 && !parsed.leds.enabled);
        assert(parsed.switches[9].release.messages[0].number == 103);
        assert(parsed.ladder[10] == 1321);
        cJSON_SetNumberValue(cJSON_GetObjectItem(j, "version"), 6);
        assert(!configParse(j, parsed, error, sizeof error));
        cJSON_Delete(j);
    }
    // Genuine v2 backup migration supplies disabled LEDs with 1:1 assignments.
    c = foot::defaults();
    j = configJson(c);
    cJSON_SetNumberValue(cJSON_GetObjectItem(j, "version"), 2);
    cJSON_DeleteItemFromObject(j, "leds");
    auto switches = cJSON_GetObjectItem(j, "switches");
    for (int i = 0; i < 10; ++i)
        cJSON_DeleteItemFromObject(cJSON_GetArrayItem(switches, i), "led");
    parsed.leds.enabled = true;
    assert(configParse(j, parsed, error, sizeof error));
    assert(parsed.version == 5 && !parsed.leds.enabled && parsed.leds.brightness == 64);
    for (int i = 0; i < 10; ++i)
        assert(parsed.switches[i].led == i + 1);
    cJSON_Delete(j);
    // Version 3 requires well-typed, bounded LED fields and per-switch assignments.
    for (auto key : {"brightness", "colorOrder", "protocol"}) {
        j = configJson(c);
        auto leds = cJSON_GetObjectItem(j, "leds");
        auto field = cJSON_GetObjectItem(leds, key);
        for (double invalid : {-1.0, 256.0, 1.5}) {
            cJSON_SetNumberValue(field, invalid);
            assert(!configParse(j, parsed, error, sizeof error));
        }
        cJSON_DeleteItemFromObject(leds, key);
        assert(!configParse(j, parsed, error, sizeof error));
        cJSON_Delete(j);
    }
    j = configJson(c);
    auto leds = cJSON_GetObjectItem(j, "leds");
    cJSON_ReplaceItemInObjectCaseSensitive(leds, "enabled", cJSON_CreateNumber(1));
    assert(!configParse(j, parsed, error, sizeof error));
    cJSON_Delete(j);
    j = configJson(c);
    cJSON_DeleteItemFromObject(j, "leds");
    assert(!configParse(j, parsed, error, sizeof error));
    cJSON_Delete(j);
    for (double invalid : {-1.0, 11.0, 2.5}) {
        j = configJson(c);
        auto led =
            cJSON_GetObjectItem(cJSON_GetArrayItem(cJSON_GetObjectItem(j, "switches"), 0), "led");
        cJSON_SetNumberValue(led, invalid);
        assert(!configParse(j, parsed, error, sizeof error));
        cJSON_Delete(j);
    }
    c = foot::defaults();
    for (int i = 0; i < 4; i++)
        c.switches[i].press.count = 32;
    assert(foot::validate(c, error, sizeof error));
    j = configJson(c);
    text = cJSON_PrintUnformatted(j);
    assert(text && strlen(text) < 32768);
    assert(configParse(j, parsed, error, sizeof error));
    free(text);
    cJSON_Delete(j);
    c.switches[4].press.count = 1;
    assert(!foot::validate(c, error, sizeof error));
    // Dynamic PC messages receive durable identities; array position is not identity.
    c = foot::defaults();
    c.switches[0].press.count = 2;
    c.switches[0].press.messages[0] = {1, 2, 24, 0, 5, foot::Increment};
    c.switches[0].press.messages[1] = {1, 3, 17, 0, 5, foot::Decrement};
    j = configJson(c);
    assert(configParse(j, parsed, error, sizeof error));
    auto &a = parsed.switches[0].press;
    const int first = a.messages[0].counterId, second = a.messages[1].counterId;
    assert(first && second && first != second && parsed.nextCounterId > second);
    assert(a.messages[0].pcMode == foot::Increment && a.messages[1].pcMode == foot::Decrement);
    cJSON_Delete(j);
    c = parsed;
    std::swap(c.switches[0].press.messages[0], c.switches[0].press.messages[1]);
    j = configJson(c);
    assert(configParse(j, parsed, error, sizeof error));
    assert(parsed.switches[0].press.messages[1].counterId == first);
    cJSON_Delete(j);
    c.switches[0].press.messages[0].counterId = first;
    j = configJson(c);
    assert(!configParse(j, parsed, error, sizeof error));
    cJSON_Delete(j);
    c = foot::defaults(); c.switches[0].press.count = 1;
    c.switches[0].press.messages[0] = {1, 2, 24, 0, 5};
    j = configJson(c);
    cJSON_SetNumberValue(cJSON_GetObjectItem(j, "version"), 4);
    cJSON_DeleteItemFromObject(j, "nextCounterId");
    auto msg = cJSON_GetArrayItem(cJSON_GetObjectItem(cJSON_GetArrayItem(cJSON_GetObjectItem(j, "switches"), 0), "press"), 0);
    cJSON_DeleteItemFromObject(msg, "pcMode"); cJSON_DeleteItemFromObject(msg, "counterId");
    assert(configParse(j, parsed, error, sizeof error));
    assert(parsed.version == 5 && parsed.switches[0].press.messages[0].pcMode == foot::Static);
    for (auto invalid : {"3", "-1", "1.5", "true", "\"INCR\"", "null"}) {
        cJSON_ReplaceItemInObjectCaseSensitive(msg, "pcMode", cJSON_Parse(invalid));
        if (!cJSON_GetObjectItemCaseSensitive(msg, "pcMode"))
            cJSON_AddItemToObject(msg, "pcMode", cJSON_Parse(invalid));
        assert(!configParse(j, parsed, error, sizeof error));
    }
    cJSON_Delete(j);
    puts("Configuration tests passed: roundtrip, strict types, missing fields, maximum capacity");
}
