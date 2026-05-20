#ifndef APP_FT4_TX_H
#define APP_FT4_TX_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
	FT4TX_STATUS_OK = 0,
	FT4TX_STATUS_BUSY = 1,
	FT4TX_STATUS_NOT_ACTIVE = 2,
	FT4TX_STATUS_TX_NOT_READY = 3,
	FT4TX_STATUS_PAYLOAD_TOO_LONG = 4,
} FT4TX_Status_t;

typedef enum {
	FT4TX_RETUNE_IMMEDIATE = 0,
	FT4TX_RETUNE_RATE_LIMITED = 1,
} FT4TX_RetuneMode_t;

typedef struct __attribute__((__packed__)) {
	bool                 active;
	uint8_t              last_status;
	uint8_t              retune_mode;
	uint8_t              reserved;
	uint32_t             current_tx_frequency_hz;
	uint32_t             last_applied_tx_frequency_hz;
	uint32_t             pending_tx_frequency_hz;
	uint16_t             frames_sent;
	uint16_t             frame_sequence;
} FT4TX_StateSnapshot_t;

void FT4TX_TimeSlice10ms(void);
FT4TX_Status_t FT4TX_Start(const uint8_t *payload, uint8_t payload_length, uint32_t tx_frequency_hz);
FT4TX_Status_t FT4TX_UpdateFrequency(uint32_t tx_frequency_hz);
FT4TX_Status_t FT4TX_Stop(void);
void FT4TX_GetState(FT4TX_StateSnapshot_t *snapshot);

#endif
