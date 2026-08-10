#ifndef ECCTG_COMMON_H
#define ECCTG_COMMON_H

//======================================
// commonly used definitions
//======================================

/* Microsoft Visual Studio */
#ifdef _MSC_VER
#ifndef _CRT_SECURE_NO_WARNINGS
#define _CRT_SECURE_NO_WARNINGS
#endif
#endif

#include <iostream>
#include <fstream>
#include <time.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "mode.h"

#if defined (__WIN_OS__)
#include <direct.h>
#else
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <unistd.h>
#endif

#if defined (__RUN_MPI__)
#include "mpi.h"
#endif

using namespace std;

/* common */
#define FALSE                   0
#define TRUE                    1
#define LEN_FILENAME            300
#define EMPTY                   -1
#define BITS_PER_BYTE           8
#define FLAG_HIGH               1
#define FLAG_LOW                0
#define HEX_BITS                4

/* display */
#if defined(__AUTO_LLR_OPT__)
#define DISPLAY_UNIT            100000  /*10*/ /*1000*/
#else
#define DISPLAY_UNIT            1       /*10*/ /*1000*/
#endif
#define DISPLAY_UNIT_MPI        /*1000*/    100

/* Throughput */
#define MAX_THROUGHPUT_CLOCK    384

/* MPI */
#define ID_ROOT                 0
#define MPI_PRINT_MODE_START    -1
#define MPI_PRINT_MODE_INTER    0
#define MPI_PRINT_MODE_END      1

/* CRC logic */
#define CRC_LEN                 80
#define DEC_D_LEN               256
#define NUM_PCRC_TERMINATION_POINT  4
#define CRC_LOGIC_SHORTENED     0

/* XOR25 register */
#define SEED_LEN                25

/* ECC IP options */
#define MODE_DEC_HD             1
#define MODE_DEC_2SD            2
#define MODE_DEC_3SD            3
#define MODE_DEC_1_5SD          4

#define MODE_CH_RBER            1
#define MODE_CH_FIXED_ERROR     2
#define MODE_CH_STRONG_ERROR    3
#define MODE_CH_ERASURE         4
#define MODE_CH_3SD_FIXED       5

#define MODE_BF_OFF             0
#define MODE_BF_ON              1

#define MODE_SEED_DEFAULT       0
#define MODE_SEED_SAVE_UNCOR_SEED       1
#define MODE_SEED_LOAD_UNCOR_SEED       2
#define MODE_SEED_LOAD_UNCOR_VECTOR     3
#define MODE_SEED_SAVE_ALL_SEED         4
#define MODE_SEED_SAVE_COR_SEED         5
#define MODE_SEED_SAVE_CORNER_SEED           6
#define MODE_SEED_SAVE_UNCOR_SEED_LOAD_INIT_SEED    10
#define MODE_SEED_LOAD_UNCOR_SEED_SAVE_UNCOR_SEED   12
#define MODE_SEED_DEFAULT_LOAD_INIT_SEED            11

#define MODE_SEED_INIT_FIXED        0
#define MODE_SEED_INIT_FIXED2       9999    // DAO(Auto opt) core loop
#define MODE_SEED_INIT_TIME         1

#define MODE_ALL_ZERO_CODEWORD      0
#define MODE_ALL_ONE_CODEWORD       1

#define MODE_SCENARIO_ENC_4KB_DEC_4KB   0

#define MODE_INPUT_PATTERN_RANDOM       0
#define MODE_INPUT_PATTERN_ALL_ZERO     1   // Inverting: LDPC all zero
#define MODE_INPUT_PATTERN_ALL_ONE      2   // msg 0, LDPC all one
#define MODE_INPUT_PATTERN_FIXED        3

#define MODE_POWER_STOPPING_ON          1
#define MODE_POWER_STOPPING_OFF         2

#define MODE_STOPPING_CRITERIA_ITER     1
#define MODE_STOPPING_CRITERIA_CYCLE    2

#define MODE_CRC_FULL           0
#define MODE_CRC_PARTIAL        1
#define MODE_CRC_GENIE          2
#define MODE_PCRC_GENIE         3
#define MODE_CRC_PARTIAL_LAST_ONLY  4

#define MODE_ITER_DEFAULT       0

