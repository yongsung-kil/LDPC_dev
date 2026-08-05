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
private:
    PCM*    m_PCM;
    int*    z_mem_shift;
    int**   P;
    int*    Parity;
};

#endif
