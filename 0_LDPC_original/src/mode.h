#ifndef ECCTG_MODE_H
#define ECCTG_MODE_H

//======================================
//  (check before compile)
//======================================

//#define __PROGRAM_MODE_REF_C__       // Ref-C
//#define __LLR_TWO_DV3__     565
//#define __RUN_MPI__         // Supercon
//#define __12META__          // Deneb: 16B, Piccolo: 12B
//#define __4_BIT_LLR__
//#define __1_BLK_PUNCT__
//#define __3_BLK_PUNCT__
//#define __HBF_LLR_OPT__
//#define __HACRC_IKD_5B__

#if (defined(_WIN64) || defined(_WIN32))
#define __WIN_OS__                  // Windows
#else
#ifdef __PROGRAM_MODE_REF_C__
#define __AUTO_LLR_OPT__
#if !defined(__AUTO_LLR_OPT__)       // LLR matrix loading
#define __RUN_MPI__                 // Supercon
#endif
#endif // __PROGRAM_MODE_REF_C__
#endif

//#define __LLR_PUNCT_TO_DV2__
#if defined(__PROGRAM_MODE_REF_C__)
//#define __PRINT_LOG_DATA__          // Decoder
//#define __LOG_DECODING_STATUS__
//#define __LOG_VNU_IN_OUT__          // sector
//#define __SHOW_RBER_DIST__
#else
//#define __LOG_DECODING_STATUS__
//#define __LOG_VNU_IN_OUT__          // sector
#define __PROGRAM_MODE_TV_GEN__
#define __ECC_TV__
#define __ECC_TV_SYND_INTERNAL_DEBUG__
//#define __FULL_CRC__
//#define __ECC_TV_ITER__
#define __ECC_TV_CNT_DEBUG__        // FULL ENC TV: PARTIAL_ENC_LAST only TV
//#define __TV_FW_MODE__             // vbit cnt, 1 cnt
//#define __ENC_TV_ONLY__
#if defined (__ENC_TV_ONLY__)
//#define __Enc_TV_INTER_DEBUG__             // TV encoder
//#define __NAND_IO_DELIVERY__        // NAND IO
//#define __ENC_TV_ONLY_SINGLE_FILE__ // TV encoder single file
#endif
//#define __FIXED_SECTOR_NUMBER__
//#define __TV_LOG_FIFO_POWER_STOPPING__   // TV
//#define __PRIME_ECC_ENCODER__           // FPGA: Encoder Only Program

#endif

//#define __ONLY_FOR_DEBUG__
//#define __PRINT_GT_ROM_CODE__       // Ref-C
//#define __VSS_ECC_TOP__             // VSS ECC TOP

#define __RUN_PUNCT_RECOVERY__
//#define __GENIE_PUNCT_RECOVERY__
//#define __RUN_PREPROCESSING__
#define __DUAL_UPDATE__
#define __SHUFFLED_DUAL_DIAG__        // Punctured bit
#define __PMU_READ__             // Parity bit
//#define __PMU_ERROR_ONE__             // Parity bit
#define __HALF_COL_UPDATE__           // Full Column Update
#ifdef __HALF_COL_UPDATE__           // Full Column Update
#define __HALF_COL_MODIFIED__           // Full Column Update
#endif //__HALF_COL_UPDATE__           // Full Column Update

//#define __HD_FLOOR_SET__              // message saturated

//#define __CORNER_CHECKER__

/* Algorithm */
//#define __RUN_ITER34_HIGH_DV_SKIP__  // Iter skip
//#define __RUN_PARITY_SKIP__         // Iter skip Dv skip
//#define __MAX_ITER_LIMITED__

#endif