#define MODE_TV_CASE_HD_NORMAL      1
#define MODE_TV_CASE_HD_MASS        11
#define MODE_TV_CASE_HD_A           12
#define MODE_TV_CASE_HD_B           13
#define MODE_TV_CASE_HD_C           14
#define MODE_TV_CASE_HD_D           15
#define MODE_TV_CASE_HD_E           16
#define MODE_TV_CASE_HD_FIXED_DIN       19
#define MODE_TV_CASE_HD_XOR25_SEED_FIXED    191
#define MODE_TV_CASE_HD_XOR25_SEED_RBER     192
#define MODE_TV_CASE_HD_POWER_0         100
#define MODE_TV_CASE_HD_POWER_50        101
#define MODE_TV_CASE_HD_POWER_100       102
#define MODE_TV_CASE_HD_POWER_150       103
#define MODE_TV_CASE_HD_POWER_155       104
#define MODE_TV_CASE_HD_POWER_165       105
#define MODE_TV_CASE_HD_POWER_200       106
#define MODE_TV_CASE_HD_POWER_250       107
#define MODE_TV_CASE_HD_POWER_300       108
#define MODE_TV_CASE_HD_POWER_350       109
#define MODE_TV_CASE_HD_POWER_400       110
#define MODE_TV_CASE_HD_POWER_450       111
#define MODE_TV_CASE_HD_POWER_500       112

#define MODE_TV_CASE_2SD_NORMAL     2
#define MODE_TV_CASE_2SD_MASS       21
#define MODE_TV_CASE_2SD_A          22
#define MODE_TV_CASE_2SD_B          23
#define MODE_TV_CASE_2SD_C          24
#define MODE_TV_CASE_2SD_FIXED_DIN      29
#define MODE_TV_CASE_2SD_XOR25_SEED_RBER    292
#define MODE_TV_CASE_2SD_XOR25_SEED_STRONG_ERROR    293

#define MODE_TV_CASE_3SD_NORMAL     3
#define MODE_TV_CASE_3SD_MASS       31
#define MODE_TV_CASE_3SD_A          32
#define MODE_TV_CASE_3SD_B          33
#define MODE_TV_CASE_3SD_C          34
#define MODE_TV_CASE_3SD_D          35
#define MODE_TV_CASE_3SD_FIXED_DIN      39
#define MODE_TV_CASE_3SD_XOR25_SEED_RBER      392

#define MODE_TV_CASE_1_5SD_NORMAL       4
#define MODE_TV_CASE_1_5SD_MASS         41
#define MODE_TV_CASE_1_5SD_FIXED_DIN    49
#define MODE_TV_CASE_1_5SD_XOR25_SEED_ERASURE   494

#define MODE_TV_ERR_POS_FIXED       1
#define MODE_TV_ERR_POS_RANDOM      2

#define MODE_RANDOM_TYPE_SRAND      1
#define MODE_RANDOM_TYPE_XOR_25     2

/* PCRC stop type */
#define PCRC_STOP_NO            0
#define PCRC_STOP_TYPE_1        1   // Store: Dual update
#define PCRC_STOP_TYPE_2        2   // Store: Single update

/* power stopping threshold */
#define HD_POWER_STOPPING_TH        /*1023*/    999999
#define SD_POWER_STOPPING_TH        /*1022*//*2004C*/999999

#define CSW_VALUE_JUMP              /*2000*/    999999

/* Prime ECC layout */
#define LAYOUT_PRIME_512B_TLC_VSS_OFF   1
//#define LAYOUT_PRIME_512B_TLC_VSS_ON  2
//#define LAYOUT_PRIME_520B_TLC_VSS_OFF 11
//#define LAYOUT_PRIME_520B_TLC_VSS_ON  12
//#define LAYOUT_PRIME_512B_QLC_VSS_OFF 3
//#define LAYOUT_PRIME_512B_QLC_VSS_ON  4

#if defined(__12META__)
/* MBF mode threshold */
#define SW_TH_BF_DEFAULT               740
#define SW_TH_BF_520B_TLC_ON           340
#define SW_TH_BF_520B_TLC_OFF          400
#define SW_TH_BF_512B_TLC_ON           460
#define SW_TH_BF_512B_TLC_OFF          530
#define SW_TH_BF_512B_QLC_ON           740
#define SW_TH_BF_512B_QLC_OFF          800

/* S-8th Set0 mode threshold */
#define SW_TH_5_8_SET0_DEFAULT             950
#define SW_TH_5_8_SET0_520B_TLC_ON         450  /*720*/
#define SW_TH_5_8_SET0_520B_TLC_OFF        500
#define SW_TH_5_8_SET0_512B_TLC_ON         550
#define SW_TH_5_8_SET0_512B_TLC_OFF        620
#define SW_TH_5_8_SET0_512B_QLC_ON         950
#define SW_TH_5_8_SET0_512B_QLC_OFF        1010

/* 5-8th Set1 mode threshold */
#define SW_TH_5_8_SET1_DEFAULT             1270
#define SW_TH_5_8_SET1_520B_TLC_ON         630
#define SW_TH_5_8_SET1_520B_TLC_OFF        710
#define SW_TH_5_8_SET1_512B_TLC_ON         780
#define SW_TH_5_8_SET1_512B_TLC_OFF        870
#define SW_TH_5_8_SET1_512B_QLC_ON         1270
#define SW_TH_5_8_SET1_512B_QLC_OFF        1330

#else

