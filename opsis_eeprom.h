#ifndef __OPSIS_EEPROM_H
#define __OPSIS_EEPROM_H

#ifdef __SDCC

#define __u8    BYTE
#define __u16   __le16
#define __le16  WORD
#define __u32   __le32
#define __le32  DWORD

#define __le16_to_cpu

// Use a macro to make __attribute__ stuff disappear. sdcc always generates
// "packed" structures.
#define __attribute__(x)

#else

#include <stdint.h>

#endif  // __SDCC

struct fx2_config_header {
	__u8   format;
	__le16 vid;
	__le16 pid;
	__le16 did;
	__u8   config;
} __attribute__ ((packed));
// BUILD_BUG_ON(sizeof(struct fx2_c0_config) != 8)

/*
Structures for FX2 C2 load
*/
struct fx2_config_data {
	__be16 length;  // Actually 10 bits
	__be16 address; // Actually 14 bits
	__u8   data[];
} __attribute__ ((packed));

struct fx2_config_data fx2_c2_term = {
	.length = 1 | 0x8000,
	.address = 0xE600,
	.data = { 0 },
};

struct opsis_eeprom {
	struct fx2_config_header fx2;
        // Format information
	char   start_seperator;
	char   magic[5];
	__le16 version;
        // PCB information
	__le64 pcb_batch;
	__u8   pcb_commit[20];
	__u8   pcb_pad[4];
        // Production information
	__le64 prod_batch;
	__le64 prod_program;
        // Event Log
	__u8   eventlog_size;
	__u8   eventlog_data;
        // Checksum
	char   rmagic[5];
	char   end_seperator;
	__u8   crc8_data;
	__u8   crc8_full;
	// Microchip section
	__u8   wp_empty[120];
	__u8   wp_mac[8];
} __attribute__ ((packed));

__u8 oe_calculate_crc8_data(struct opsis_eeprom* data);
__u8 oe_calculate_crc8_full(struct opsis_eeprom* data);

#define OPSIS_MAGIC \
	"OPSIS"
#define OPSIS_RMAGIC \
	"SISPO"
#define OPSIS_SEPERATOR \
	'\0'

// BUILD_BUG_ON(sizeof(struct opsis_eeprom) != 256)
#endif  // __OPSIS_EEPROM
