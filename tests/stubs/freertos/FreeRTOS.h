#pragma once
// Single-threaded host UI tests do not create RTOS tasks or use a real mutex.
using SemaphoreHandle_t = void *;
constexpr unsigned portMAX_DELAY = ~0u;