/* HBF mode threshold */
#define SW_TH_BF_DEFAULT               630
#define SW_TH_BF_520B_TLC_ON           440
#define SW_TH_BF_520B_TLC_OFF          500
#define SW_TH_BF_512B_TLC_ON           560
#define SW_TH_BF_512B_TLC_OFF          630
#define SW_TH_BF0_512B_TLC_OFF          680
#define SW_TH_BF1_512B_TLC_OFF          130

/* 5-8th Set0 mode threshold */
#define SW_TH_5_8_SET0_DEFAULT          960  /*720*/
#define SW_TH_5_8_SET0_520B_TLC_ON      550
#define SW_TH_5_8_SET0_520B_TLC_OFF     600
#define SW_TH_5_8_SET0_512B_TLC_ON         650
#define SW_TH_5_8_SET0_512B_TLC_OFF        1100

/* 5-8th Set1 mode threshold */
#define SW_TH_5_8_SET1_DEFAULT          950
#define SW_TH_5_8_SET1_520B_TLC_ON      710
#define SW_TH_5_8_SET1_520B_TLC_OFF     790
#define SW_TH_5_8_SET1_512B_TLC_ON      860
#define SW_TH_5_8_SET1_512B_TLC_OFF     950
#endif

//#define META_12B_SHORTENED_BIT_PRIME_INFO_4KB           (8 * BITS_PER_BYTE)
//#define META_12B_PUNCTURED_BIT_PRIME_INFO_4KB

//#define META_16B_SHORTENED_BIT_PRIME_INFO_4KB           (2 * BITS_PER_BYTE)
//#define META_16B_PUNCTURED_BIT_PRIME_INFO_4KB

/* PCRC termination point for VSS off */
#define PCRC_TERMINATION_POINT_PRIME_512B_1     128//33
#define PCRC_TERMINATION_POINT_PRIME_512B_2     128//63
#define PCRC_TERMINATION_POINT_PRIME_512B_3     128//95
#define PCRC_TERMINATION_POINT_PRIME_512B_4     128//128

//#define PCRC_TERMINATION_POINT_PRIME_520B_1      33
//#define PCRC_TERMINATION_POINT_PRIME_520B_2      63
//#define PCRC_TERMINATION_POINT_PRIME_520B_3      95
//#define PCRC_TERMINATION_POINT_PRIME_520B_4      128

//#define PCRC_TERMINATION_POINT_PRIME_520B_1     35
//#define PCRC_TERMINATION_POINT_PRIME_520B_2     65
//#define PCRC_TERMINATION_POINT_PRIME_520B_1     97
//#define PCRC_TERMINATION_POINT_PRIME_520B_2     130

//#define PCRC_TERMINATION_POINT_PRIME_528B_1      34
//#define PCRC_TERMINATION_POINT_PRIME_528B_2      67
//#define PCRC_TERMINATION_POINT_PRIME_528B_3       99
//#define PCRC_TERMINATION_POINT_PRIME_528B_4      132

#define IDX_WEAK_NUM            0
#define IDX_CHECK_SUM           1
#define TWO_CLK                 2

/* Graph thinning */
#define GT_HW_MAX_ROW           17//3  /*20*/

#if defined(__Dv10_CONV__)
#define MAX_DV_GLOBAL           10
#else
#define MAX_DV_GLOBAL           17  /*16*/ /*12*/
#define MAX_DV_GLOBAL_2ND       13
#define MAX_DV_GLOBAL_HALF      10//8
#endif
#define DV_5                    5
#define DV_2                    2

/* test vector */
#define TV_MASS_CASE_FACTOR             10//10
#define TV_ERROR_PATTERN_SIZE_DEFAULT   8
#define TV_ERROR_PATTERN_SIZE_HD_SPECIAL    100
#define TV_ERROR_PATTERN_SIZE_2SD_SPECIAL   20
#define TV_ERROR_PATTERN_SIZE_3SD_SPECIAL   20
#define TV_INPUT_PATTERN_SIZE           11
#define TV_INPUT_PATTERN_SIZE_ENC_ONLY  /*100*/  10

#define TV_PRINT        1   // 0 : iteration, 1 : column block

#define TV_LINE_WIDTH_256   256
#define TV_LINE_WIDTH_128   128
#define TV_LINE_WIDTH_64    64
#define TV_LINE_WIDTH_32    32
#define TV_LINE_WIDTH_16    16
#define TV_LINE_WIDTH_8     8
#define TV_LINE_WIDTH_4     4

/* message */
#if defined(__4_BIT_LLR__)
#define V_MAG7          7
#define V_MAG6          6
#define V_MAG5          5
#define V_MAG4          4
#define V_MAG3          3
#define V_MAG2          2
#define V_MAG1          1
#define V_MAG0          0

