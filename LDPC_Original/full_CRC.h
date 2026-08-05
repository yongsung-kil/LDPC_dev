#ifndef ECCTG_FULL_CRC_H
#define ECCTG_FULL_CRC_H

#include "common.h"

//======================================
// Full CRC
//======================================

#define ZSB_CRC             64

void    CRC_encoder(int *user_data, int number_of_info_block, int ShortenedBit);
void    CRC_decoder(int *codeword, int number_of_code_block, int *success_flag, int *CRC_dec_LFSR_final, int ShortenedBit);
void    CRC_decoder(int *codeword, int number_of_code_block, int *success_flag, int *CRC_dec_LFSR_final, int **CRC_dec_LFSR_internal, int ShortenedBit);
void    GEN_CRC80(int *crc80, int *crc80_ply, int *crc80_init, int **msg, int n_msg, int zsb);
void    GEN_CRC80(int **crc80_internal, int *crc80, int *crc80_ply, int *crc80_init, int **msg, int n_msg, int zsb);
void    CRC_LFSR(int *crc, int m, int *crc_ply, int n_ply);

#endif
