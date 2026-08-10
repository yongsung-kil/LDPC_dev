#ifndef ECCTG_CHANNEL_H
#define ECCTG_CHANNEL_H

#include "common.h"
#include <math.h>

//======================================
// AWGN Channel (Gaussian Model)
//======================================

#define M_PI_m  3.141592654

void    Set_R_Offset(int init_n);
void    Set_LLR_Th(double var);
void    Get_Mag_2SD(double Lq_ini_m, int * sd);
void    Get_Mag_3SD(double Lq_ini_m, int * sd, int * cc);
void    Get_Mag_1_5SD(double Lq_ini, int * hd, int * sd);

double  qfunc_inv(double p);
double  SNR_from_RBER(double p);
double  dev_from_RBER(double p);
double  Q_fn(double arg);
double  erf_m(double x);
double  erfc_m(double x);

#endif
