#ifndef APP_FT4_ENCODER_H
#define APP_FT4_ENCODER_H

#include <stdbool.h>
#include <stdint.h>

// FT4 Protocol Constants
#define FT4_MESSAGE_BITS        77
#define FT4_CRC_BITS            14
#define FT4_ENCODED_BITS        91   // 77 + 14
#define FT4_CODEWORD_BITS       174  // 91 + 83 (LDPC)
#define FT4_SYMBOLS_PER_BIT     2    // 4-FSK: 2 bits per symbol
#define FT4_DATA_SYMBOLS        87   // 174 / 2
#define FT4_SYNC_SYMBOLS        16   // 4 Costas arrays × 4 symbols
#define FT4_RAMP_SYMBOLS        2    // Start and end ramp
#define FT4_TOTAL_SYMBOLS       105  // 87 + 16 + 2

// FT4 Timing Constants
#define FT4_SYMBOL_DURATION_MS  48
#define FT4_TX_DURATION_MS      (FT4_SYMBOL_DURATION_MS * FT4_TOTAL_SYMBOLS)  // 4480 ms
#define FT4_TR_CYCLE_MS         7500  // 7.5 seconds

// FT4 Frequency Constants
#define FT4_TONE_SPACING_HZ     20833  // 20.833 Hz × 1000 for integer math
#define FT4_BASE_FREQ_HZ        1500   // Base frequency in Hz

// Costas Array Definitions
#define FT4_COSTAS_LENGTH       4

// Message Types
#define FT4_MSG_TYPE_FREE_TEXT  0
#define FT4_MSG_TYPE_STANDARD   1
#define FT4_MSG_TYPE_CQ         2

// FT4 Symbol Structure
typedef struct {
    uint8_t symbol;      // Symbol value (0-3)
    uint16_t freq_hz;    // Frequency in Hz
} FT4_Symbol_t;

// FT4 Encoder State
typedef struct {
    uint8_t message_bits[FT4_MESSAGE_BITS];
    uint8_t crc_bits[FT4_CRC_BITS];
    uint8_t encoded_bits[FT4_ENCODED_BITS];
    uint8_t codeword_bits[FT4_CODEWORD_BITS];
    uint8_t data_symbols[FT4_DATA_SYMBOLS];
    uint8_t all_symbols[FT4_TOTAL_SYMBOLS];
    int symbol_count;
} FT4_EncoderState_t;

// Function Prototypes

/**
 * @brief Initialize FT4 encoder
 */
void FT4ENC_Init(void);

/**
 * @brief Encode a message into FT4 symbols
 * @param message Message string (max 13 characters)
 * @param message_len Length of message
 * @param symbols Output symbol array (must be at least FT4_TOTAL_SYMBOLS)
 * @return Number of symbols generated, or negative on error
 */
int FT4ENC_EncodeMessage(const char *message, int message_len, uint8_t *symbols);

/**
 * @brief Calculate CRC-14 for FT4
 * @param bits Input bit array
 * @param length Number of bits
 * @return 14-bit CRC value
 */
uint16_t FT4ENC_CalculateCRC(const uint8_t *bits, int length);

/**
 * @brief Perform LDPC encoding
 * @param bits Input 91-bit array
 * @param codeword Output 174-bit codeword
 */
void FT4ENC_LDPCEncode(const uint8_t *bits, uint8_t *codeword);

/**
 * @brief Map codeword bits to 4-FSK symbols
 * @param codeword Input 174-bit codeword
 * @param symbols Output 87 symbols
 */
void FT4ENC_MapToSymbols(const uint8_t *codeword, uint8_t *symbols);

/**
 * @brief Add sync sequences and ramp symbols
 * @param data_symbols Input 87 data symbols
 * @param all_symbols Output 105 symbols with sync
 */
void FT4ENC_AddSyncSequence(const uint8_t *data_symbols, uint8_t *all_symbols);

/**
 * @brief Calculate frequency for a symbol
 * @param symbol Symbol value (0-3)
 * @param base_freq_hz Base frequency in Hz
 * @param tone_spacing_hz Tone spacing in Hz (×1000 for precision)
 * @return Frequency in Hz
 */
uint16_t FT4ENC_CalculateFrequency(uint8_t symbol, uint16_t base_freq_hz, uint16_t tone_spacing_hz);

/**
 * @brief Convert frequency to BK4819 register value
 * @param freq_hz Frequency in Hz
 * @return REG_71 value
 */
uint16_t FT4ENC_FreqToRegValue(uint16_t freq_hz);

#endif // APP_FT4_ENCODER_H
