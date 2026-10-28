#pragma once
#define SIGMIDI_VERSION "0.1"
namespace foot {
inline constexpr char ProjectVersion[] = SIGMIDI_VERSION;
inline constexpr char ProjectName[] = "SIGMIDI Foot Controller v" SIGMIDI_VERSION;
inline constexpr char FirmwareLabel[] = "FOOT CONTROLLER v" SIGMIDI_VERSION;
static_assert(sizeof(ProjectName) - 1 <= 29, "BLE scan response name exceeds its payload");
inline constexpr char BrandName[] = "SIGMIDI";
inline constexpr char WifiSsidFormat[] = "SIGMIDI-%02X%02X";
} // namespace foot
