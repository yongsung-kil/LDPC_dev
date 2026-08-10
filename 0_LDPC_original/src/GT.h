#ifndef ECCTG_GT_H
#define ECCTG_GT_H

#include "common.h"
#include "ecc_data.h"

void        Make_GT_HW(FILE * FILE_MUX, PCM * pcm);
void        Release_GT(PCM * pcm);
int         Get_Sel_Signal_In_MUX(int * ar, int row_idx);
int         Get_Row_Index_In_MUX(int * ar, int row_num, int sel_signal);
int         Get_Empty_Sel_Signal_In_MUX(int * ar, int sel_signal_default, int row_num, int * selected, int mux_name);

#endif
