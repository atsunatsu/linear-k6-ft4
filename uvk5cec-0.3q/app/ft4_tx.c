#include <string.h>

#include "app/ft4_tx.h"
#include "app/ft4_encoder.h"
#include "app/app.h"
#include "ceccommon.h"
#include "driver/bk4819.h"
#include "driver/crc.h"
#include "functions.h"
#include "misc.h"
#include "radio.h"
#include "settings.h"

#define FT4TX_MAX_PAYLOAD_BYTES       64u
#define FT4TX_FRAME_WORDS             36u
#define FT4TX_MIN_STEP_HZ             10u
#define FT4TX_RATE_LIMIT_WINDOW_10MS  20u

static const uint16_t FT4TX_Obfuscation[8] = {
    0x6C16, 0xE614, 0x912E, 0x400D, 0x3521, 0x40D5, 0x0313, 0x80E9
};

typedef struct {
    bool              active;
    uint8_t           payload_length;
    uint8_t           stable_apply_count;
    uint8_t           reserved;
    uint32_t          current_tx_frequency_hz;
    uint32_t          pending_tx_frequency_hz;
    uint32_t          last_applied_tx_frequency_hz;
    uint32_t          last_retune_tick_10ms;
    uint32_t          next_send_tick_10ms;
    uint32_t          symbol_start_tick_10ms;
    uint16_t          frames_sent;
    uint16_t          frame_sequence;
    uint16_t          symbols_sent;
    FT4TX_Status_t    last_status;
    FT4TX_RetuneMode_t retune_mode;
    VFO_Info_t       *session_vfo;
    uint32_t          previous_tx_frequency_hz;
    ModulationMode_t  previous_modulation;
    uint8_t           payload[FT4TX_MAX_PAYLOAD_BYTES];
    uint8_t           ft4_symbols[FT4_TOTAL_SYMBOLS];
    bool              gfsk_mode;
} FT4TX_State_t;

static FT4TX_State_t gFt4TxState;

static void FT4TX_BuildFrame(uint16_t *frame_words)
{
    uint8_t *frame_bytes = (uint8_t *)&frame_words[2];
    memset(frame_words, 0, sizeof(uint16_t) * FT4TX_FRAME_WORDS);
    frame_words[0] = 0xABCD;
    frame_words[1] = gFt4TxState.frame_sequence++;
    memset(frame_bytes, ' ', FT4TX_MAX_PAYLOAD_BYTES);
    memcpy(frame_bytes, gFt4TxState.payload, gFt4TxState.payload_length);
    frame_words[34] = CRC_Calculate(&frame_words[1], 2 + FT4TX_MAX_PAYLOAD_BYTES);
    frame_words[35] = 0xDCBA;
    for (unsigned int i = 0; i < 34; i++)
        frame_words[i + 1] ^= FT4TX_Obfuscation[i % 8];
}

static void FT4TX_ApplyFrequency(uint32_t tx_frequency_hz)
{
    if (gFt4TxState.session_vfo == NULL)
        return;
    gFt4TxState.session_vfo->freq_config_TX.Frequency = tx_frequency_hz;
    if (gFt4TxState.session_vfo->pTX == &gFt4TxState.session_vfo->freq_config_RX)
        gFt4TxState.session_vfo->pTX = &gFt4TxState.session_vfo->freq_config_TX;
    BK4819_SetFrequency(tx_frequency_hz);
    BK4819_PickRXFilterPathBasedOnFrequency(tx_frequency_hz);
    BK4819_SetupPowerAmplifier(gFt4TxState.session_vfo->TXP_CalculatedSetting, tx_frequency_hz);
    gFt4TxState.last_applied_tx_frequency_hz = tx_frequency_hz;
    gFt4TxState.last_retune_tick_10ms = millis10();
}

static void FT4TX_SendGFSKSymbol(void)
{
    if (!gFt4TxState.active || gCurrentFunction != FUNCTION_TRANSMIT)
        return;
    if (gFt4TxState.symbols_sent >= FT4_TOTAL_SYMBOLS) {
        FT4TX_Stop();
        return;
    }
    uint8_t symbol = gFt4TxState.ft4_symbols[gFt4TxState.symbols_sent];
    uint16_t freq = FT4ENC_CalculateFrequency(
        symbol,
        FT4_BASE_FREQ_HZ,
        FT4_TONE_SPACING_HZ
    );
    uint16_t reg_value = FT4ENC_FreqToRegValue(freq);
    BK4819_WriteRegister(BK4819_REG_71, reg_value);
    gFt4TxState.symbols_sent++;
    gFt4TxState.next_send_tick_10ms = millis10() + (FT4_SYMBOL_DURATION_MS / 10);
}

