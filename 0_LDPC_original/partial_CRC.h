#ifndef ECCTG_PARTIAL_CRC_H
#define ECCTG_PARTIAL_CRC_H

#include "common.h"

//======================================
// Partial CRC
//======================================

void    partial_crc_HW_T4(int *dec_d, int *lfsr, int column_number, int ShortenedBit, int* idxTermination);

void    division_DEX(int *div_in, int *div_r_255);
void    division_REX(int *div_in, int *div_r_335);
void    division_REX_Last_Col_Shortened_18Byte(int *div_in, int *div_r_191);
void    division_REX_Last_Col_Shortened_00Byte(int *div_in, int *div_r_335);
void    division_REX_Last_Col_Shortened_16Byte(int *div_in, int *div_r_207);
void    division_REX_Last_Col_Shortened_12Byte(int *div_in, int *div_r_239);

/* Pablo Layout 512B, Meta 32 Byte */
void    division_TP1_Shortened_18Byte(int *div_in, int *div_r_25023);
void    division_TP2_Shortened_18Byte(int *div_in, int *div_r_16575);
void    division_TP3_Shortened_18Byte(int *div_in, int *div_r_8383);

/* Elpis Layout Meta 16B + Ex 28*/
//void division_TP1_Shortened_00Byte(int *div_in, int *div_r_25107);
//void division_TP2_Shortened_00Byte(int *div_in, int *div_r_16719);
//void division_TP3_Shortened_00Byte(int *div_in, int *div_r_8527);

/*Prime ECC 1.3*/
void    division_TP1_Shortened_00Byte(int *div_in, int *div_r_24399);
void    division_TP2_Shortened_00Byte(int *div_in, int *div_r_16719);
void    division_TP3_Shortened_00Byte(int *div_in, int *div_r_8527);
/* Solvit Layout 1 */
void    division_TP1_Shortened_16Byte(int *div_in, int *div_r_25039);
void    division_TP2_Shortened_16Byte(int *div_in, int *div_r_16591);
void    division_TP3_Shortened_16Byte(int *div_in, int *div_r_8399);
/* Solvit Layout 2 */
void    division_TP1_Shortened_12Byte(int *div_in, int *div_r_25071);
void    division_TP2_Shortened_12Byte(int *div_in, int *div_r_16623);
void    division_TP3_Shortened_12Byte(int *div_in, int *div_r_8431);

#endif
