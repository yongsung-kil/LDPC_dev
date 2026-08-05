#ifndef ECCTG_TV_DEC_H
#define ECCTG_TV_DEC_H

#include "common.h"
#include "ecc_data.h"

//======================================
// TV for Decoder (input / output)
//======================================
class TV_Dec
{
public:
    TV_Dec();
    ~TV_Dec();
public:
    void    Set_Param(ECC_INFO* ecc_info, PCM* pcm, PARAM_DEC * param);
    void    Set_TV_idx(int idx, int sub_idx);
    void    Open();
    void    Close();
    void    Print_TV_Dec_In(int *i_HD_input, int *i_SD_input, int *i_CC_input, int * i_CD_input, int print_cw, int print_noPS);
    void    Print_TV_Dec_Out(int *cwc, int * i_HD_input, int CRC_flag, int print_cw, int print_noPS, int print_noS);
    void    Print_Empty_Line(int in, int out, int out_noPS);
private:
    void    Set_Filename();
private:
    PARAM_DEC * m_param_dec;
    ECC_INFO*   m_ecc_info;
    PCM*        m_PCM;
    int         m_TV_idx;
    int         m_TV_sub_idx;
    int         m_bits_per_line;
    char    m_str_DEC_IN_HD[LEN_FILENAME];
    char    m_str_DEC_IN_HD_noPS[LEN_FILENAME];
    char    m_str_DEC_OUT[LEN_FILENAME];
    char    m_str_DEC_OUT_noPS[LEN_FILENAME];
    char    m_str_DEC_OUT_noS[LEN_FILENAME];
    char    m_str_DECIN_2SD[LEN_FILENAME];
    char    m_str_DECIN_2SD_noPS[LEN_FILENAME];
    char    m_str_DECIN_3SD[LEN_FILENAME];
    char    m_str_DECIN_3SD_noPS[LEN_FILENAME];
    char    m_str_DECIN_CD[LEN_FILENAME];
    char    m_str_DECIN_CD_noPS[LEN_FILENAME];
    char    m_str_COR_SGN[LEN_FILENAME];
    char    m_str_COR_SGN_noPS[LEN_FILENAME];

    FILE *  m_fp_in;
    FILE *  m_fp_in_noPS;
    FILE *  m_fp_out;
    FILE *  m_fp_out_noS;
    FILE *  m_fp_out_noPS;
    FILE *  m_fp_in_2SD;
    FILE *  m_fp_in_2SD_noPS;
    FILE *  m_fp_in_3SD;
    FILE *  m_fp_in_3SD_noPS;
    FILE *  m_fp_in_COR_SGN;
    FILE *  m_fp_in_COR_SGN_noPS;
};

#endif