#define EDGE_MAG_8      8
#define EDGE_MAG_7      7
#define EDGE_MAG_6      6
#define EDGE_MAG_5      5
#define EDGE_MAG_4      4
#define EDGE_MAG_3      3
#define EDGE_MAG_2      2
#define EDGE_MAG_1      1

#else
#define V_VERY_STRONG       3
#define V_NORMAL_STRONG     2
#define V_NORMAL_WEAK       1
#define V_VERY_WEAK         0

#define EDGE_MAG_7      7
#define EDGE_MAG_5      5
#define EDGE_MAG_3      3
#define EDGE_MAG_1      1

#endif

#define V_MINUS         1
#define V_PLUS          0

/* timing */
#define PMU_UNIT_WIDTH          8
#define PMU_UNIT_SIZE           128
#define PMU_HIT                 0
#define PMU_NON_HIT             1
#define CYCLE_IDLE              -1
#define CYCLE_END               -2
#define CYCLE_BEFORE_START      -3
#define CYCLE_FOR_PREPROCESSING 8

#define PHASE_M1        -1
#define PHASE_Z         0
#define PHASE_P1        1
#define PHASE_P2        2
#define PHASE_P3        3
#define PHASE_P4        4
#define PHASE_PREV2     5
#define PHASE_GAP_RTL   2   //RTL clk delay
#define PHASE_GAP       5
#define POWER_STOPPING_DELAY        3   // power stopping

/* Decoding rule */
#define CH_LLR_MAX              /*15*/  31
#define CH_LLR_MIN                      0

#ifdef __HALF_COL_MODIFIED__
#define HCU_COL_1_IDX       127
#define HCU_COL_2_IDX       128
#define SEPARATE_V_DEG_1     9
#define SEPARATE_V_DEG_2     7
#endif // __HALF_COL_MODIFIED__

//======================================
// Prime ECC 2.1
// Date : 2023-11-08 11:01:34
// HD mode
// Version : 3.0
// Update : 23.11.08
// 2SD mode
// Version : 2.0
// Update : 23.10.04
// Version : 3.0
// Update : 23.10.06
//======================================

#define ITER_MAX_REF_C_HD_NUM       5
#define ITER_MAX_REF_C_2SD_NUM      9
#define ITER_MAX_REF_C_3SD_NUM      15
#define ITER_MAX_REF_C_1_5SD_NUM    1

#ifdef __AUTO_LLR_OPT__
#define ITER_MAX_HBF                0
#else
#define ITER_MAX_HBF                4
#endif // __AUTO_LLR_OPT__

#ifdef __4_BIT_LLR__

#define ITER_MAX_HD_1_PRIME     8
#define ITER_MAX_HD_2_PRIME     50
#define ITER_MAX_HD_3_PRIME     100
#define ITER_MAX_HD_PRIME           120

#define ITER_MAX_2SD_1_PRIME        200
#define ITER_MAX_2SD_2_PRIME        401
#define ITER_MAX_2SD_3_PRIME        651
#define ITER_MAX_2SD_4_PRIME        899
#define ITER_MAX_2SD_5_PRIME        929
#define ITER_MAX_2SD_6_PRIME        959
#define ITER_MAX_2SD_7_PRIME        989
#define ITER_MAX_2SD_8_PRIME        1019
#define ITER_MAX_2SD_PRIME          1040

#define ITER_MAX_3SD_1_PRIME        200
#define ITER_MAX_3SD_2_PRIME        352
#define ITER_MAX_3SD_3_PRIME        504
#define ITER_MAX_3SD_4_PRIME        655
#define ITER_MAX_3SD_5_PRIME        756
#define ITER_MAX_3SD_6_PRIME        857
#define ITER_MAX_3SD_7_PRIME        1058
#define ITER_MAX_3SD_8_PRIME        1249
#define ITER_MAX_3SD_PRIME        1400

#define PRIME_HD_LLR_TABLE_NUM_ROW  40
#define PRIME_2SD_LLR_TABLE_NUM_ROW 48
#define PRIME_3SD_LLR_TABLE_NUM_ROW 116

#define PRIME_LLR_TABLE_NUM_DEGREE  4
#define PRIME_LLR_TABLE_NUM_TH      7

#else

#define ITER_MAX_HD_1_PRIME     8
#define ITER_MAX_HD_2_PRIME     64
#define ITER_MAX_HD_3_PRIME     100
#define ITER_MAX_HD_PRIME           120

#define ITER_MAX_2SD_1_PRIME        100
#define ITER_MAX_2SD_2_PRIME        200
#define ITER_MAX_2SD_3_PRIME        240
#define ITER_MAX_2SD_4_PRIME        340
#define ITER_MAX_2SD_5_PRIME        540
#define ITER_MAX_2SD_6_PRIME        580
#define ITER_MAX_2SD_7_PRIME        730
#define ITER_MAX_2SD_8_PRIME        880
#define ITER_MAX_2SD_PRIME          920

