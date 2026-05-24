#ifdef ENABLE_FT4_CLEAN_TX

#include <string.h>
#include "driver/st7565.h"
#include "external/printf/printf.h"
#include "misc.h"
#include "radio.h"
#include "ui/helper.h"
#include "ui/ui.h"

void UI_DisplayFT8(void)
{
    char String[22];

    UI_DisplayClear();

    /* Title */
    UI_PrintString("FT8 STANDBY", 0, 127, 0, 8);

    /* Frequency */
    uint32_t freq = gRxVfo->freq_config_TX.Frequency;
    sprintf(String, "%3u.%05u", freq / 100000, freq % 100000);
    UI_PrintStringSmallNormal(String + 7, 97, 0, 3);
    String[7] = 0;
    UI_DisplayFrequency(String, 16, 2, false);

    /* Status */
    UI_PrintString("Waiting PC...", 0, 127, 4, 8);

    ST7565_BlitFullScreen();
}

#endif