static void FT4TX_SendFrame(void)
{
    uint16_t frame_words[FT4TX_FRAME_WORDS];
    if (!gFt4TxState.active || gCurrentFunction != FUNCTION_TRANSMIT)
        return;
    FT4TX_BuildFrame(frame_words);
    BK4819_SendFSKData(frame_words);
    gFt4TxState.frames_sent++;
    gFt4TxState.next_send_tick_10ms = millis10() + 200;
}

FT4TX_Status_t FT4TX_Start(const uint8_t *payload, uint8_t payload_length, uint32_t tx_frequency_hz)
{
    if (gFt4TxState.active)
        return gFt4TxState.last_status = FT4TX_STATUS_BUSY;
    if (payload_length > FT4TX_MAX_PAYLOAD_BYTES)
        return gFt4TxState.last_status = FT4TX_STATUS_PAYLOAD_TOO_LONG;

    memset(&gFt4TxState, 0, sizeof(gFt4TxState));
    gFt4TxState.session_vfo = gCurrentVfo;
    gFt4TxState.previous_tx_frequency_hz = gCurrentVfo->freq_config_TX.Frequency;
    gFt4TxState.previous_modulation = gCurrentVfo->Modulation;
    gFt4TxState.payload_length = payload_length;
    gFt4TxState.current_tx_frequency_hz = tx_frequency_hz;
    memcpy(gFt4TxState.payload, payload, payload_length);

    gCurrentVfo->Modulation = MODULATION_FM;
    gCurrentVfo->freq_config_TX.Frequency = tx_frequency_hz;
    gCurrentVfo->pTX = &gCurrentVfo->freq_config_TX;

    RADIO_PrepareTX();
    if (gCurrentFunction != FUNCTION_TRANSMIT) {
        gCurrentVfo->freq_config_TX.Frequency = gFt4TxState.previous_tx_frequency_hz;
        gCurrentVfo->Modulation = gFt4TxState.previous_modulation;
        memset(&gFt4TxState, 0, sizeof(gFt4TxState));
        return FT4TX_STATUS_TX_NOT_READY;
    }

    gFt4TxState.active = true;
    gFt4TxState.retune_mode = FT4TX_RETUNE_IMMEDIATE;
    gFt4TxState.last_applied_tx_frequency_hz = tx_frequency_hz;
    gFt4TxState.last_retune_tick_10ms = millis10();
    gFt4TxState.next_send_tick_10ms = gFt4TxState.last_retune_tick_10ms;
    gFt4TxState.symbol_start_tick_10ms = gFt4TxState.last_retune_tick_10ms;
    gFt4TxState.last_status = FT4TX_STATUS_OK;

    FT4ENC_Init();
    int symbols_generated = FT4ENC_EncodeMessage(
        (const char *)payload,
        payload_length,
        gFt4TxState.ft4_symbols
    );

    if (symbols_generated > 0) {
        gFt4TxState.gfsk_mode = true;
        gFt4TxState.symbols_sent = 0;
        BK4819_WriteRegister(BK4819_REG_70, 0x00E0);
        BK4819_WriteRegister(BK4819_REG_30, 0);
        BK4819_WriteRegister(BK4819_REG_30, 0x0302);
        FT4TX_SendGFSKSymbol();
    } else {
        gFt4TxState.gfsk_mode = false;
        FT4TX_SendFrame();
    }

    return FT4TX_STATUS_OK;
}

FT4TX_Status_t FT4TX_UpdateFrequency(uint32_t tx_frequency_hz)
{
    if (!gFt4TxState.active)
        return gFt4TxState.last_status = FT4TX_STATUS_NOT_ACTIVE;

    const uint32_t reference_hz =
        (gFt4TxState.pending_tx_frequency_hz != 0) ? gFt4TxState.pending_tx_frequency_hz : gFt4TxState.last_applied_tx_frequency_hz;
    const uint32_t delta_hz = (tx_frequency_hz > reference_hz) ? (tx_frequency_hz - reference_hz) : (reference_hz - tx_frequency_hz);

    gFt4TxState.current_tx_frequency_hz = tx_frequency_hz;
    if (delta_hz < FT4TX_MIN_STEP_HZ) {
        gFt4TxState.last_status = FT4TX_STATUS_OK;
        return FT4TX_STATUS_OK;
    }

    if (gFt4TxState.pending_tx_frequency_hz != 0 && gFt4TxState.pending_tx_frequency_hz != tx_frequency_hz)
        gFt4TxState.retune_mode = FT4TX_RETUNE_RATE_LIMITED;

    gFt4TxState.pending_tx_frequency_hz = tx_frequency_hz;
    gFt4TxState.last_status = FT4TX_STATUS_OK;
    return FT4TX_STATUS_OK;
}