#define ITER_MAX_3SD_1_PRIME        130
#define ITER_MAX_3SD_2_PRIME        170
#define ITER_MAX_3SD_3_PRIME        271
#define ITER_MAX_3SD_4_PRIME        311
#define ITER_MAX_3SD_5_PRIME        462
#define ITER_MAX_3SD_6_PRIME        612
#define ITER_MAX_3SD_7_PRIME        652
#define ITER_MAX_3SD_8_PRIME        803
#define ITER_MAX_3SD_9_PRIME        843
#define ITER_MAX_3SD_10_PRIME       994
#define ITER_MAX_3SD_11_PRIME       1034
#define ITER_MAX_3SD_12_PRIME       1260
#define ITER_MAX_3SD_13_PRIME       1300
#define ITER_MAX_3SD_14_PRIME       1360
#define ITER_MAX_3SD_PRIME       1400

#define PRIME_HD_LLR_TABLE_NUM_ROW  63
#define PRIME_2SD_LLR_TABLE_NUM_ROW 36
#define PRIME_3SD_LLR_TABLE_NUM_ROW 66

#ifdef __LLR_TWO_DV3__
#define PRIME_LLR_TABLE_NUM_DEGREE  4
#else
#define PRIME_LLR_TABLE_NUM_DEGREE  4   /*3*/
#endif

#define PRIME_LLR_TABLE_NUM_TH      3

#endif

#define PRIME_LLR_TABLE_NUM_COH     1
#ifdef __4_BIT_LLR__


#else
enum {
    PRIME_HD_LLR_TABLE_IDX_ITER_1,
    PRIME_HD_LLR_TABLE_IDX_ITER_2_4_A,
    PRIME_HD_LLR_TABLE_IDX_ITER_2_4_B,
    PRIME_HD_LLR_TABLE_IDX_ITER_2_4_C,
    PRIME_HD_LLR_TABLE_IDX_ITER_2_4_D,
    PRIME_HD_LLR_TABLE_IDX_ITER_2_4_E,
    PRIME_HD_LLR_TABLE_IDX_ITER_5_f0,
    PRIME_HD_LLR_TABLE_IDX_ITER_6_8_A_f0,
    PRIME_HD_LLR_TABLE_IDX_ITER_6_8_B_f0,
    PRIME_HD_LLR_TABLE_IDX_ITER_6_8_C_f0,
    PRIME_HD_LLR_TABLE_IDX_ITER_6_8_D_f0,
    PRIME_HD_LLR_TABLE_IDX_ITER_5_f1,
    PRIME_HD_LLR_TABLE_IDX_ITER_6_8_A_f1,
    PRIME_HD_LLR_TABLE_IDX_ITER_6_8_B_f1,
    PRIME_HD_LLR_TABLE_IDX_ITER_6_8_C_f1,
    PRIME_HD_LLR_TABLE_IDX_ITER_6_8_D_f1,
    PRIME_HD_LLR_TABLE_IDX_ITER_6_8_E_f1,
    PRIME_HD_LLR_TABLE_IDX_ITER_9_44_A,
    PRIME_HD_LLR_TABLE_IDX_ITER_9_44_B,
    PRIME_HD_LLR_TABLE_IDX_ITER_9_44_C,
    PRIME_HD_LLR_TABLE_IDX_ITER_9_44_D,
    PRIME_HD_LLR_TABLE_IDX_ITER_9_44_E,
    PRIME_HD_LLR_TABLE_IDX_ITER_45_64_A,
    PRIME_HD_LLR_TABLE_IDX_ITER_45_64_B,
    PRIME_HD_LLR_TABLE_IDX_ITER_45_64_C,
    PRIME_HD_LLR_TABLE_IDX_ITER_45_64_D,
    PRIME_HD_LLR_TABLE_IDX_ITER_45_64_E,
    PRIME_HD_LLR_TABLE_IDX_ITER_45_64_F,
    PRIME_HD_LLR_TABLE_IDX_ITER_65_74_A,
    PRIME_HD_LLR_TABLE_IDX_ITER_65_74_B,
    PRIME_HD_LLR_TABLE_IDX_ITER_65_74_C,
    PRIME_HD_LLR_TABLE_IDX_ITER_65_74_D,
    PRIME_HD_LLR_TABLE_IDX_ITER_65_74_E,
    PRIME_HD_LLR_TABLE_IDX_ITER_65_74_F,
    PRIME_HD_LLR_TABLE_IDX_ITER_75_84_A,
    PRIME_HD_LLR_TABLE_IDX_ITER_75_84_B,
    PRIME_HD_LLR_TABLE_IDX_ITER_75_84_C,
    PRIME_HD_LLR_TABLE_IDX_ITER_75_84_D,
    PRIME_HD_LLR_TABLE_IDX_ITER_75_84_E,
    PRIME_HD_LLR_TABLE_IDX_ITER_75_84_F,
    PRIME_HD_LLR_TABLE_IDX_ITER_85_104_A,
    PRIME_HD_LLR_TABLE_IDX_ITER_85_104_B,
    PRIME_HD_LLR_TABLE_IDX_ITER_85_104_C,
    PRIME_HD_LLR_TABLE_IDX_ITER_85_104_D,
    PRIME_HD_LLR_TABLE_IDX_ITER_85_104_E,
    PRIME_HD_LLR_TABLE_IDX_ITER_85_104_F,
    PRIME_HD_LLR_TABLE_IDX_ITER_85_104_G,
    PRIME_HD_LLR_TABLE_IDX_ITER_105_114_A,
    PRIME_HD_LLR_TABLE_IDX_ITER_105_114_B,
    PRIME_HD_LLR_TABLE_IDX_ITER_105_114_C,
    PRIME_HD_LLR_TABLE_IDX_ITER_105_114_D,
    PRIME_HD_LLR_TABLE_IDX_ITER_105_114_E,
    PRIME_HD_LLR_TABLE_IDX_ITER_105_114_F,
    PRIME_HD_LLR_TABLE_IDX_ITER_105_114_G,
    PRIME_HD_LLR_TABLE_IDX_ITER_105_114_H,
    PRIME_HD_LLR_TABLE_IDX_ITER_115_124_A,
    PRIME_HD_LLR_TABLE_IDX_ITER_115_124_B,
    PRIME_HD_LLR_TABLE_IDX_ITER_115_124_C,
    PRIME_HD_LLR_TABLE_IDX_ITER_115_124_D,
    PRIME_HD_LLR_TABLE_IDX_ITER_115_124_E,
    PRIME_HD_LLR_TABLE_IDX_ITER_115_124_F,
    PRIME_HD_LLR_TABLE_IDX_ITER_115_124_G,
    PRIME_HD_LLR_TABLE_IDX_ITER_115_124_H,
};

