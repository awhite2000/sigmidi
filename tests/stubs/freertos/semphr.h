#pragma once
#include "FreeRTOS.h"
inline int xSemaphoreTake(SemaphoreHandle_t, unsigned) { return 1; }
inline int xSemaphoreGive(SemaphoreHandle_t) { return 1; }
