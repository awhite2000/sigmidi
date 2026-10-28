#pragma once
#include "cJSON.h"
#include "core.hpp"
cJSON *configJson(const foot::Config &);
bool configParse(const cJSON *, foot::Config &, char *, size_t);
