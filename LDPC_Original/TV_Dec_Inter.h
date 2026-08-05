#ifndef ECCTG_TV_DEC_INTER_H
#define ECCTG_TV_DEC_INTER_H

#include "common.h"
#include "ecc_data.h"

// TV for Decoder (Intermediate)

class TV_Dec_Inter
{
public:
    TV_Dec_Inter();
    ~TV_Dec_Inter();
private:
    void Set_Filename();
public:
    void Set_Param(ECC_INFO* ecc_info, PARAM_DEC * param, PCM* pcm);
    void Set_TV_idx(int idx, int sub_idx);
    void Open();
    void Close();

    void Print_TV_check_sum(int ** Check_REG, int * Syndrome, int pre_up, int mn, int jj);
    void Print_TV_syndrome(int * Syndrome);
    void Print_TV_syndrome_intermediate(int* Syndrome);
    void Print_TV_one_cnt_BLK(int * i_HD_input);
    void Print_TV_str_err_cnt_BLK(int* Variable_mem, int* cwc, int* i_SD_input);
    void Print_TV_SW_CSW(int iter, int csw);
    void Print_TV_SW_CSW(int sw);
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
    void Print_TV_syndrome_intermediate_internal(int** Syndrome_internal);
    void Print_TV_punc_vote_internal(int*** Punc_vote_Mag_Row, int ***Punc_vote_Mag_Row_before_BS, int **Punc_vote_Mag, int **Punc_vote_decision);
#endif
    void Print_TV_old_sgn(int ** old_sgn, int mn, int PCRC_done, int last_col, int skip_idx);
    void Print_TV_old_sgn_HCU(int** old_sgn, int mn, int PCRC_done, int last_col, int skip_idx);
    void Print_TV_llr_out(int * llr_out, int * Variable_mem, int mn, int PCRC_done, int last_col, int skip_idx);
    void Print_TV_vtc_inp(int ** vtc_inp, int mn, int PCRC_done, int last_col, int skip_idx);
    void Print_TV_new_sgn(int ** vnu_out, int mn, int PCRC_done, int last_col, int skip_idx);
    void Print_TV_cnd_min(int * upt, int * val1, int* val2, int mn, int jj, int clk);
    void Print_TV_cwc(int * cwc, int mn, int skip_idx);
#if defined(__HALF_COL_UPDATE__)
    void Print_TV_vtc_inp_HCU(int** vtc_inp, int mn, int PCRC_done, int last_col, int skip_idx);
    void Print_TV_new_sgn_HCU(int** vnu_out_in, int** vnu_out_in_nq, int** vnu_out, int mn, int PCRC_done, int last_col, int skip_idx);
#endif

    void Print_TV_crc_flag(int CRC_flag);
    void Print_TV_iter_num(int iter_num);
    void Print_TV_info_err_cnt(int info_err_count);
    void Print_TV_strong_err_cnt(int str_err_count);
    void Print_TV_weak_cor_cnt(int weak_cor_count);
    void Print_TV_bit_cnt(int bit_counter);
    void Print_TV_flip_cnt(int flip_counter);
    void Print_TV_BF_on_flag(int BF_on_flag);
    void Print_TV_cfp_flag_endl();
    void Print_TV_iter_endl(int mn);
    void Print_TV_min_pos(int * min_pos, int mn);

#if defined(__FULL_CRC__)
    void Print_TV_full_crc(int* crc_dec_LFSR_final, int mn);
    void Print_TV_full_crc_internal(int** crc_dec_LFSR_internal, int mn);
#else
    void Print_TV_PCRC(int* crc_in, int* crc1, int* crc2, int* crc3, int* crc4, int mn, int jj);
    void Print_TV_PCRC(int* crc1, int* crc2, int* crc3, int* crc4, int mn);
#endif

    void Print_TV_PCRC_Cycle_based(int* crc1, int* crc2, int* crc3, int* crc4, int mn, int jj);
    void Print_TV_PCRC_termination(int idx_PCRC_termination);
private:
    PARAM_DEC *     m_param_dec;
    ECC_INFO*       m_ecc_info;
    PCM*            m_PCM;
    int             m_TV_idx;
    int             m_TV_sub_idx;

