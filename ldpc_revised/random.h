#ifndef ECCTG_RANDOM_H
#define ECCTG_RANDOM_H

#include "common.h"

//======================================
// Random generator
//======================================

#define IM1 2147483563
#define IM2 2147483399
#define AM (1.0 / IM1)
#define IMM1 (IM1 - 1)
#define IA1 40014
#define IA2 40692
#define IQ1 53668
#define IQ2 52774
#define IR1 12211
#define IR2 3791
#define NTAB 32
#define NDIV (1 + IMM1 / NTAB)
#define EPS 1.2e-7
#define RNMX (1.0 - EPS)

void    Set_Random_Seed_xor25(int v);
void    Set_Random_Seed(unsigned int * s);
void    Get_Random_Seed(unsigned int * s);
void    Print_Seed(FILE * fp_uncor_seed, int uncor_type, char * filename_uncor_seed, unsigned int * current_seed);
int     Read_Seed(FILE * fp_uncor_seed, unsigned int * current_seed);
int     Read_Uncor_Seed_Format(FILE * fp_uncor_seed);
#ifdef __AUTO_LLR_OPT__
void    Print_Init_Seed(FILE* fp_uncor_seed, int uncor_type, char* filename_uncor_seed, unsigned int* current_seed);
#endif

double  ran2(int seed_ran2, int reset);
double  Gaussian_xor25(double a, double d);
double  xor_r25(unsigned int* a);
unsigned int xor_r25_u32(unsigned int* a);  // 정수 경로 — double 왕복 없이 상태 갱신 + w 반환 (5-6)
void    rand_msg_xor25(int *msg, int msglen);
void    rand_sel_ep(int *err_position, int len_max, int n_err_len, int type);
void    Make_Msg_TV(int *msg, int msglen, int input_index, int type);

unsigned char rand_int(void);
int Read_Uncor_Vector_Format(int N, FILE *, int *uncor_input);
void Convert_Hex_Bin(char hex, int * arr);
void Reverse_Arr(int * arr, int num);

#endif