enum {
    PRIME_2SD_LLR_TABLE_IDX_ITER_1_100_A,
    PRIME_2SD_LLR_TABLE_IDX_ITER_1_100_B,
    PRIME_2SD_LLR_TABLE_IDX_ITER_1_100_C,
    PRIME_2SD_LLR_TABLE_IDX_ITER_1_100_D,
    PRIME_2SD_LLR_TABLE_IDX_ITER_101_200_A,
    PRIME_2SD_LLR_TABLE_IDX_ITER_101_200_B,
    PRIME_2SD_LLR_TABLE_IDX_ITER_101_200_C,
    PRIME_2SD_LLR_TABLE_IDX_ITER_101_200_D,
    PRIME_2SD_LLR_TABLE_IDX_ITER_201_210,
    PRIME_2SD_LLR_TABLE_IDX_ITER_211_220,
    PRIME_2SD_LLR_TABLE_IDX_ITER_221_230,
    PRIME_2SD_LLR_TABLE_IDX_ITER_231_240,
    PRIME_2SD_LLR_TABLE_IDX_ITER_241,
    PRIME_2SD_LLR_TABLE_IDX_ITER_242_340_A,
    PRIME_2SD_LLR_TABLE_IDX_ITER_242_340_B,
    PRIME_2SD_LLR_TABLE_IDX_ITER_242_340_C,
    PRIME_2SD_LLR_TABLE_IDX_ITER_242_340_D,
    PRIME_2SD_LLR_TABLE_IDX_ITER_341_540_A,
    PRIME_2SD_LLR_TABLE_IDX_ITER_341_540_B,
    PRIME_2SD_LLR_TABLE_IDX_ITER_341_540_C,
    PRIME_2SD_LLR_TABLE_IDX_ITER_341_540_D,
    PRIME_2SD_LLR_TABLE_IDX_ITER_541_550,
    PRIME_2SD_LLR_TABLE_IDX_ITER_551_560,
    PRIME_2SD_LLR_TABLE_IDX_ITER_561_570,
    PRIME_2SD_LLR_TABLE_IDX_ITER_571_580,
    PRIME_2SD_LLR_TABLE_IDX_ITER_581,
    PRIME_2SD_LLR_TABLE_IDX_ITER_582_730_A,
    PRIME_2SD_LLR_TABLE_IDX_ITER_582_730_B,
    PRIME_2SD_LLR_TABLE_IDX_ITER_582_730_C,
    PRIME_2SD_LLR_TABLE_IDX_ITER_731_880_A,
    PRIME_2SD_LLR_TABLE_IDX_ITER_731_880_B,
    PRIME_2SD_LLR_TABLE_IDX_ITER_731_880_C,
    PRIME_2SD_LLR_TABLE_IDX_ITER_881_890,
    PRIME_2SD_LLR_TABLE_IDX_ITER_891_900,
    PRIME_2SD_LLR_TABLE_IDX_ITER_901_910,
    PRIME_2SD_LLR_TABLE_IDX_ITER_911_920,
};

