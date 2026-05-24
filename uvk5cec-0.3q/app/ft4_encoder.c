#include "app/ft4_encoder.h"
#include <string.h>

#define FT4_CRC_POLYNOMIAL  0x6757
#define FT4_CRC_INIT        0x0000

static const uint8_t costas_s1[FT4_COSTAS_LENGTH] = {0, 1, 3, 2};
static const uint8_t costas_s2[FT4_COSTAS_LENGTH] = {1, 0, 2, 3};
static const uint8_t costas_s3[FT4_COSTAS_LENGTH] = {2, 3, 1, 0};
static const uint8_t costas_s4[FT4_COSTAS_LENGTH] = {3, 2, 0, 1};

static const uint8_t gray_code[4] = {0, 1, 3, 2};

static const uint8_t rvec[77] = {
    0,1,0,0,1,0,1,0,0,1,0,1,1,1,1,0,1,0,0,0,1,0,0,1,1,0,1,1,0,
    1,0,0,1,0,1,1,0,0,0,0,1,0,0,0,1,0,1,0,0,1,1,1,1,0,0,1,0,1,
    0,1,0,1,0,1,1,0,1,1,1,1,1,0,0,0,1,0,1
};

static FT4_EncoderState_t encoder_state;

void FT4ENC_Init(void)
{
    memset(&encoder_state, 0, sizeof(encoder_state));
}

uint16_t FT4ENC_CalculateCRC(const uint8_t *bits, int length)
{
    uint16_t crc = FT4_CRC_INIT;
    int i, j;
    for (i = 0; i < length; i++) {
        crc ^= (bits[i] << 13);
        for (j = 0; j < 14; j++) {
            if (crc & 0x2000)
                crc = (crc << 1) ^ FT4_CRC_POLYNOMIAL;
            else
                crc <<= 1;
        }
    }
    return crc & 0x3FFF;
}

void FT4ENC_Scramble(uint8_t *bits, int length)
{
    int i;
    for (i = 0; i < length && i < 77; i++)
        bits[i] ^= rvec[i];
}

void FT4ENC_MapToSymbols(const uint8_t *codeword, uint8_t *symbols)
{
    int i;
    for (i = 0; i < FT4_DATA_SYMBOLS; i++) {
        uint8_t bit0 = codeword[i * 2];
        uint8_t bit1 = codeword[i * 2 + 1];
        uint8_t symbol_value = (bit1 << 1) | bit0;
        symbols[i] = gray_code[symbol_value];
    }
}

void FT4ENC_AddSyncSequence(const uint8_t *data_symbols, uint8_t *all_symbols)
{
    int pos = 0;
    int i;
    all_symbols[pos++] = 0;
    for (i = 0; i < FT4_COSTAS_LENGTH; i++)
        all_symbols[pos++] = costas_s1[i];
    memcpy(&all_symbols[pos], data_symbols, 29);
    pos += 29;
    for (i = 0; i < FT4_COSTAS_LENGTH; i++)
        all_symbols[pos++] = costas_s2[i];
    memcpy(&all_symbols[pos], data_symbols + 29, 29);
    pos += 29;
    for (i = 0; i < FT4_COSTAS_LENGTH; i++)
        all_symbols[pos++] = costas_s3[i];
    memcpy(&all_symbols[pos], data_symbols + 58, 29);
    pos += 29;
    for (i = 0; i < FT4_COSTAS_LENGTH; i++)
        all_symbols[pos++] = costas_s4[i];
    all_symbols[pos++] = 0;
}

uint16_t FT4ENC_CalculateFrequency(uint8_t symbol, uint16_t base_freq_hz, uint16_t tone_spacing_hz)
{
    uint32_t freq_offset = (uint32_t)symbol * tone_spacing_hz / 1000;
    return base_freq_hz + (uint16_t)freq_offset;
}

uint16_t FT4ENC_FreqToRegValue(uint16_t freq_hz)
{
    return (uint16_t)(((uint32_t)freq_hz * 1353245UL + (1UL << 16)) >> 17);
}

int FT4ENC_EncodeMessage(const char *message, int message_len, uint8_t *symbols)
{
    if (message_len > 13)
        return -1;
    memset(&encoder_state, 0, sizeof(encoder_state));
    int i;
    for (i = 0; i < message_len && i < FT4_MESSAGE_BITS / 8; i++)
        encoder_state.message_bits[i] = message[i];
    FT4ENC_Scramble(encoder_state.message_bits, FT4_MESSAGE_BITS);
    uint16_t crc = FT4ENC_CalculateCRC(encoder_state.message_bits, FT4_MESSAGE_BITS);
    for (i = 0; i < FT4_CRC_BITS; i++)
        encoder_state.crc_bits[i] = (crc >> (13 - i)) & 1;
    memcpy(encoder_state.encoded_bits, encoder_state.message_bits, FT4_MESSAGE_BITS);
    memcpy(encoder_state.encoded_bits + FT4_MESSAGE_BITS, encoder_state.crc_bits, FT4_CRC_BITS);
    FT4ENC_MapToSymbols(encoder_state.encoded_bits, encoder_state.data_symbols);
    FT4ENC_AddSyncSequence(encoder_state.data_symbols, symbols);
    return FT4_TOTAL_SYMBOLS;
}
