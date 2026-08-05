#ifndef ECCTG_INPUT_H
#define ECCTG_INPUT_H

#include "common.h"
#include "ecc_data.h"

int     Get_Sector_Num(FILE * fp, ECC_INFO* info, PCM* pcm);
int     Get_DIN_noPS(FILE * fp, ECC_INFO* info, PCM* pcm, int* hd_in);
int     Get_MSG_noS(FILE * fp, ECC_INFO* info, PCM* pcm, int * msg);
int     Get_Char_to_Hex(char c);

#endif