enum
{
    PRIME_3SD_LLR_TABLE_IDX_ITER_1_130_A,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1_130_B,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1_130_C,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1_130_D,
    PRIME_3SD_LLR_TABLE_IDX_ITER_131_140,
    PRIME_3SD_LLR_TABLE_IDX_ITER_141_150,
    PRIME_3SD_LLR_TABLE_IDX_ITER_151_160,
    PRIME_3SD_LLR_TABLE_IDX_ITER_161_170,
    PRIME_3SD_LLR_TABLE_IDX_ITER_171,
    PRIME_3SD_LLR_TABLE_IDX_ITER_172_271_A,
    PRIME_3SD_LLR_TABLE_IDX_ITER_172_271_B,
    PRIME_3SD_LLR_TABLE_IDX_ITER_172_271_C,
    PRIME_3SD_LLR_TABLE_IDX_ITER_172_271_D,
    PRIME_3SD_LLR_TABLE_IDX_ITER_272_281,
    PRIME_3SD_LLR_TABLE_IDX_ITER_282_291,
    PRIME_3SD_LLR_TABLE_IDX_ITER_292_301,
    PRIME_3SD_LLR_TABLE_IDX_ITER_302_311,
    PRIME_3SD_LLR_TABLE_IDX_ITER_312,
    PRIME_3SD_LLR_TABLE_IDX_ITER_313_462_A,
    PRIME_3SD_LLR_TABLE_IDX_ITER_313_462_B,
    PRIME_3SD_LLR_TABLE_IDX_ITER_313_462_C,
    PRIME_3SD_LLR_TABLE_IDX_ITER_313_462_D,
    PRIME_3SD_LLR_TABLE_IDX_ITER_463_612_A,
    PRIME_3SD_LLR_TABLE_IDX_ITER_463_612_B,
    PRIME_3SD_LLR_TABLE_IDX_ITER_463_612_C,
    PRIME_3SD_LLR_TABLE_IDX_ITER_463_612_D,
    PRIME_3SD_LLR_TABLE_IDX_ITER_613_622,
    PRIME_3SD_LLR_TABLE_IDX_ITER_623_632,
    PRIME_3SD_LLR_TABLE_IDX_ITER_633_637,
    PRIME_3SD_LLR_TABLE_IDX_ITER_638_652,
    PRIME_3SD_LLR_TABLE_IDX_ITER_653,
    PRIME_3SD_LLR_TABLE_IDX_ITER_654_803_A,
    PRIME_3SD_LLR_TABLE_IDX_ITER_654_803_B,
    PRIME_3SD_LLR_TABLE_IDX_ITER_654_803_C,
    PRIME_3SD_LLR_TABLE_IDX_ITER_654_803_D,
    PRIME_3SD_LLR_TABLE_IDX_ITER_804_813,
    PRIME_3SD_LLR_TABLE_IDX_ITER_814_823,
    PRIME_3SD_LLR_TABLE_IDX_ITER_824_833,
    PRIME_3SD_LLR_TABLE_IDX_ITER_834_843,
    PRIME_3SD_LLR_TABLE_IDX_ITER_844,
    PRIME_3SD_LLR_TABLE_IDX_ITER_845_994_A,
    PRIME_3SD_LLR_TABLE_IDX_ITER_845_994_B,
    PRIME_3SD_LLR_TABLE_IDX_ITER_845_994_C,
    PRIME_3SD_LLR_TABLE_IDX_ITER_845_994_D,
    PRIME_3SD_LLR_TABLE_IDX_ITER_995_1004,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1005_1014,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1015_1024,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1025_1034,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1035,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1036_1260_A,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1036_1260_B,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1036_1260_C,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1036_1260_D,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1261_1270,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1271_1280,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1281_1290,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1291_1300,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1301,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1302_1360_A,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1302_1360_B,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1302_1360_C,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1302_1360_D,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1361_1370,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1371_1380,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1381_1390,
    PRIME_3SD_LLR_TABLE_IDX_ITER_1391_1400,

};

enum {
    PRIME_LLR_TABLE_IDX_MAXDV = 0,  // 8, 9
    PRIME_LLR_TABLE_IDX_MIDDV = 0,  // 5, 6, 7
    PRIME_LLR_TABLE_IDX_DV4 = 1,
    PRIME_LLR_TABLE_IDX_DV3 = 2,    /*1*/
    PRIME_LLR_TABLE_IDX_DV2 = 3     /*2*/
};

#define RSP1_2SD_PRIME_1    241
#define RSP1_2SD_PRIME_2    581
#define RSP1_3SD_PRIME_1    171
#define RSP1_3SD_PRIME_2    312
#define RSP1_3SD_PRIME_3    653
#define RSP1_3SD_PRIME_4    844
#define RSP1_3SD_PRIME_5    1035
#define RSP1_3SD_PRIME_6    1301