    char hex_dec_RESULT[LEN_FILENAME];
    char hex_dec_ITR_OUT[LEN_FILENAME];
    char hex_dec_LLR_OUT[LEN_FILENAME];
    char hex_dec_LLR_OUT_SGN[LEN_FILENAME];
    char hex_dec_VNU_IN[LEN_FILENAME];
    char hex_dec_SYND[LEN_FILENAME];
    char hex_dec_SYND_INT[LEN_FILENAME];
    char hex_dec_SW_CSW[LEN_FILENAME];
    char hex_dec_ONE_CNT[LEN_FILENAME];
    char hex_dec_STR_ERR_CNT_BLK[LEN_FILENAME];
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
    char hex_dec_SYND_INT_INTERNAL[LEN_FILENAME];
    char hex_dec_PUNC_VOTE_MAG[LEN_FILENAME];
    char hex_dec_PUNC_VOTE_MAG_ROW[LEN_FILENAME];
    char hex_dec_PUNC_VOTE_DEC[LEN_FILENAME];
#endif

    char hex_dec_CSUM_SGN[LEN_FILENAME];
    char hex_dec_OLD_MAG[LEN_FILENAME];
    char hex_dec_OLD_SGN[LEN_FILENAME];
    char hex_dec_VNU_OUT[LEN_FILENAME];
    char hex_dec_MIN_UPT[LEN_FILENAME];
    char hex_dec_MIN_VAL[LEN_FILENAME];
    char hex_dec_MIN_VAL2[LEN_FILENAME];
    char hex_dec_FULL_CRC[LEN_FILENAME];
    char hex_dec_FULL_CRC_INT[LEN_FILENAME];
    char hex_dec_CSUM_SGN_CYCLE[LEN_FILENAME];
    char hex_dec_MIN_POS[LEN_FILENAME];

    char hex_dec_PCRC_T4[LEN_FILENAME];
    char hex_dec_PCRC_T4_in_last_column[LEN_FILENAME];

#if defined(__HALF_COL_UPDATE__)
    char hex_dec_VNU_IN_HCU[LEN_FILENAME];
    char hex_dec_VNU_OUT_HCU[LEN_FILENAME];
    char hex_dec_VNU_OUT_HCU_in_mag[LEN_FILENAME];
    char hex_dec_VNU_OUT_HCU_in_sgn[LEN_FILENAME];
    char hex_dec_VNU_OUT_HCU_in_mag_nq[LEN_FILENAME];
    char hex_dec_VNU_OUT_HCU_in_sgn_nq[LEN_FILENAME];
    char hex_dec_OLD_SGN_HCU[LEN_FILENAME];
#endif

    FILE * fp_RESULT;       //
    FILE * fp_ITR_OUT;
    FILE * fp_LLR_OUT;
    FILE * fp_LLR_OUT_SGN;
    FILE * fp_VNU_IN;       //
    FILE * fp_VNU_OUT;

    FILE * fp_SYND;         // Syndrome
    FILE * fp_SYND_INT;     // Syndrome_intermediate
    FILE * fp_SW_CSW;
    FILE * fp_ONE_CNT;
    FILE * fp_STR_ERR_BLK_CNT;
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
    FILE* fp_SYND_INT_INTERNAL;     // Syndrome_intermediate internal
    FILE* fp_PUNC_VOTE_MAG;
    FILE* fp_PUNC_VOTE_MAG_ROW;
    FILE* fp_PUNC_VOTE_DEC;
#endif

    FILE * fp_CSUM_SGN;             //
    FILE * fp_CSUM_SGN_CYCLE;       //
    FILE * fp_OLD_MAG;
    FILE * fp_OLD_SGN;
    FILE * fp_MIN_UPT;

    FILE * fp_MIN_VAL;              //
    FILE * fp_MIN_VAL2;             //
#if defined(__FULL_CRC__)
    FILE * fp_FULL_CRC;
    FILE* fp_FULL_CRC_INT;
#else
    FILE* fp_PCRC_T4;
    FILE* fp_PCRC_T4_in_last_column;
#endif

    FILE * fp_MIN_POS;

#if defined(__HALF_COL_UPDATE__)
    FILE* fp_VNU_IN_HCU;
    FILE* fp_VNU_OUT_HCU;
    FILE* fp_VNU_OUT_HCU_in_mag;
    FILE* fp_VNU_OUT_HCU_in_sgn;
    FILE* fp_VNU_OUT_HCU_in_mag_nq;
    FILE* fp_VNU_OUT_HCU_in_sgn_nq;
    FILE* fp_OLD_SGN_HCU;
    
    int HCU_start;
    int HCU_end;
    #endif
};

#endif
