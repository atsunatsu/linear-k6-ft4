#ifndef APP_FT4_ENCODER_H
#define APP_FT4_ENCODER_H

#include <stdint.h>

#define FT4_TOTAL_SYMBOLS  105
#define FT4_DATA_SYMBOLS   87
#define FT4_SYMBOL_DURATION_MS  48
#define FT4_TR_CYCLE_MS         7500
#define FT4_TONE_SPACING_HZ     20833
#define FT4_BASE_FREQ_HZ        1500

void FT4ENC_Init(void);

/**
 * @brief Encode a 77-bit payload (10 bytes, MSB first) into 105 FT4 tones.
 * @param payload77  10-byte array containing 77-bit message (MSB first)
 * @param tones      Output array of 105 tone values (0-3)
 * @return 105 on success, negative on error
 */
int FT4ENC_EncodeMessage(const uint8_t *payload77, uint8_t *tones);

#endif