#endif // __4_BIT_LLR__

#define PUNCTURED_COL_NUM       2   /*2*/ /*3*/
#define PR_MAJORITY_MAG         12

#if defined(__1_BLK_PUNCT__)
#define SHORTENED_BIT_PRIME_INFO_4KB            (0 * BITS_PER_BYTE)
#define PUNCTURED_BIT_PRIME_INFO_4KB            (0 * BITS_PER_BYTE)
#else
#if defined(__HACRC_IKD_5B__)
#define SHORTENED_BIT_PRIME_INFO_4KB            (31 * BITS_PER_BYTE)
#else
#define SHORTENED_BIT_PRIME_INFO_4KB            (4 * BITS_PER_BYTE)
#endif
#ifdef __3_BLK_PUNCT__
#define PUNCTURED_BIT_PRIME_INFO_4KB            (92 * BITS_PER_BYTE)
#else
#if defined(__HACRC_IKD_5B__)
#define PUNCTURED_BIT_PRIME_INFO_4KB            (65 * BITS_PER_BYTE)
#else
#define PUNCTURED_BIT_PRIME_INFO_4KB            (60 * BITS_PER_BYTE)
#define PUNCTURED_BIT_PRIME_INFO_4KB_SEPERATE   (50 * BITS_PER_BYTE)
#endif
#endif
#endif

#define PUNCTURED_BIT_PRIME_PARITY_4KB          (0 * BITS_PER_BYTE)

enum {
    FLAG_HD_1_4_SET_TYPE_0 = 0,
    FLAG_HD_1_4_SET_TYPE_1 = 1,
};

enum {
    FLAG_HD_5_8_SET_TYPE_0 = 0,
    FLAG_HD_5_8_SET_TYPE_1 = 1,
};

enum {
    FLAG_HD_FLOOR_TYPE_0 = 0,
    FLAG_HD_FLOOR_TYPE_1,
    FLAG_HD_FLOOR_TYPE_2,
    FLAG_HD_FLOOR_TYPE_3,
};

enum {
    HD_FLOOR_CNT_TH1 = 15,
    HD_FLOOR_CNT_TH2 = 10,
};

enum {
    HD_FLOOR_CSW_TH1_512B_TLC_OFF = 64,
    HD_FLOOR_CSW_TH2_512B_TLC_OFF = 234,
    HD_FLOOR_CSW_TH1_512B_TLC_ON = 64,
    HD_FLOOR_CSW_TH2_512B_TLC_ON = 234,

    HD_FLOOR_CSW_TH1_512B_QLC_OFF = 80,
    HD_FLOOR_CSW_TH2_512B_QLC_OFF = 280,
    HD_FLOOR_CSW_TH1_512B_QLC_ON = 80,
    HD_FLOOR_CSW_TH2_512B_QLC_ON = 280,
};

#define FLOOR_DETECT_ON_ITER_START_TLC  10
#define FLOOR_DETECT_ON_ITER_END_TLC    74
#define FLOOR_DETECT_ON_ITER_START_QLC  29
#define FLOOR_DETECT_ON_ITER_END_QLC    89

#define GROUP_TYPE_ITER     0
#define GROUP_TYPE_CSW      1

#define LOG_SHOW_TYPE_ALL       0
#define LOG_SHOW_TYPE_ONE       1
#define LOG_SHOW_TYPE_ERR       2

/* functions */
void    shift_mem(int * arr, int len, int s, int dir);
void    Set_Array(int * x, int len, int v);
int     Convert_Binary_Hex(int* arr, int offset, int k);
void    Print_Array_HEX(FILE * fp, int* arr, int line_len, int block_len, int start_pos);
void    Print_Array_HEX_Fill_F(FILE * fp, int* arr, int data_len, int line_width);
void    Intentional_Blank();
void    Print_Excuting_Time(FILE * fp, int bFile, time_t start, time_t end);
void    Init_Buf(char * buf, int len);
void    Init_Buf(int * buf, int len);
void    Copy_1D_Array(int *arr_dest, int *arr_src, int arr_len);
void    Copy_1D_Array(double *arr_dest, double *arr_src, int arr_len);
void    Print_Decimal_to_Binary(FILE * fp, int d, int bit_len);

void    Print_Array_HEX_FW(FILE* fp, int* arr, int line_len_bits, int line_num, int start_pos);
void    Print_Array_HEX_FW(FILE* fp, int* arr, int line_len_bits, int line_num, int start_pos, int dummy_bits);
void    Print_Array_HEX_Fill_F2(FILE* fp, int* arr, int data_len, int line_width);
int     Convert_Binary_Hex_FW(int* arr, int offset, int kk);
int     Convert_Binary_Hex_FW2(int* arr, int offset, int line_len_bits, int kk);
void    Convert_Hex_Binary_FW(char hex, int* arr, int offset, int kk);

#endif