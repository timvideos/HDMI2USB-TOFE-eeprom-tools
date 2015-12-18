#ifndef __SDCC_STDINT_H
#define __SDCC_STDINT_H

#ifndef __SDCC
#error "File only used with SDCC compiler."
#endif

#define __u8    BYTE
#define __u16   __le16
#define __le16  WORD
#define __u32   __le32
#define __le32  DWORD

#define __le16_to_cpu

// Use a macro to make __attribute__ stuff disappear. sdcc always generates
// "packed" structures.
#define __attribute__(x)

#endif  // __SDCC_STDINT_H
