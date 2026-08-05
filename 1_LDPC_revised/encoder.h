#ifndef ECCTG_ENCODER_H
#define ECCTG_ENCODER_H

#include "ecc_data.h"
//#include "xcp_enc.h"

//======================================
// Prime ECC encoder
//======================================

class Encoder
{
public:
    Encoder();
    ~Encoder();
public:
    void    Init_Enc(PCM* pcm);
    void    LDPC_encoder_4KB(int* Codeword, int* Msg);
    void    LDPC_encoder_4KB(int* Codeword, int* Msg, int** Parity_inter);
private:
    void    LDPC_encoder_dual_diagonal(int* Codeword, int* Msg, int** PCM, int NumColBlk, int NumRowBlk, int zsb);
    void    LDPC_encoder_dual_diagonal(int* Codeword, int* Msg, int** Parity_inter, int **PCM, int NumColBlk, int NumRowBlk, int zsb);
    void    Column_Reordering_Dual_Update(int* Codeword, int NumColBlk, int NumRowBlk, int zsb);
    void    Generate_PCM_encoding(int **PCM_dec, int **PCM_enc, int NumColBlk, int NumRowBlk, int shuffled_dual_diag);
    void    Alloc_Enc();
    void    Release_Enc();
    void    Build_P_All();
private:
    PCM*    m_PCM;
    int*    z_mem_shift;
    int***  P_all;      // [kb][z_sb][z_sb] column별 P 행렬 사전 계산 (PCM_b_enc 기반, 시뮬레이션 중 불변)
    int*    Parity;
};

#endif
