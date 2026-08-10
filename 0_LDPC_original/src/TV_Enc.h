#ifndef ECCTG_TV_ENC_H
#define ECCTG_TV_ENC_H

#include "common.h"
#include "ecc_data.h"

//======================================
// TV for Encoder (input / output)
//======================================
class TV_Enc
{
public:
    TV_Enc();
    ~TV_Enc();
public:
    void    Set_Param(ECC_INFO * ecc_info, PCM * pcm);
    void    Set_TV_idx(int idx);
    void    Open();
    void    Close();
    void    Print_TV_Enc_In(int * data);
    void    Print_TV_Enc_Out(int * data, int print_cw, int print_noPS);
    void    Print_Empty_Line(int in, int out, int out_noPS);
#if defined(__ENC_TV_INTER_DEBUG__)
    void    Print_TV_Enc_Inter(int** data);
#endif

private:
    void    Set_Filename();
private:
    ECC_INFO *  m_ecc_info;
    PCM*        m_PCM;
    char    m_str_ENC_IN[LEN_FILENAME];
    char    m_str_ENC_OUT[LEN_FILENAME];
    char    m_str_ENC_OUT_noPS[LEN_FILENAME];
    FILE *  m_fp_in;
    FILE *  m_fp_out;
    FILE *  m_fp_out_noPS;
#if defined(__ENC_TV_INTER_DEBUG__)
    char    m_str_ENC_INTER[LEN_FILENAME];
    FILE*   m_fp_inter;
#endif
    int     m_TV_idx;
    int     m_bits_per_line;
};

#endif