FT4TX_Status_t FT4TX_Stop(void)
{
    if (!gFt4TxState.active) {
        gFt4TxState.last_status = FT4TX_STATUS_OK;
        return FT4TX_STATUS_OK;
    }

    gFt4TxState.active = false;
    gFt4TxState.pending_tx_frequency_hz = 0;

    if (gCurrentFunction == FUNCTION_TRANSMIT) {
        APP_EndTransmission();
        FUNCTION_Select(FUNCTION_FOREGROUND);
        gFlagEndTransmission = false;
        gUpdateStatus = true;
        gUpdateDisplay = true;
    }

    if (gFt4TxState.session_vfo != NULL) {
        gFt4TxState.session_vfo->freq_config_TX.Frequency = gFt4TxState.previous_tx_frequency_hz;
        gFt4TxState.session_vfo->Modulation = gFt4TxState.previous_modulation;
    }

    memset(&gFt4TxState, 0, sizeof(gFt4TxState));
    gFt4TxState.last_status = FT4TX_STATUS_OK;
    return FT4TX_STATUS_OK;
}

void FT4TX_TimeSlice10ms(void)
{
    if (!gFt4TxState.active)
        return;

    if (gCurrentFunction != FUNCTION_TRANSMIT) {
        FT4TX_Stop();
        return;
    }

    if (gFt4TxState.pending_tx_frequency_hz != 0) {
        const uint32_t now_10ms = millis10();
        const uint32_t reference_hz = gFt4TxState.last_applied_tx_frequency_hz;
        const uint32_t delta_hz = (gFt4TxState.pending_tx_frequency_hz > reference_hz)
            ? (gFt4TxState.pending_tx_frequency_hz - reference_hz)
            : (reference_hz - gFt4TxState.pending_tx_frequency_hz);

        if (delta_hz < FT4TX_MIN_STEP_HZ) {
            gFt4TxState.pending_tx_frequency_hz = 0;
        } else {
            const uint32_t elapsed_10ms = now_10ms - gFt4TxState.last_retune_tick_10ms;
            if (gFt4TxState.retune_mode == FT4TX_RETUNE_IMMEDIATE || elapsed_10ms >= FT4TX_RATE_LIMIT_WINDOW_10MS) {
                FT4TX_ApplyFrequency(gFt4TxState.pending_tx_frequency_hz);
                gFt4TxState.pending_tx_frequency_hz = 0;
                if (gFt4TxState.retune_mode == FT4TX_RETUNE_RATE_LIMITED) {
                    if (++gFt4TxState.stable_apply_count >= 3) {
                        gFt4TxState.retune_mode = FT4TX_RETUNE_IMMEDIATE;
                        gFt4TxState.stable_apply_count = 0;
                    }
                }
            }
        }
    }

    if ((int32_t)(millis10() - gFt4TxState.next_send_tick_10ms) >= 0) {
        if (gFt4TxState.gfsk_mode)
            FT4TX_SendGFSKSymbol();
        else
            FT4TX_SendFrame();
    }
}

void FT4TX_GetState(FT4TX_StateSnapshot_t *snapshot)
{
    memset(snapshot, 0, sizeof(*snapshot));
    snapshot->active = gFt4TxState.active;
    snapshot->last_status = gFt4TxState.last_status;
    snapshot->retune_mode = gFt4TxState.retune_mode;
    snapshot->current_tx_frequency_hz = gFt4TxState.current_tx_frequency_hz;
    snapshot->last_applied_tx_frequency_hz = gFt4TxState.last_applied_tx_frequency_hz;
    snapshot->pending_tx_frequency_hz = gFt4TxState.pending_tx_frequency_hz;
    snapshot->frames_sent = gFt4TxState.frames_sent;
    snapshot->frame_sequence = gFt4TxState.frame_sequence;
}
