#include "TV_Dec_Inter.h"
//================================================
// ������
//================================================
TV_Dec_Inter::TV_Dec_Inter()
{
    m_param_dec = NULL;
    m_ecc_info = NULL;
    m_PCM = NULL;
    fp_RESULT = NULL;
    fp_ITR_OUT = NULL;
    fp_LLR_OUT = NULL;
    fp_LLR_OUT_SGN = NULL;
    fp_VNU_IN = NULL;
    fp_SYND = NULL;
    fp_SYND_INT = NULL;
    fp_SW_CSW = NULL;
    fp_ONE_CNT = NULL;
    fp_STR_ERR_BLK_CNT = NULL;
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
    fp_SYND_INT_INTERNAL = NULL;
    fp_PUNC_VOTE_MAG = NULL;
    fp_PUNC_VOTE_MAG_ROW = NULL;
    fp_PUNC_VOTE_DEC = NULL;
#endif
    fp_CSUM_SGN = NULL;
    fp_OLD_MAG = NULL;
    fp_OLD_SGN = NULL;
    fp_VNU_OUT = NULL;
    fp_MIN_UPT = NULL;
    fp_MIN_VAL = NULL;
    fp_MIN_VAL2 = NULL;
#if defined(__FULL_CRC__)
    fp_FULL_CRC = NULL;
    fp_FULL_CRC_INT = NULL;
#else
    fp_PCRC_T4 = NULL;
    fp_PCRC_T4_in_last_column = NULL;
#endif
    fp_CSUM_SGN_CYCLE = NULL;
    fp_MIN_POS = NULL;
#if defined(__HALF_COL_UPDATE__)
    fp_VNU_IN_HCU = NULL;
    fp_VNU_OUT_HCU = NULL;
    fp_VNU_OUT_HCU_in_sgn = NULL;
    fp_VNU_OUT_HCU_in_mag = NULL;
    fp_VNU_OUT_HCU_in_sgn_nq = NULL;
    fp_VNU_OUT_HCU_in_mag_nq = NULL;
    fp_OLD_SGN_HCU = NULL;
#endif
}
//================================================
// ������
//================================================
TV_Dec_Inter::~TV_Dec_Inter()
{}
//================================================
// ������ decoder parameter ��������
//================================================
void TV_Dec_Inter::Set_Param(ECC_INFO* ecc_info, PARAM_DEC * param, PCM* pcm)
{
    m_ecc_info = ecc_info;
    m_param_dec = param;
    m_PCM = pcm;
#ifdef __HALF_COL_UPDATE_
    HCU_start = m_PCM->N_b - m_PCM->M_b - m_PCM->punct_col_num;
    HCU_end = m_PCM->N_b - m_PCM->M_b - 1;
#endif // #ifdef __HALF_COL_UPDATE_
}
//================================================
// TV ������ ��������
//================================================
void TV_Dec_Inter::Set_TV_idx(int idx, int sub_idx)
{
    m_TV_idx = idx;
    m_TV_sub_idx = sub_idx;
}
//================================================
// TV ������ ���� ��������
//================================================
void TV_Dec_Inter::Set_Filename()
{
    memset(hex_dec_RESULT, LEN_FILENAME, 0);
    memset(hex_dec_ITR_OUT, LEN_FILENAME, 0);
    memset(hex_dec_LLR_OUT, LEN_FILENAME, 0);
    memset(hex_dec_LLR_OUT_SGN, LEN_FILENAME, 0);
    memset(hex_dec_VNU_IN, LEN_FILENAME, 0);
    memset(hex_dec_SYND, LEN_FILENAME, 0);
    memset(hex_dec_SYND_INT, LEN_FILENAME, 0);
    memset(hex_dec_SW_CSW, LEN_FILENAME, 0);
    memset(hex_dec_ONE_CNT, LEN_FILENAME, 0);
    memset(hex_dec_STR_ERR_CNT_BLK, LEN_FILENAME, 0);
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
    memset(hex_dec_SYND_INT_INTERNAL, LEN_FILENAME, 0);
    memset(hex_dec_PUNC_VOTE_MAG, LEN_FILENAME, 0);
    memset(hex_dec_PUNC_VOTE_MAG_ROW, LEN_FILENAME, 0);
    memset(hex_dec_PUNC_VOTE_DEC, LEN_FILENAME, 0);
#endif
    memset(hex_dec_CSUM_SGN, LEN_FILENAME, 0);
    memset(hex_dec_OLD_MAG, LEN_FILENAME, 0);
    memset(hex_dec_OLD_SGN, LEN_FILENAME, 0);
    memset(hex_dec_VNU_OUT, LEN_FILENAME, 0);
    memset(hex_dec_MIN_UPT, LEN_FILENAME, 0);
    memset(hex_dec_MIN_VAL, LEN_FILENAME, 0);
    memset(hex_dec_MIN_VAL2, LEN_FILENAME, 0);
#if defined(__FULL_CRC__)
    memset(hex_dec_FULL_CRC, LEN_FILENAME, 0);
    memset(hex_dec_FULL_CRC_INT, LEN_FILENAME, 0);
#else
    memset(hex_dec_PCRC_T4, LEN_FILENAME, 0);
    memset(hex_dec_PCRC_T4_in_last_column, LEN_FILENAME, 0);
#endif
    memset(hex_dec_CSUM_SGN_CYCLE, LEN_FILENAME, 0);
    memset(hex_dec_MIN_POS, LEN_FILENAME, 0);
#if defined(__HALF_COL_UPDATE__)
    memset(hex_dec_VNU_IN_HCU, LEN_FILENAME, 0);
    memset(hex_dec_VNU_OUT_HCU, LEN_FILENAME, 0);
    memset(hex_dec_VNU_OUT_HCU_in_mag, LEN_FILENAME, 0);
    memset(hex_dec_VNU_OUT_HCU_in_sgn, LEN_FILENAME, 0);
    memset(hex_dec_VNU_OUT_HCU_in_mag_nq, LEN_FILENAME, 0);
    memset(hex_dec_VNU_OUT_HCU_in_sgn_nq, LEN_FILENAME, 0);
    memset(hex_dec_OLD_SGN_HCU, LEN_FILENAME, 0);
#endif
#if defined (__WIN_OS__)
    if (EMPTY == m_TV_sub_idx) {
        sprintf(hex_dec_RESULT, "output\\C_TEST%04d_RESULT.dat", m_TV_idx);
        sprintf(hex_dec_ITR_OUT, "output\\C_TEST%04d_ITR_OUT.dat", m_TV_idx);
        sprintf(hex_dec_LLR_OUT, "output\\C_TEST%04d_LLR_OUT.dat", m_TV_idx);
        sprintf(hex_dec_LLR_OUT_SGN, "output\\C_TEST%04d_LLR_OUT_SGN.dat", m_TV_idx);
        sprintf(hex_dec_VNU_IN, "output\\C_TEST%04d_VNU_IN.dat", m_TV_idx);
#if defined(__HALF_COL_UPDATE__)
        sprintf(hex_dec_VNU_IN_HCU, "output\\C_TEST%04d_VNU_IN_HCU.dat", m_TV_idx);
#endif
        sprintf(hex_dec_SYND, "output\\C_TEST%04d_SYND.dat", m_TV_idx);
        sprintf(hex_dec_SYND_INT, "output\\C_TEST%04d_SYND_INT.dat", m_TV_idx);
        sprintf(hex_dec_SW_CSW, "output\\C_TEST%04d_SW_CSW.dat", m_TV_idx);
        sprintf(hex_dec_ONE_CNT, "output\\C_TEST%04d_ONE_CNT_BLK.dat", m_TV_idx);
        sprintf(hex_dec_STR_ERR_CNT_BLK, "output\\C_TEST%04d_STR_ERR_CNT_BLK.dat", m_TV_idx);
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
        sprintf(hex_dec_SYND_INT_INTERNAL, "output\\C_TEST%04d_SYND_INT_INTERNAL.dat", m_TV_idx);
        sprintf(hex_dec_PUNC_VOTE_MAG, "output\\C_TEST%04d_PUNC_VOTE_MAG.dat", m_TV_idx);
        sprintf(hex_dec_PUNC_VOTE_MAG_ROW, "output\\C_TEST%04d_PUNC_VOTE_MAG_ROW.dat", m_TV_idx);
        sprintf(hex_dec_PUNC_VOTE_DEC, "output\\C_TEST%04d_PUNC_VOTE_DEC.dat", m_TV_idx);
#endif
        sprintf(hex_dec_CSUM_SGN, "output\\C_TEST%04d_CSUM_SGN.dat", m_TV_idx);
        sprintf(hex_dec_OLD_MAG, "output\\C_TEST%04d_OLD_MAG.dat", m_TV_idx);
        sprintf(hex_dec_OLD_SGN, "output\\C_TEST%04d_OLD_SGN.dat", m_TV_idx);
#if defined(__HALF_COL_UPDATE__)
        sprintf(hex_dec_OLD_SGN_HCU, "output\\C_TEST%04d_OLD_SGN_HCU.dat", m_TV_idx);
        sprintf(hex_dec_VNU_OUT_HCU, "output\\C_TEST%04d_VNU_OUT_HCU.dat", m_TV_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_mag, "output\\C_TEST%04d_VNU_OUT_HCU_in_mag.dat", m_TV_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_sgn, "output\\C_TEST%04d_VNU_OUT_HCU_in_sgn.dat", m_TV_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_mag_nq, "output\\C_TEST%04d_VNU_OUT_HCU_in_mag_nq.dat", m_TV_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_sgn_nq, "output\\C_TEST%04d_VNU_OUT_HCU_in_sgn_nq.dat", m_TV_idx);
#endif
        sprintf(hex_dec_VNU_OUT, "output\\C_TEST%04d_VNU_OUT.dat", m_TV_idx);
        sprintf(hex_dec_MIN_UPT, "output\\C_TEST%04d_MIN_UPT.dat", m_TV_idx);
        sprintf(hex_dec_MIN_VAL, "output\\C_TEST%04d_MIN_VAL.dat", m_TV_idx);
        sprintf(hex_dec_MIN_VAL2, "output\\C_TEST%04d_MIN_VAL2.dat", m_TV_idx);
#if defined(__FULL_CRC__)
        sprintf(hex_dec_FULL_CRC, "output\\C_TEST%04d_FULL_CRC.dat", m_TV_idx);
        sprintf(hex_dec_FULL_CRC_INT, "output\\C_TEST%04d_FULL_CRC_INT.dat", m_TV_idx);
#else
        sprintf(hex_dec_PCRC_T4, "output\\C_TEST%04d_PCRC_T4.dat", m_TV_idx);
        sprintf(hex_dec_PCRC_T4_in_last_column, "output\\C_TEST%04d_PCRC_T4_in_last_column.dat", m_TV_idx);
#endif
        sprintf(hex_dec_CSUM_SGN_CYCLE, "output\\C_TEST%04d_CSUM_SGN_CYCLE.dat", m_TV_idx);
        sprintf(hex_dec_MIN_POS, "output\\C_TEST%04d_MIN_POS.dat", m_TV_idx);
    }
    else {
        sprintf(hex_dec_RESULT, "output\\C_TEST%04d_%d_RESULT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_ITR_OUT, "output\\C_TEST%04d_%d_ITR_OUT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_LLR_OUT, "output\\C_TEST%04d_%d_LLR_OUT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_LLR_OUT_SGN, "output\\C_TEST%04d_%d_LLR_OUT_SGN.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_IN, "output\\C_TEST%04d_%d_VNU_IN.dat", m_TV_idx, m_TV_sub_idx);
#if defined(__HALF_COL_UPDATE__)
        sprintf(hex_dec_VNU_IN_HCU, "output\\C_TEST%04d_%d_VNU_IN_HCU.dat", m_TV_idx, m_TV_sub_idx);
#endif
        sprintf(hex_dec_SYND, "output\\C_TEST%04d_%d_SYND.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_SYND_INT, "output\\C_TEST%04d_%d_SYND_INT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_SW_CSW, "output\\C_TEST%04d_%d_SW_CSW.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_ONE_CNT, "output\\C_TEST%04d_%d_ONE_CNT_BLK.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_STR_ERR_CNT_BLK, "output\\C_TEST%04d_%d_STR_ERR_CNT_BLK.dat", m_TV_idx, m_TV_sub_idx);
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
        sprintf(hex_dec_SYND_INT_INTERNAL, "output\\C_TEST%04d_%d_SYND_INT_INTERNAL.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_PUNC_VOTE_MAG, "output\\C_TEST%04d_%d_PUNC_VOTE_MAG.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_PUNC_VOTE_MAG_ROW, "output\\C_TEST%04d_%d_PUNC_VOTE_MAG_ROW.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_PUNC_VOTE_DEC, "output\\C_TEST%04d_%d_PUNC_VOTE_DEC.dat", m_TV_idx, m_TV_sub_idx);
#endif
        sprintf(hex_dec_CSUM_SGN, "output\\C_TEST%04d_%d_CSUM_SGN.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_OLD_MAG, "output\\C_TEST%04d_%d_OLD_MAG.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_OLD_SGN, "output\\C_TEST%04d_%d_OLD_SGN.dat", m_TV_idx, m_TV_sub_idx);
#if defined(__HALF_COL_UPDATE__)
        sprintf(hex_dec_OLD_SGN_HCU, "output\\C_TEST%04d_%d_OLD_SGN_HCU.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_OUT_HCU, "output\\C_TEST%04d_%d_VNU_OUT_HCU.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_mag, "output\\C_TEST%04d_%d_VNU_OUT_HCU_in_mag.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_sgn, "output\\C_TEST%04d_%d_VNU_OUT_HCU_in_sgn.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_mag_nq, "output\\C_TEST%04d_%d_VNU_OUT_HCU_in_mag_nq.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_sgn_nq, "output\\C_TEST%04d_%d_VNU_OUT_HCU_in_sgn_nq.dat", m_TV_idx, m_TV_sub_idx);
#endif
        sprintf(hex_dec_VNU_OUT, "output\\C_TEST%04d_%d_VNU_OUT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_MIN_UPT, "output\\C_TEST%04d_%d_MIN_UPT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_MIN_VAL, "output\\C_TEST%04d_%d_MIN_VAL.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_MIN_VAL2, "output\\C_TEST%04d_%d_MIN_VAL2.dat", m_TV_idx, m_TV_sub_idx);
#if defined(__FULL_CRC__)
        sprintf(hex_dec_FULL_CRC, "output\\C_TEST%04d_%d_FULL_CRC.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_FULL_CRC_INT, "output\\C_TEST%04d_%d_FULL_CRC_INT.dat", m_TV_idx, m_TV_sub_idx);
#else
        sprintf(hex_dec_PCRC_T4, "output\\C_TEST%04d_%d_PCRC_T4.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_PCRC_T4_in_last_column, "output\\C_TEST%04d_%d_PCRC_T4_in_last_column.dat", m_TV_idx, m_TV_sub_idx);
#endif
        sprintf(hex_dec_CSUM_SGN_CYCLE, "output\\C_TEST%04d_%d_CSUM_SGN_CYCLE.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_MIN_POS, "output\\C_TEST%04d_%d_MIN_POS.dat", m_TV_idx, m_TV_sub_idx);
    }
#else
    if (EMPTY == m_TV_sub_idx) {
        sprintf(hex_dec_RESULT, "./output/C_TEST%04d_RESULT.dat", m_TV_idx);
        sprintf(hex_dec_ITR_OUT, "./output/C_TEST%04d_ITR_OUT.dat", m_TV_idx);
        sprintf(hex_dec_LLR_OUT, "./output/C_TEST%04d_LLR_OUT.dat", m_TV_idx);
        sprintf(hex_dec_LLR_OUT_SGN, "./output/C_TEST%04d_LLR_OUT_SGN.dat", m_TV_idx);
        sprintf(hex_dec_VNU_IN, "./output/C_TEST%04d_VNU_IN.dat", m_TV_idx);
#if defined(__HALF_COL_UPDATE__)
        sprintf(hex_dec_VNU_IN_HCU, "./output/C_TEST%04d_VNU_IN_HCU.dat", m_TV_idx);
#endif
        sprintf(hex_dec_SYND, "./output/C_TEST%04d_SYND.dat", m_TV_idx);
        sprintf(hex_dec_SYND_INT, "./output/C_TEST%04d_SYND_INT.dat", m_TV_idx);
        sprintf(hex_dec_SW_CSW, "./output/C_TEST%04d_SW_CSW.dat", m_TV_idx);
        sprintf(hex_dec_ONE_CNT, "./output/C_TEST%04d_ONE_CNT_BLK.dat", m_TV_idx);
        sprintf(hex_dec_STR_ERR_CNT_BLK, "./output/C_TEST%04d_STR_ERR_CNT_BLK.dat", m_TV_idx);
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
        sprintf(hex_dec_SYND_INT_INTERNAL, "./output/C_TEST%04d_SYND_INT_INTERNAL.dat", m_TV_idx);
        sprintf(hex_dec_PUNC_VOTE_MAG, "./output/C_TEST%04d_PUNC_VOTE_MAG.dat", m_TV_idx);
        sprintf(hex_dec_PUNC_VOTE_MAG_ROW, "./output/C_TEST%04d_PUNC_VOTE_MAG_ROW.dat", m_TV_idx);
        sprintf(hex_dec_PUNC_VOTE_DEC, "./output/C_TEST%04d_PUNC_VOTE_DEC.dat", m_TV_idx);
#endif
        sprintf(hex_dec_CSUM_SGN, "./output/C_TEST%04d_CSUM_SGN.dat", m_TV_idx);
        sprintf(hex_dec_OLD_MAG, "./output/C_TEST%04d_OLD_MAG.dat", m_TV_idx);
        sprintf(hex_dec_OLD_SGN, "./output/C_TEST%04d_OLD_SGN.dat", m_TV_idx);
#if defined(__HALF_COL_UPDATE__)
        sprintf(hex_dec_OLD_SGN_HCU, "./output/C_TEST%04d_OLD_SGN_HCU.dat", m_TV_idx);
        sprintf(hex_dec_VNU_OUT_HCU, "./output/C_TEST%04d_VNU_OUT_HCU.dat", m_TV_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_mag, "./output/C_TEST%04d_VNU_OUT_HCU_in_mag.dat", m_TV_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_sgn, "./output/C_TEST%04d_VNU_OUT_HCU_in_sgn.dat", m_TV_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_mag_nq, "./output/C_TEST%04d_VNU_OUT_HCU_in_mag_nq.dat", m_TV_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_sgn_nq, "./output/C_TEST%04d_VNU_OUT_HCU_in_sgn_nq.dat", m_TV_idx);
#endif
        sprintf(hex_dec_PCRC_T4, "./output/C_TEST%04d_PCRC_T4.dat", m_TV_idx);
        sprintf(hex_dec_PCRC_T4_in_last_column, "./output/C_TEST%04d_PCRC_T4_in_last_column.dat", m_TV_idx);
        sprintf(hex_dec_VNU_OUT, "./output/C_TEST%04d_VNU_OUT.dat", m_TV_idx);
        sprintf(hex_dec_MIN_UPT, "./output/C_TEST%04d_MIN_UPT.dat", m_TV_idx);
        sprintf(hex_dec_MIN_VAL, "./output/C_TEST%04d_MIN_VAL.dat", m_TV_idx);
        sprintf(hex_dec_MIN_VAL2, "./output/C_TEST%04d_MIN_VAL2.dat", m_TV_idx);
#if defined(__FULL_CRC__)
        sprintf(hex_dec_FULL_CRC, "./output/C_TEST%04d_FULL_CRC.dat", m_TV_idx);
        sprintf(hex_dec_FULL_CRC_INT, "./output/C_TEST%04d_FULL_CRC_INT.dat", m_TV_idx);
#else
        sprintf(hex_dec_PCRC_T4, "./output/C_TEST%04d_PCRC_T4.dat", m_TV_idx);
        sprintf(hex_dec_PCRC_T4_in_last_column, "./output/C_TEST%04d_PCRC_T4_in_last_column.dat", m_TV_idx);
#endif
        sprintf(hex_dec_CSUM_SGN_CYCLE, "./output/C_TEST%04d_CSUM_SGN_CYCLE.dat", m_TV_idx);
        sprintf(hex_dec_MIN_POS, "./output/C_TEST%04d_MIN_POS.dat", m_TV_idx);
    }
    else {
        sprintf(hex_dec_RESULT, "./output/C_TEST%04d_%d_RESULT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_ITR_OUT, "./output/C_TEST%04d_%d_ITR_OUT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_LLR_OUT, "./output/C_TEST%04d_%d_LLR_OUT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_LLR_OUT_SGN, "./output/C_TEST%04d_%d_LLR_OUT_SGN.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_IN, "./output/C_TEST%04d_%d_VNU_IN.dat", m_TV_idx, m_TV_sub_idx);
#if defined(__HALF_COL_UPDATE__)
        sprintf(hex_dec_VNU_IN_HCU, "./output/C_TEST%04d_%d_VNU_IN_HCU.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_OUT_HCU, "./output/C_TEST%04d_%d_VNU_OUT_HCU.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_mag, "./output/C_TEST%04d_%d_VNU_OUT_HCU_in_mag.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_sgn, "./output/C_TEST%04d_%d_VNU_OUT_HCU_in_sgn.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_mag_nq, "./output/C_TEST%04d_%d_VNU_OUT_HCU_in_mag_nq.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_OUT_HCU_in_sgn_nq, "./output/C_TEST%04d_%d_VNU_OUT_HCU_in_sgn_nq.dat", m_TV_idx, m_TV_sub_idx);
#endif
        sprintf(hex_dec_SYND, "./output/C_TEST%04d_%d_SYND.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_SYND_INT, "./output/C_TEST%04d_%d_SYND_INT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_SW_CSW, "./output/C_TEST%04d_%d_SW_CSW.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_ONE_CNT, "./output/C_TEST%04d_%d_ONE_CNT_BLK.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_STR_ERR_CNT_BLK, "./output/C_TEST%04d_%d_STR_ERR_CNT_BLK.dat", m_TV_idx, m_TV_sub_idx);
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
        sprintf(hex_dec_SYND_INT_INTERNAL, "./output/C_TEST%04d_%d_SYND_INT_INTERNAL.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_PUNC_VOTE_MAG, "./output/C_TEST%04d_%d_PUNC_VOTE_MAG.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_PUNC_VOTE_MAG_ROW, "./output/C_TEST%04d_%d_PUNC_VOTE_MAG_ROW.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_PUNC_VOTE_DEC, "./output/C_TEST%04d_%d_PUNC_VOTE_DEC.dat", m_TV_idx, m_TV_sub_idx);
#endif
        sprintf(hex_dec_CSUM_SGN, "./output/C_TEST%04d_%d_CSUM_SGN.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_OLD_MAG, "./output/C_TEST%04d_%d_OLD_MAG.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_OLD_SGN, "./output/C_TEST%04d_%d_OLD_SGN.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_OLD_SGN_HCU, "./output/C_TEST%04d_%d_OLD_SGN_HCU.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_PCRC_T4, "./output/C_TEST%04d_%d_PCRC_T4.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_PCRC_T4_in_last_column, "./output/C_TEST%04d_%d_PCRC_T4_in_last_column.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_VNU_OUT, "./output/C_TEST%04d_%d_VNU_OUT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_MIN_UPT, "./output/C_TEST%04d_%d_MIN_UPT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_MIN_VAL, "./output/C_TEST%04d_%d_MIN_VAL.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_MIN_VAL2, "./output/C_TEST%04d_%d_MIN_VAL2.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_FULL_CRC, "./output/C_TEST%04d_%d_FULL_CRC.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_FULL_CRC_INT, "./output/C_TEST%04d_%d_FULL_CRC_INT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_CSUM_SGN_CYCLE, "./output/C_TEST%04d_%d_CSUM_SGN_CYCLE.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(hex_dec_MIN_POS, "./output/C_TEST%04d_%d_MIN_POS.dat", m_TV_idx, m_TV_sub_idx);
    }
#endif
}
//================================================
// Open file stream
//================================================
void TV_Dec_Inter::Open()
{
    Set_Filename();
    fp_RESULT = fopen(hex_dec_RESULT, "wt");
    fp_ITR_OUT = fopen(hex_dec_ITR_OUT, "wt");
    fp_LLR_OUT = fopen(hex_dec_LLR_OUT, "wt");
    fp_LLR_OUT_SGN = fopen(hex_dec_LLR_OUT_SGN, "wt");
    fp_VNU_IN = fopen(hex_dec_VNU_IN, "wt");
    fp_SYND = fopen(hex_dec_SYND, "wt");
    fp_SYND_INT = fopen(hex_dec_SYND_INT, "wt");
    fp_SW_CSW = fopen(hex_dec_SW_CSW, "wt");
    fp_ONE_CNT = fopen(hex_dec_ONE_CNT, "wt");
    fp_STR_ERR_BLK_CNT = fopen(hex_dec_STR_ERR_CNT_BLK, "wt");
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
    fp_SYND_INT_INTERNAL = fopen(hex_dec_SYND_INT_INTERNAL, "wt");
    fp_PUNC_VOTE_MAG = fopen(hex_dec_PUNC_VOTE_MAG, "wt");
    fp_PUNC_VOTE_MAG_ROW = fopen(hex_dec_PUNC_VOTE_MAG_ROW, "wt");
    fp_PUNC_VOTE_DEC = fopen(hex_dec_PUNC_VOTE_DEC, "wt");
#endif
    fp_CSUM_SGN = fopen(hex_dec_CSUM_SGN, "wt");
    fp_OLD_SGN = fopen(hex_dec_OLD_SGN, "wt");
    fp_VNU_OUT = fopen(hex_dec_VNU_OUT, "wt");
    fp_MIN_UPT = fopen(hex_dec_MIN_UPT, "wt");
    fp_MIN_VAL = fopen(hex_dec_MIN_VAL, "wt");
    fp_MIN_VAL2 = fopen(hex_dec_MIN_VAL2, "wt");
#if defined(__FULL_CRC__)
    fp_FULL_CRC = fopen(hex_dec_FULL_CRC, "wt");
    fp_FULL_CRC_INT = fopen(hex_dec_FULL_CRC_INT, "wt");
#else
    fp_PCRC_T4 = fopen(hex_dec_PCRC_T4, "wt");
    fp_PCRC_T4_in_last_column = fopen(hex_dec_PCRC_T4_in_last_column, "wt");
#endif
    fp_CSUM_SGN_CYCLE = fopen(hex_dec_CSUM_SGN_CYCLE, "wt");
    fp_MIN_POS = fopen(hex_dec_MIN_POS, "wt");
#if defined(__HALF_COL_UPDATE__)
    fp_VNU_IN_HCU = fopen(hex_dec_VNU_IN_HCU, "wt");
    fp_VNU_OUT_HCU = fopen(hex_dec_VNU_OUT_HCU, "wt");
    fp_VNU_OUT_HCU_in_sgn = fopen(hex_dec_VNU_OUT_HCU_in_sgn, "wt");
    fp_VNU_OUT_HCU_in_mag = fopen(hex_dec_VNU_OUT_HCU_in_mag, "wt");
    fp_VNU_OUT_HCU_in_sgn_nq = fopen(hex_dec_VNU_OUT_HCU_in_sgn_nq, "wt");
    fp_VNU_OUT_HCU_in_mag_nq = fopen(hex_dec_VNU_OUT_HCU_in_mag_nq, "wt");
    fp_OLD_SGN_HCU = fopen(hex_dec_OLD_SGN_HCU, "wt");
#endif
}
//================================================
// Close file stream
//================================================
void TV_Dec_Inter::Close()
{
    fclose(fp_RESULT);
    fclose(fp_ITR_OUT);
    fclose(fp_LLR_OUT);
    fclose(fp_LLR_OUT_SGN);
    fclose(fp_VNU_IN);
#if defined(__HALF_COL_UPDATE__)
    fclose(fp_VNU_IN_HCU);
    fclose(fp_OLD_SGN_HCU);
    fclose(fp_VNU_OUT_HCU);
    fclose(fp_VNU_OUT_HCU_in_sgn);
    fclose(fp_VNU_OUT_HCU_in_mag);
    fclose(fp_VNU_OUT_HCU_in_sgn_nq);
    fclose(fp_VNU_OUT_HCU_in_mag_nq);
#endif
    fclose(fp_SYND);
    fclose(fp_SYND_INT);
    fclose(fp_SW_CSW);
    fclose(fp_ONE_CNT);
    fclose(fp_STR_ERR_BLK_CNT);
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
    fclose(fp_SYND_INT_INTERNAL);
    fclose(fp_PUNC_VOTE_MAG);
    fclose(fp_PUNC_VOTE_MAG_ROW);
    fclose(fp_PUNC_VOTE_DEC);
#endif
    fclose(fp_CSUM_SGN);
    fclose(fp_OLD_SGN);
    fclose(fp_VNU_OUT);
    fclose(fp_MIN_UPT);
    fclose(fp_MIN_VAL);
    fclose(fp_MIN_VAL2);
#if defined(__FULL_CRC__)
    fclose(fp_FULL_CRC);
    fclose(fp_FULL_CRC_INT);
#else
    fclose(fp_PCRC_T4);
    fclose(fp_PCRC_T4_in_last_column);
#endif
    fclose(fp_CSUM_SGN_CYCLE);
    fclose(fp_MIN_POS);
    fp_RESULT = NULL;
    fp_ITR_OUT = NULL;
    fp_LLR_OUT = NULL;
    fp_LLR_OUT_SGN = NULL;
    fp_VNU_IN = NULL;
#if defined(__HALF_COL_UPDATE__)
    fp_VNU_IN_HCU = NULL;
    fp_OLD_SGN_HCU = NULL;
    fp_VNU_OUT_HCU = NULL;
    fp_VNU_OUT_HCU_in_sgn = NULL;
    fp_VNU_OUT_HCU_in_mag = NULL;
    fp_VNU_OUT_HCU_in_sgn_nq = NULL;
    fp_VNU_OUT_HCU_in_mag_nq = NULL;
#endif
    fp_SYND = NULL;
    fp_SYND_INT = NULL;
    fp_SW_CSW = NULL;
    fp_ONE_CNT = NULL;
    fp_STR_ERR_BLK_CNT = NULL;
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
    fp_SYND_INT_INTERNAL = NULL;
    fp_PUNC_VOTE_MAG = NULL;
    fp_PUNC_VOTE_MAG_ROW = NULL;
    fp_PUNC_VOTE_DEC = NULL;
#endif
    fp_CSUM_SGN = NULL;
    fp_OLD_MAG = NULL;
    fp_OLD_SGN = NULL;
    fp_VNU_OUT = NULL;
    fp_MIN_UPT = NULL;
    fp_MIN_VAL = NULL;
    fp_MIN_VAL2 = NULL;
#if defined(__FULL_CRC__)
    fp_FULL_CRC = NULL;
    fp_FULL_CRC_INT = NULL;
#else
    fp_PCRC_T4 = NULL;
    fp_PCRC_T4_in_last_column = NULL;
#endif
    fp_CSUM_SGN_CYCLE = NULL;
    fp_MIN_POS = NULL;
}
//================================================
// ������
//================================================
void TV_Dec_Inter::Print_TV_iter_endl(int mn)
{
    fprintf(fp_LLR_OUT, "\n");
    fprintf(fp_LLR_OUT_SGN, "\n");
    fprintf(fp_VNU_IN, "\n");
#if defined(__HALF_COL_UPDATE__)
    fprintf(fp_VNU_IN_HCU, "\n");
    fprintf(fp_VNU_OUT_HCU, "\n");
    fprintf(fp_VNU_OUT_HCU_in_sgn, "\n");
    fprintf(fp_VNU_OUT_HCU_in_mag, "\n");
    fprintf(fp_VNU_OUT_HCU_in_sgn_nq, "\n");
    fprintf(fp_VNU_OUT_HCU_in_mag_nq, "\n");
    fprintf(fp_OLD_SGN_HCU, "\n");
#endif
    fprintf(fp_CSUM_SGN, "\n");
    fprintf(fp_VNU_OUT, "\n");
    fprintf(fp_OLD_SGN, "\n");
    fprintf(fp_MIN_UPT, "\n");
    fprintf(fp_MIN_VAL, "\n");
    fprintf(fp_MIN_VAL2, "\n");
    fprintf(fp_MIN_POS, "\n");
    // 2SD, 3SD�� HW������ iter=0������ PR�� ��P�� ������;������ ����������8�� ����, ref-c�������� iter=0������ PR������
    // TV ������n�� ������ ���� ����/�� ����������D�� ������
    if (mn > 0) fprintf(fp_CSUM_SGN_CYCLE, "\n");
}
//================================================
// Checksum ������
//================================================
void TV_Dec_Inter::Print_TV_check_sum(int ** Check_REG, int * Syndrome, int pre_up, int mn, int jj)
{
    int temp_i;
    int temp_bin4;
    int i, j;
    int z_sb = m_PCM->z_sb;
    int M_b = m_PCM->M_b;
    FILE * fp = NULL;
    if (pre_up == TRUE) { fp = fp_SYND; }
    else {
        if (CYCLE_END != jj) { fp = fp_CSUM_SGN_CYCLE; }
        else { fp = fp_CSUM_SGN; }
    }
#if defined (__ECC_TV_ITER__)
    int pos = 0;
    int * active_row = new int[M_b];
    for (i = 0; i < M_b; i++) { active_row[i] = FALSE; }
    if (CYCLE_END != jj) {
        for (i = 0; i < m_PCM->ColW[jj]; i++) { active_row[m_PCM->V_net_b[jj][i]] = TRUE; }
    }
    if (CYCLE_END == jj) { fprintf(fp, "iter: %d\n", mn); }
    else { fprintf(fp, "iter: %d\tcol: %d\n", mn, jj); }
#endif
    temp_i = 0;
    for (i = 0; i < M_b; i++) {
#if defined (__ECC_TV_ITER__)
        fprintf(fp, "row : %2d\t", i);
#endif
        if (m_PCM->ar[i] == 1) {
#if defined (__ECC_TV_ITER__)
            fprintf(fp, "active\t");
            if (active_row[pos] == TRUE) { fprintf(fp, "active\t"); }
            else { fprintf(fp, "       \t"); }
            pos++;
#endif
            for (j = 0; j < z_sb; j = j + HEX_BITS) {
                temp_bin4 = 8 * ((Check_REG[z_sb*temp_i + j][IDX_CHECK_SUM] + Syndrome[z_sb*temp_i + j]) % 2)
                          + 4 * ((Check_REG[z_sb*temp_i + j + 1][IDX_CHECK_SUM] + Syndrome[z_sb*temp_i + j + 1]) % 2)
                          + 2 * ((Check_REG[z_sb*temp_i + j + 2][IDX_CHECK_SUM] + Syndrome[z_sb*temp_i + j + 2]) % 2)
                          + 1 * ((Check_REG[z_sb*temp_i + j + 3][IDX_CHECK_SUM] + Syndrome[z_sb*temp_i + j + 3]) % 2);
                fprintf(fp, "%x", temp_bin4);
            }
            fprintf(fp, "\n");
            temp_i++;
        }
        else {
#if defined (__ECC_TV_ITER__)
            fprintf(fp, "       \t");
            fprintf(fp, "       \t");
#endif
            for (j = 0; j < z_sb; j = j + HEX_BITS) {
                fprintf(fp, "0");
            }
            fprintf(fp, "\n");
        }
    }
    if (TRUE == pre_up) {
        fprintf(fp, "\n");
    }
#if defined (__ECC_TV_ITER__)
    fprintf(fp, "\n");
    delete[] active_row;
#endif
}
//================================================
// Syndrome ������
//================================================
void TV_Dec_Inter::Print_TV_syndrome(int * Syndrome)
{
    int temp_i;
    int temp_bin4;
    int i, j;
    int z_sb = m_PCM->z_sb;
    int M_b = m_PCM->M_b;
    temp_i = 0;
    //for (i = 0; i < GT_HW_MAX_ROW; i++) {
    for (i = 0; i < M_b; i++) {
#if defined (__ECC_TV_ITER__)
        fprintf(fp_SYND, "row : %2d\t", i);
#endif
        if (m_PCM->ar[i] == 1) {
            for (j = 0; j < z_sb; j = j + HEX_BITS) {
                temp_bin4 = 8 * Syndrome[z_sb*temp_i + j]
                          + 4 * Syndrome[z_sb*temp_i + j + 1]
                          + 2 * Syndrome[z_sb*temp_i + j + 2]
                          + 1 * Syndrome[z_sb*temp_i + j + 3];
            fprintf(fp_SYND, "%x", temp_bin4);
        }
        fprintf(fp_SYND, "\n");
        temp_i++;
    }
    else {
        for (j = 0; j < z_sb; j = j + HEX_BITS) {
            fprintf(fp_SYND, "0");
        }
        fprintf(fp_SYND, "\n");
    }
  }
#if defined (__ECC_TV_ITER__)
    fprintf(fp_SYND, "\n");
#endif
}
void TV_Dec_Inter::Print_TV_str_err_cnt_BLK(int* Variable_mem, int *cwc, int* i_SD_input)
{
    int n;
    int info_length = 0;
    int str_err_BLK_acc = 0;
    int str_err_BLK = 0;
    info_length = (m_PCM->N - m_PCM->M) - m_ecc_info->shortened_bit_info_offset_end;
    // Punc Col Blk>> 127, 128 Case
    for (n = 0; n < m_PCM->N - m_PCM->M - m_ecc_info->punctured_bit_info - m_ecc_info->shortened_bit_info; n++) {
        if (Variable_mem[n] != cwc[n]) {
            if (i_SD_input[n] == 1) str_err_BLK++;
        }
    }
    fprintf(fp_STR_ERR_BLK_CNT, "%d\n", str_err_BLK);
    /*
    // Punc Col Blk>> 0, 1 Case
    for (n = 0;n < m_PCM->N_b - m_PCM->M_b - 1; n++) {
        str_err_BLK = 0;
        if (n == 0) {
            for (i = m_ecc_info->shortened_bit_info;i < m_PCM->z_sb;i++) {
                if (Variable_mem[n * m_PCM->z_sb + i] != cwc[n * m_PCM->z_sb + i]) {
                    if (i_SD_input[n * m_PCM->z_sb + i]==1) str_err_BLK++;
                }
            }
        }
        else {
            for (i = 0;i < m_PCM->z_sb;i++) {
                if (Variable_mem[n * m_PCM->z_sb + i] != cwc[n * m_PCM->z_sb + i]) {
                    if (i_SD_input[n * m_PCM->z_sb + i] == 1)    str_err_BLK++;
                }
            }
        }
        fprintf(fp_STR_ERR_BLK_CNT, "%d\n", str_err_BLK);
        str_err_BLK_acc += str_err_BLK;
    }
    n = (m_PCM->N_b - m_PCM->M_b - 1) * m_PCM->z_sb;
    str_err_BLK = 0;
    for (i = 0;i < m_PCM->z_sb - m_ecc_info->shortened_bit_info_offset_end;i++) {
        if (Variable_mem[n + i] != cwc[n + i]) {
            if (i_SD_input[n + i] == 1) str_err_BLK++;
        }
    }
    str_err_BLK_acc += str_err_BLK;
    fprintf(fp_STR_ERR_BLK_CNT, "%d\n", str_err_BLK);
    fprintf(fp_STR_ERR_BLK_CNT, "%d\n", str_err_BLK_acc);
    */
}
void TV_Dec_Inter::Print_TV_one_cnt_BLK(int* Punc_one_cnt)
{
    int n,i;
    int bit_counter;
    int bit_counter_acc = 0;
    int data_len = m_PCM->N;
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) {
        for (n = 0; n < HCU_start; n++) {
            bit_counter = 0;
            for (i = 0; i < m_PCM->z_sb; i++) {
                bit_counter += (Punc_one_cnt[n * m_PCM->z_sb + i] + 1) % 2;
            }
            fprintf(fp_ONE_CNT, "%d\n", bit_counter);
            bit_counter_acc += bit_counter;
        }
        n = HCU_start;
        bit_counter = 0;
        for (i = m_ecc_info->shortened_bit_info; i < m_PCM->z_sb; i++) {
            bit_counter += (Punc_one_cnt[n * m_PCM->z_sb + i] + 1) % 2;
        }
        fprintf(fp_ONE_CNT, "%d\n", bit_counter);
        bit_counter_acc += bit_counter;
        n = HCU_end * m_PCM->z_sb;
        bit_counter = 0;
        for (i = 0; i < m_PCM->z_sb - m_ecc_info->shortened_bit_info_offset_end; i++) {
            bit_counter += (Punc_one_cnt[n + i] + 1) % 2;
        }
        bit_counter_acc += bit_counter;
        fprintf(fp_ONE_CNT, "%d\n", bit_counter);
        fprintf(fp_ONE_CNT, "%d\n", bit_counter_acc);
        // Col Blk 0, 1 Puncturing Case
        /*
        for (n = 0;n < m_PCM->N_b - m_PCM->M_b - 1; n++) {
            bit_counter = 0;
            if (n == 0) {
                for (i = m_ecc_info->shortened_bit_info;i < m_PCM->z_sb;i++) {
                    bit_counter += (Punc_one_cnt[n * m_PCM->z_sb + i] + 1) % 2;
                }
            }
            else {
                for (i = 0;i < m_PCM->z_sb;i++) {
                    bit_counter += (Punc_one_cnt[n * m_PCM->z_sb + i] + 1) % 2;
                }
            }
            fprintf(fp_ONE_CNT, "%d\n", bit_counter);
            bit_counter_acc += bit_counter;
        }
        n = (m_PCM->N_b - m_PCM->M_b - 1) * m_PCM->z_sb;
        bit_counter = 0;
        for (i = 0;i < m_PCM->z_sb - m_ecc_info->shortened_bit_info_offset_end;i++) {
            bit_counter+= (Punc_one_cnt[n + i] + 1) % 2;
        }
        bit_counter_acc += bit_counter;
        fprintf(fp_ONE_CNT, "%d\n", bit_counter);
        fprintf(fp_ONE_CNT, "%d\n", bit_counter_acc);
        */
    }
}
//==============================================
// Syndrome >>>
//==============================================
void TV_Dec_Inter::Print_TV_syndrome_intermediate(int* Syndrome)
{
    int temp_i;
    int temp_bin4;
    int i, j;
    int z_sb = m_PCM->z_sb;
    int M_b = m_PCM->M_b;
    temp_i = 0;
    //for (i = 0; i < GT_HW_MAX_ROW; i++) {
    for (i = 0; i < M_b; i++) {
#if defined (__ECC_TV_ITER__)
        fprintf(fp_SYND_INT, "row : %2d\t", i);
#endif
        if (m_PCM->ar[i] == 1) {
            for (j = 0; j < z_sb; j = j + HEX_BITS) {
                temp_bin4 = 8 * Syndrome[z_sb * temp_i + j]
                          + 4 * Syndrome[z_sb * temp_i + j + 1]
                          + 2 * Syndrome[z_sb * temp_i + j + 2]
                          + 1 * Syndrome[z_sb * temp_i + j + 3];
                fprintf(fp_SYND_INT, "%x", temp_bin4);
            }
            fprintf(fp_SYND_INT, "\n");
            temp_i++;
        }
        else {
            for (j = 0; j < z_sb; j = j + HEX_BITS) {
                fprintf(fp_SYND_INT, "0");
            }
            fprintf(fp_SYND_INT, "\n");
        }
    }
}
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
void TV_Dec_Inter::Print_TV_syndrome_intermediate_internal(int** Syndrome_internal)
{
    int temp_bin4;
    int i, j, k;
    int z_sb = m_PCM->z_sb;
    int N_b = m_PCM->N_b;
    int M_b = m_PCM->M_b;
    for (i = 0; i < N_b; i++) {
        //for (i = 0;i < N_b-m_PCM->punct_col_num;i++) {
        for (k = 0;k < M_b;k++) {
            for (j = 0; j < z_sb; j = j + HEX_BITS) {
                temp_bin4 = 8 * Syndrome_internal[i][z_sb * k + j]
                          + 4 * Syndrome_internal[i][z_sb * k + j + 1]
                          + 2 * Syndrome_internal[i][z_sb * k + j + 2]
                          + 1 * Syndrome_internal[i][z_sb * k + j + 3];
                fprintf(fp_SYND_INT_INTERNAL, "%x", temp_bin4);
            }
            fprintf(fp_SYND_INT_INTERNAL, "\n");
        }
        fprintf(fp_SYND_INT_INTERNAL, "\n");
    }
}
void TV_Dec_Inter::Print_TV_SW_CSW(int iter, int csw)
{
    fprintf(fp_SW_CSW, "%d %d\n",iter, csw);
}
void TV_Dec_Inter::Print_TV_SW_CSW(int sw)
{
    fprintf(fp_SW_CSW, "%d\n", sw);
}
void TV_Dec_Inter::Print_TV_punc_vote_internal(int*** Punc_vote_Mag_Row, int*** Punc_vote_Mag_Row_before_BS, int** Punc_vote_Mag, int** Punc_vote_decision)
{
    int temp_bin4;
    int i, j, k;
    int z_sb = m_PCM->z_sb;
    for (i = 0;i < m_PCM->punct_col_num;i++) {
        for (k = 0;k < m_PCM->M_b;k++) {
            for (j = 0;j < z_sb;j = j + HEX_BITS) {
                temp_bin4 = 8 * Punc_vote_Mag_Row_before_BS[i][k][j]
                          + 4 * Punc_vote_Mag_Row_before_BS[i][k][j + 1]
                          + 2 * Punc_vote_Mag_Row_before_BS[i][k][j + 2]
                          + 1 * Punc_vote_Mag_Row_before_BS[i][k][j + 3];
                fprintf(fp_PUNC_VOTE_MAG_ROW, "%x", temp_bin4);
            }
            fprintf(fp_PUNC_VOTE_MAG_ROW, "\n");
        }
        fprintf(fp_PUNC_VOTE_MAG_ROW, "\n");
        for (k = 0; k < m_PCM->M_b;k++) {
            for (j = 0;j < z_sb;j = j + HEX_BITS) {
                temp_bin4 = 8 * Punc_vote_Mag_Row[i][k][j]
                          + 4 * Punc_vote_Mag_Row[i][k][j + 1]
                          + 2 * Punc_vote_Mag_Row[i][k][j + 2]
                          + 1 * Punc_vote_Mag_Row[i][k][j + 3];
                fprintf(fp_PUNC_VOTE_MAG_ROW, "%x", temp_bin4);
            }
            fprintf(fp_PUNC_VOTE_MAG_ROW, "\n");
        }
        fprintf(fp_PUNC_VOTE_MAG_ROW, "\n");
        fprintf(fp_PUNC_VOTE_MAG_ROW, "\n");
    }
    for (i = 0;i < m_PCM->punct_col_num;i++) {
        for (j = 0;j < z_sb;j = j + HEX_BITS) {
            temp_bin4 = 8 * Punc_vote_decision[i][j]
                      + 4 * Punc_vote_decision[i][j + 1]
                      + 2 * Punc_vote_decision[i][j + 2]
                      + 1 * Punc_vote_decision[i][j + 3];
            fprintf(fp_PUNC_VOTE_DEC, "%x", temp_bin4);
        }
        fprintf(fp_PUNC_VOTE_DEC, "\n");
    }
    for (i = 0;i < m_PCM->punct_col_num;i++) {
        for (j = 0;j < z_sb;j++) {
            temp_bin4 = Punc_vote_Mag[i][j];
            fprintf(fp_PUNC_VOTE_MAG, "%x", temp_bin4);
        }
        fprintf(fp_PUNC_VOTE_MAG, "\n");
    }
}
#endif
#if defined(__FULL_CRC__)
//==============================================
// full crc >>> >>>
//==============================================
void TV_Dec_Inter::Print_TV_full_crc(int* crc_dec_LFSR_final, int mn)
{
    int temp_bin4;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_FULL_CRC, "iter : %d\n", mn);
#endif
    temp_bin4 = 8 * crc_dec_LFSR_final[79] + 4 * crc_dec_LFSR_final[78] + 2 * crc_dec_LFSR_final[77] + 1 * crc_dec_LFSR_final[76];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[75] + 4 * crc_dec_LFSR_final[74] + 2 * crc_dec_LFSR_final[73] + 1 * crc_dec_LFSR_final[72];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[71] + 4 * crc_dec_LFSR_final[70] + 2 * crc_dec_LFSR_final[69] + 1 * crc_dec_LFSR_final[68];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[67] + 4 * crc_dec_LFSR_final[66] + 2 * crc_dec_LFSR_final[65] + 1 * crc_dec_LFSR_final[64];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[63] + 4 * crc_dec_LFSR_final[62] + 2 * crc_dec_LFSR_final[61] + 1 * crc_dec_LFSR_final[60];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[59] + 4 * crc_dec_LFSR_final[58] + 2 * crc_dec_LFSR_final[57] + 1 * crc_dec_LFSR_final[56];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[55] + 4 * crc_dec_LFSR_final[54] + 2 * crc_dec_LFSR_final[53] + 1 * crc_dec_LFSR_final[52];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[51] + 4 * crc_dec_LFSR_final[50] + 2 * crc_dec_LFSR_final[49] + 1 * crc_dec_LFSR_final[48];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[47] + 4 * crc_dec_LFSR_final[46] + 2 * crc_dec_LFSR_final[45] + 1 * crc_dec_LFSR_final[44];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[43] + 4 * crc_dec_LFSR_final[42] + 2 * crc_dec_LFSR_final[41] + 1 * crc_dec_LFSR_final[40];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[39] + 4 * crc_dec_LFSR_final[38] + 2 * crc_dec_LFSR_final[37] + 1 * crc_dec_LFSR_final[36];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[35] + 4 * crc_dec_LFSR_final[34] + 2 * crc_dec_LFSR_final[33] + 1 * crc_dec_LFSR_final[32];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[31] + 4 * crc_dec_LFSR_final[30] + 2 * crc_dec_LFSR_final[29] + 1 * crc_dec_LFSR_final[28];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[27] + 4 * crc_dec_LFSR_final[26] + 2 * crc_dec_LFSR_final[25] + 1 * crc_dec_LFSR_final[24];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[23] + 4 * crc_dec_LFSR_final[22] + 2 * crc_dec_LFSR_final[21] + 1 * crc_dec_LFSR_final[20];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[19] + 4 * crc_dec_LFSR_final[18] + 2 * crc_dec_LFSR_final[17] + 1 * crc_dec_LFSR_final[16];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[15] + 4 * crc_dec_LFSR_final[14] + 2 * crc_dec_LFSR_final[13] + 1 * crc_dec_LFSR_final[12];  fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[11] + 4 * crc_dec_LFSR_final[10] + 2 * crc_dec_LFSR_final[9] + 1 * crc_dec_LFSR_final[8];    fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[7] + 4 * crc_dec_LFSR_final[6] + 2 * crc_dec_LFSR_final[5] + 1 * crc_dec_LFSR_final[4];      fprintf(fp_FULL_CRC, "%x", temp_bin4);
    temp_bin4 = 8 * crc_dec_LFSR_final[3] + 4 * crc_dec_LFSR_final[2] + 2 * crc_dec_LFSR_final[1] + 1 * crc_dec_LFSR_final[0];      fprintf(fp_FULL_CRC, "%x\n", temp_bin4);
}

//==============================================
// full crc internal >>> >>>
//==============================================
void TV_Dec_Inter::Print_TV_full_crc_internal(int** crc_dec_LFSR_internal, int mn)
{
    int temp_bin4;
    int i;
    int N_CWD_4K = 4 * (m_PCM->N_b - m_PCM->M_b);
#if defined (__ECC_TV_ITER__)
    fprintf(fp_FULL_CRC, "iter : %d\n", mn);
#endif
    for (i = 0;i < N_CWD_4K;i++) {
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][79] + 4 * crc_dec_LFSR_internal[i][78] + 2 * crc_dec_LFSR_internal[i][77] + 1 * crc_dec_LFSR_internal[i][76];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][75] + 4 * crc_dec_LFSR_internal[i][74] + 2 * crc_dec_LFSR_internal[i][73] + 1 * crc_dec_LFSR_internal[i][72];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][71] + 4 * crc_dec_LFSR_internal[i][70] + 2 * crc_dec_LFSR_internal[i][69] + 1 * crc_dec_LFSR_internal[i][68];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][67] + 4 * crc_dec_LFSR_internal[i][66] + 2 * crc_dec_LFSR_internal[i][65] + 1 * crc_dec_LFSR_internal[i][64];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][63] + 4 * crc_dec_LFSR_internal[i][62] + 2 * crc_dec_LFSR_internal[i][61] + 1 * crc_dec_LFSR_internal[i][60];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][59] + 4 * crc_dec_LFSR_internal[i][58] + 2 * crc_dec_LFSR_internal[i][57] + 1 * crc_dec_LFSR_internal[i][56];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][55] + 4 * crc_dec_LFSR_internal[i][54] + 2 * crc_dec_LFSR_internal[i][53] + 1 * crc_dec_LFSR_internal[i][52];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][51] + 4 * crc_dec_LFSR_internal[i][50] + 2 * crc_dec_LFSR_internal[i][49] + 1 * crc_dec_LFSR_internal[i][48];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][47] + 4 * crc_dec_LFSR_internal[i][46] + 2 * crc_dec_LFSR_internal[i][45] + 1 * crc_dec_LFSR_internal[i][44];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][43] + 4 * crc_dec_LFSR_internal[i][42] + 2 * crc_dec_LFSR_internal[i][41] + 1 * crc_dec_LFSR_internal[i][40];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][39] + 4 * crc_dec_LFSR_internal[i][38] + 2 * crc_dec_LFSR_internal[i][37] + 1 * crc_dec_LFSR_internal[i][36];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][35] + 4 * crc_dec_LFSR_internal[i][34] + 2 * crc_dec_LFSR_internal[i][33] + 1 * crc_dec_LFSR_internal[i][32];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][31] + 4 * crc_dec_LFSR_internal[i][30] + 2 * crc_dec_LFSR_internal[i][29] + 1 * crc_dec_LFSR_internal[i][28];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][27] + 4 * crc_dec_LFSR_internal[i][26] + 2 * crc_dec_LFSR_internal[i][25] + 1 * crc_dec_LFSR_internal[i][24];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][23] + 4 * crc_dec_LFSR_internal[i][22] + 2 * crc_dec_LFSR_internal[i][21] + 1 * crc_dec_LFSR_internal[i][20];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][19] + 4 * crc_dec_LFSR_internal[i][18] + 2 * crc_dec_LFSR_internal[i][17] + 1 * crc_dec_LFSR_internal[i][16];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][15] + 4 * crc_dec_LFSR_internal[i][14] + 2 * crc_dec_LFSR_internal[i][13] + 1 * crc_dec_LFSR_internal[i][12];  fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][11] + 4 * crc_dec_LFSR_internal[i][10] + 2 * crc_dec_LFSR_internal[i][9] + 1 * crc_dec_LFSR_internal[i][8];    fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][7] + 4 * crc_dec_LFSR_internal[i][6] + 2 * crc_dec_LFSR_internal[i][5] + 1 * crc_dec_LFSR_internal[i][4];      fprintf(fp_FULL_CRC_INT, "%x", temp_bin4);
        temp_bin4 = 8 * crc_dec_LFSR_internal[i][3] + 4 * crc_dec_LFSR_internal[i][2] + 2 * crc_dec_LFSR_internal[i][1] + 1 * crc_dec_LFSR_internal[i][0];      fprintf(fp_FULL_CRC_INT, "%x\n", temp_bin4);
    }
    fprintf(fp_FULL_CRC_INT, "\n");
}
#else
//==============================================
// Partial CRC register >>>
//==============================================
void TV_Dec_Inter::Print_TV_PCRC(int* crc_in, int* crc1, int* crc2, int* crc3, int* crc4, int mn, int jj)
{
    int i;
    int tmp1, tmp2, tmp3, tmp4;
    int* crc_acc;
    crc_acc = new int[CRC_LEN];
    int temp_bin4;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_PCRC_T4, "iter : %d\n", mn);
#endif
    for (i = 0;i < CRC_LEN;i++) {
        crc_acc[i] = (crc1[i] + crc2[i] + crc3[i] + crc4[i]) % 2;
    }
    // crc 1
    for (i = 0; i < 20; i++) {
        tmp1 = crc1[79 - 0 - 4 * i];
        tmp2 = crc1[79 - 1 - 4 * i];
        tmp3 = crc1[79 - 2 - 4 * i];
        tmp4 = crc1[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
        //printf("(1) [%d]: %d\n", i, temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    /*
    // crc 2
    for (i = 0; i < 20; i++) {
        tmp1 = crc2[79 - 0 - 4 * i];
        tmp2 = crc2[79 - 1 - 4 * i];
        tmp3 = crc2[79 - 2 - 4 * i];
        tmp4 = crc2[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
        //printf("(2) [%d]: %d\n", i, temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    // crc 3
    for (i = 0; i < 20; i++) {
        tmp1 = crc3[79 - 0 - 4 * i];
        tmp2 = crc3[79 - 1 - 4 * i];
        tmp3 = crc3[79 - 2 - 4 * i];
        tmp4 = crc3[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
        //printf("(3) [%d]: %d\n", i, temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    // crc 4
    for (i = 0; i < 20; i++) {
        tmp1 = crc4[79 - 0 - 4 * i];
        tmp2 = crc4[79 - 1 - 4 * i];
        tmp3 = crc4[79 - 2 - 4 * i];
        tmp4 = crc4[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    for (i = 0; i < 20; i++) {
        tmp1 = crc_acc[79 - 0 - 4 * i];
        tmp2 = crc_acc[79 - 1 - 4 * i];
        tmp3 = crc_acc[79 - 2 - 4 * i];
        tmp4 = crc_acc[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    */
    if (jj==m_PCM->N_b-m_PCM->M_b-1) fprintf(fp_PCRC_T4, "\n"); // iteration >> >L>
    if (jj == m_PCM->N_b - m_PCM->M_b - 1) {
        for (i = 0;i < m_PCM->z_sb; i = i + HEX_BITS) {
            temp_bin4 = 1 * crc_in[i + 3] + 2 * crc_in[i + 2] + 4 * crc_in[i + 1] + 8 * crc_in[i];
            fprintf(fp_PCRC_T4_in_last_column, "%x", temp_bin4);
        }
        fprintf(fp_PCRC_T4_in_last_column, "\n");
    }
    delete[] crc_acc;
}
//==============================================
// Partial CRC register >>>
//==============================================
void TV_Dec_Inter::Print_TV_PCRC(int* crc1, int* crc2, int* crc3, int* crc4, int mn)
{
    int i;
    int tmp1, tmp2, tmp3, tmp4;
    int* crc_acc;
    crc_acc = new int[CRC_LEN];
    int temp_bin4;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_PCRC_T4, "iter : %d\n", mn);
#endif
    for (i = 0;i < CRC_LEN;i++) {
        crc_acc[i] = (crc1[i] + crc2[i] + crc3[i] + crc4[i]) % 2;
    }
    /*
    // crc 1
    for (i = 0; i < 20; i++) {
        tmp1 = crc1[79 - 0 - 4 * i];
        tmp2 = crc1[79 - 1 - 4 * i];
        tmp3 = crc1[79 - 2 - 4 * i];
        tmp4 = crc1[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    // crc 2
    for (i = 0; i < 20; i++) {
        tmp1 = crc2[79 - 0 - 4 * i];
        tmp2 = crc2[79 - 1 - 4 * i];
        tmp3 = crc2[79 - 2 - 4 * i];
        tmp4 = crc2[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    // crc 3
    for (i = 0; i < 20; i++) {
        tmp1 = crc3[79 - 0 - 4 * i];
        tmp2 = crc3[79 - 1 - 4 * i];
        tmp3 = crc3[79 - 2 - 4 * i];
        tmp4 = crc3[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    // crc 4
    for (i = 0; i < 20; i++) {
        tmp1 = crc4[79 - 0 - 4 * i];
        tmp2 = crc4[79 - 1 - 4 * i];
        tmp3 = crc4[79 - 2 - 4 * i];
        tmp4 = crc4[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    */
    for (i = 0; i < 20; i++) {
        tmp1 = crc_acc[79 - 0 - 4 * i];
        tmp2 = crc_acc[79 - 1 - 4 * i];
        tmp3 = crc_acc[79 - 2 - 4 * i];
        tmp4 = crc_acc[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    delete[] crc_acc;
}
void TV_Dec_Inter::Print_TV_PCRC_Cycle_based(int* crc1, int* crc2, int* crc3, int* crc4, int mn, int jj)
{
    int i;
    int tmp1, tmp2, tmp3, tmp4;
    int temp_bin4;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_PCRC_T4, "iter : %d\tcol : %d\n", mn, jj);
#endif
    // crc 1
    for (i = 0; i < 20; i++) {
        tmp1 = crc1[79 - 0 - 4 * i];
        tmp2 = crc1[79 - 1 - 4 * i];
        tmp3 = crc1[79 - 2 - 4 * i];
        tmp4 = crc1[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    // crc 2
    for (i = 0; i < 20; i++) {
        tmp1 = crc2[79 - 0 - 4 * i];
        tmp2 = crc2[79 - 1 - 4 * i];
        tmp3 = crc2[79 - 2 - 4 * i];
        tmp4 = crc2[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    // crc 3
    for (i = 0; i < 20; i++) {
        tmp1 = crc3[79 - 0 - 4 * i];
        tmp2 = crc3[79 - 1 - 4 * i];
        tmp3 = crc3[79 - 2 - 4 * i];
        tmp4 = crc3[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    // crc 4
    for (i = 0; i < 20; i++) {
        tmp1 = crc4[79 - 0 - 4 * i];
        tmp2 = crc4[79 - 1 - 4 * i];
        tmp3 = crc4[79 - 2 - 4 * i];
        tmp4 = crc4[79 - 3 - 4 * i];
        temp_bin4 = tmp4 + 2 * tmp3 + 4 * tmp2 + 8 * tmp1;
        fprintf(fp_PCRC_T4, "%x", temp_bin4);
    }
    fprintf(fp_PCRC_T4, "\n");
    fprintf(fp_PCRC_T4, "\n"); // iteration >> >L>
}
#endif
//==============================================
// Old v2c sign >>>
//==============================================
void TV_Dec_Inter::Print_TV_old_sgn(int ** old_sgn, int mn, int PCRC_done, int last_col, int skip_idx)
{
    int n, ii, i, kk;
    int col_blk;
    int temp_bin4;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_OLD_SGN, "iter : %d\n", mn);
#endif
    for (n = 0; n < m_PCM->N; n = n + m_PCM->z_sb) {
        col_blk = n / m_PCM->z_sb;
#if defined (__RUN_ITER34_HIGH_DV_SKIP__)
        if ((MODE_DEC_HD == m_param_dec->init_n) &&
            //((mn == 4 + ITER_MAX_HBF) || (mn == 4)) &&
            //(mn == 4 + ITER_MAX_HBF) &&
            ((mn == 4 + ITER_MAX_HBF) || (mn == 3 + ITER_MAX_HBF)) &&
            (col_blk < skip_idx)) {
            Intentional_Blank();
        }
        else if ((TRUE == PCRC_done) && (col_blk > last_col)) {
            Intentional_Blank();
        }
        else {
            for (ii = 0; ii < MAX_DV_GLOBAL; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_OLD_SGN, "col : %3d\tii : %d\t", col_blk, ii);
#endif
            for (i = 0; i < m_PCM->z_sb; i = i + m_PCM->z_sb) {
                for (kk = 0; kk < m_PCM->z_sb; kk = kk + HEX_BITS) {
                    /* old sgn */
                    temp_bin4 = 1 * old_sgn[ii][n + i + 3 + kk]
                                + 2 * old_sgn[ii][n + i + 2 + kk]
                        + 4 * old_sgn[ii][n + i + 1 + kk]
                        + 8 * old_sgn[ii][n + i + kk];
                    fprintf(fp_OLD_SGN, "%x", temp_bin4);
                }
                fprintf(fp_OLD_SGN, "\n");
            }
        }
        }
#else
        if ((TRUE == PCRC_done) && (col_blk > last_col)) {
            Intentional_Blank();
        }
        else {
            for (ii = 0; ii < MAX_DV_GLOBAL; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_OLD_SGN, "col : %3d\tii : %d\t", col_blk, ii);
#endif
            for (i = 0; i < m_PCM->z_sb; i = i + m_PCM->z_sb) {
                for (kk = 0; kk < m_PCM->z_sb; kk = kk + HEX_BITS) {
                    /* old sgn */
                    temp_bin4 =    1 * old_sgn[ii][n + i + 3 + kk]
                                + 2 * old_sgn[ii][n + i + 2 + kk]
                        + 4 * old_sgn[ii][n + i + 1 + kk]
                        + 8 * old_sgn[ii][n + i + kk];
                    fprintf(fp_OLD_SGN, "%x", temp_bin4);
                }
                fprintf(fp_OLD_SGN, "\n");
            }
        }
    }
#endif
    }
}
//=============================================
// Old v2c sign ???
//=============================================
#if defined(__HALF_COL_UPDATE__)
void TV_Dec_Inter::Print_TV_old_sgn_HCU(int** old_sgn, int mn, int PCRC_done, int last_col, int skip_idx)
{
    int n, ii, i, kk;
    int col_blk;
    int col_blk_effective;
    int G_idx;
    int temp_bin4;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_OLD_SGN_HCU, "iter : %d\n", mn);
#endif
    for (n = 0; n < m_PCM->N+m_PCM->punct_col_num*m_PCM->z_sb; n = n + m_PCM->z_sb) {
        col_blk = n / m_PCM->z_sb;
        if ((TRUE == PCRC_done) && (col_blk > last_col)) {
            Intentional_Blank();
        }
        else {
            /* OLD_SGN HCU */
            if (col_blk < HCU_start) {
                col_blk_effective = col_blk; G_idx = 0;
            }
            else if (col_blk >= HCU_start && col_blk < m_PCM->N_b - m_PCM->M_b + m_PCM->punct_col_num) {
                if (mn % 2 == 0) {
                    if (col_blk == HCU_start)                                { col_blk_effective = HCU_start; G_idx = 0; }
                    else if (col_blk == HCU_end)                             { col_blk_effective = HCU_start; G_idx = 1; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b)            { col_blk_effective = HCU_end; G_idx = 0; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b + 1)        { col_blk_effective = HCU_end; G_idx = 1; }
                }
                else {
                    if (col_blk == HCU_start) { col_blk_effective = HCU_start; G_idx = 1; }
                    else if (col_blk == HCU_end) { col_blk_effective = HCU_start; G_idx = 0; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b) { col_blk_effective = HCU_end; G_idx = 1; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b + 1) { col_blk_effective = HCU_end; G_idx = 0; }
                }
            }
            else {
                col_blk_effective = col_blk - m_PCM->punct_col_num; G_idx = 0;
            }
            // Col Blk 0, 1 Puncturing Case
            /*
            if (col_blk > 3) { col_blk_effective = col_blk - 2; G_idx = 0; }
            else {
                if (mn % 2 == 0) {
                    if (col_blk == 0) { col_blk_effective = 0;G_idx = 0; }
                    else if (col_blk == 1) { col_blk_effective = 0;G_idx = 1; }
                    else if (col_blk == 2) { col_blk_effective = 1;G_idx = 0; }
                    else if (col_blk == 3) { col_blk_effective = 1;G_idx = 1; }
                }
                else {
                    else if (col_blk == 2) { col_blk_effective = 1;G_idx = 1; }
                    else if (col_blk == 3) { col_blk_effective = 1;G_idx = 0; }
                }
            }
            */
            //fprintf(fp_OLD_SGN_HCU, "iter: %3d\tcol : %3d\tGroup : %d\n", mn, col_blk_effective, G_idx);
            for (ii = 0; ii < MAX_DV_GLOBAL_HALF; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_OLD_SGN_HCU, "col : %3d\tii : %d\t", col_blk, ii);
#endif
                for (i = 0; i < m_PCM->z_sb; i = i + m_PCM->z_sb) {
                    for (kk = 0; kk < m_PCM->z_sb; kk = kk + HEX_BITS) {
                        /* old sgn */
                        temp_bin4 = 1 * old_sgn[ii][n + i + 3 + kk]
                            + 2 * old_sgn[ii][n + i + 2 + kk]
                            + 4 * old_sgn[ii][n + i + 1 + kk]
                            + 8 * old_sgn[ii][n + i + kk];
                        fprintf(fp_OLD_SGN_HCU, "%x", temp_bin4);
                    }
                    fprintf(fp_OLD_SGN_HCU, "\n");
                }
            }
        }
    }
}   
#endif
void TV_Dec_Inter::Print_TV_llr_out(int * llr_out, int * Variable_mem, int mn, int PCRC_done, int last_col, int skip_idx)
{
    int n, i;
    int col_blk;
    int mag;
    int sign;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_LLR_OUT, "iter : %d\n", mn);
    fprintf(fp_LLR_OUT_SGN, "iter : %d\n", mn);
#endif
    for (n = 0; n < m_PCM->N; n = n + m_PCM->z_sb) {
        col_blk = n / m_PCM->z_sb;
#if defined (__RUN_ITER34_HIGH_DV_SKIP__)
        if ((MODE_DEC_HD == m_param_dec->init_n) &&
            //((mn == 4 + ITER_MAX_HBF) || (mn == 4)) &&
            //(mn == 4 + ITER_MAX_HBF) &&
            ((mn == 4 + ITER_MAX_HBF) || (mn == 3 + ITER_MAX_HBF)) &&
            (col_blk < skip_idx)) {
            Intentional_Blank();
        }
        else if ((TRUE == PCRC_done) && (col_blk > last_col)) {
            Intentional_Blank();
        }
        else {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_LLR_OUT, "col : %3d\t", col_blk);
            //fprintf(fp_LLR_OUT_SGN, "col : %3d\t", col_blk);
#endif
            /* general case */
            for (i = 0; i < m_PCM->z_sb; i++) {
                mag = abs(llr_out[i + n]);
                if (llr_out[i + n] >= 0) { sign = 0; }
                else { sign = 1; }
                fprintf(fp_LLR_OUT, "%x", mag);
                //fprintf(fp_LLR_OUT_SGN, "%x", sign);
            }
            fprintf(fp_LLR_OUT, "\n");
            //fprintf(fp_LLR_OUT_SGN, "\n");
        }
#else
        if ((TRUE == PCRC_done) && (col_blk > last_col)) {
            Intentional_Blank();
        }
        else {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_LLR_OUT, "col : %3d\t", col_blk);
            //fprintf(fp_LLR_OUT_SGN, "col : %3d\t", col_blk);
#endif
            /* general case */
            for (i = 0; i < m_PCM->z_sb; i++) {
                mag = abs(llr_out[i + n]);
                if (((i + n) >= m_ecc_info->bit_pos.info_punc_start1) && ((i + n) < m_ecc_info->bit_pos.info_punc_end1)) {
                    sign = Variable_mem[i + n];
                }
                else if (((i + n) >= m_ecc_info->bit_pos.info_punc_start2) && ((i + n) < m_ecc_info->bit_pos.info_punc_end2)) {
                    sign = Variable_mem[i + n];
                }
                else {
                    //if (llr_out[i + n] >= 0) { sign = 0; }
                    if (llr_out[i + n] > 0) { sign = 0; }
                    else if (llr_out[i + n] == 0) {
                        sign = Variable_mem[i + n];
                    }
                    else { sign = 1; }
                }
//              fprintf(fp_LLR_OUT, "%x", mag);
                if (mag <= 15)  fprintf(fp_LLR_OUT, "0%x", mag);
                else            fprintf(fp_LLR_OUT, "%x", mag);
                fprintf(fp_LLR_OUT_SGN, "%x", sign);
            }
            fprintf(fp_LLR_OUT, "\n");
            fprintf(fp_LLR_OUT_SGN, "\n");
        }
#endif
    }
}
void TV_Dec_Inter::Print_TV_vtc_inp(int ** vtc_inp, int mn, int PCRC_done, int last_col, int skip_idx)
{
    int n, ii, kk;
    int col_blk;
    int temp_bin4;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_VNU_IN, "iter : %d\n", mn);
#endif
    for (n = 0; n < (3 * m_PCM->N); n = n + (m_PCM->z_sb * 3)) {
        col_blk = n / (m_PCM->z_sb * 3);
#if defined (__RUN_ITER34_HIGH_DV_SKIP__)
        if ((MODE_DEC_HD == m_param_dec->init_n) &&
            //((mn == 4 + ITER_MAX_HBF) || (mn == 4)) &&
            //(mn == 4 + ITER_MAX_HBF) &&
            ((mn == 4 + ITER_MAX_HBF) || (mn == 3 + ITER_MAX_HBF)) &&
            (col_blk < skip_idx)) {
            Intentional_Blank();
        }
        else if ((TRUE == PCRC_done) && (col_blk > last_col)) {
            Intentional_Blank();
        }
        else {
            /* VTC_INP */
            for (ii = 0; ii < MAX_DV_GLOBAL; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_VNU_IN, "col : %3d\tii : %d\t", col_blk, ii);
#endif
                // sign (1bit x 256)
                for (kk = 0; kk < m_PCM->z_sb; kk = kk + HEX_BITS) {
                    temp_bin4 = 1 * vtc_inp[ii][n + kk + 3]
                        + 2 * vtc_inp[ii][n + kk + 2]
                        + 4 * vtc_inp[ii][n + kk + 1]
                        + 8 * vtc_inp[ii][n + kk];
                    fprintf(fp_VNU_IN, "%x", temp_bin4);
                }
                fprintf(fp_VNU_IN, "\n");
            }
            for (ii = 0; ii < MAX_DV_GLOBAL; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_VNU_IN, "col : %3d\tii : %d\t", col_blk, ii);
#endif
                // mag (2bit x 256)
                for (kk = 0; kk < (2 * m_PCM->z_sb); kk = kk + HEX_BITS) {
                    temp_bin4 = 1 * vtc_inp[ii][n + m_PCM->z_sb + kk + 3]
                        + 2 * vtc_inp[ii][n + m_PCM->z_sb + kk + 2]
                        + 4 * vtc_inp[ii][n + m_PCM->z_sb + kk + 1]
                        + 8 * vtc_inp[ii][n + m_PCM->z_sb + kk];
                    fprintf(fp_VNU_IN, "%x", temp_bin4);
                }
                fprintf(fp_VNU_IN, "\n");
            }
#if defined (__ECC_TV_ITER__)
            fprintf(fp_VNU_IN, "\n");
#endif
        }
#else
        if ((TRUE == PCRC_done) && (col_blk > last_col)) {
            Intentional_Blank();
        }
        else {
            /* VTC_INP */
            for (ii = 0; ii < MAX_DV_GLOBAL; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_VNU_IN, "col : %3d\tii : %d\t", col_blk, ii);
#endif
                // sign (1bit x 256)
                for (kk = 0; kk < m_PCM->z_sb; kk = kk + HEX_BITS) {
                    temp_bin4 =    1 * vtc_inp[ii][n + kk + 3]
                        + 2 * vtc_inp[ii][n + kk + 2]
                        + 4 * vtc_inp[ii][n + kk + 1]
                        + 8 * vtc_inp[ii][n + kk];
                    fprintf(fp_VNU_IN, "%x", temp_bin4);
                }
                fprintf(fp_VNU_IN, "\n");
            }
            for (ii = 0; ii < MAX_DV_GLOBAL; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_VNU_IN, "col : %3d\tii : %d\t", col_blk, ii);
#endif
                // mag (2bit x 256)
                for (kk = 0; kk < (2 * m_PCM->z_sb); kk = kk + HEX_BITS) {
                    temp_bin4 =    1 * vtc_inp[ii][n + m_PCM->z_sb + kk + 3]
                        + 2 * vtc_inp[ii][n + m_PCM->z_sb + kk + 2]
                        + 4 * vtc_inp[ii][n + m_PCM->z_sb + kk + 1]
                        + 8 * vtc_inp[ii][n + m_PCM->z_sb + kk];
                    fprintf(fp_VNU_IN, "%x", temp_bin4);
                }
                fprintf(fp_VNU_IN, "\n");
            }
#if defined (__ECC_TV_ITER__)
            fprintf(fp_VNU_IN, "\n");
#endif
        }
#endif
    }
}
#if defined(__HALF_COL_UPDATE__)
void TV_Dec_Inter::Print_TV_vtc_inp_HCU(int** vtc_inp, int mn, int PCRC_done, int last_col, int skip_idx)
{
    int n, ii, kk;
    int col_blk;
    int col_blk_effective;
    int G_idx;
    int temp_bin4;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_VNU_IN_HCU, "iter : %d\n", mn);
#endif
    for (n = 0; n < (3 * (m_PCM->N + m_PCM->punct_col_num * m_PCM->z_sb)); n = n + (m_PCM->z_sb * 3)) {
        col_blk = n / (m_PCM->z_sb * 3);
        //if ((TRUE == PCRC_done) && (col_blk > last_col)) {
        if ((TRUE == PCRC_done) && (col_blk > last_col + 2)) {
            Intentional_Blank();
        }
        else {
            /* VTC_INP HCU */
            if (col_blk < HCU_start) {
                col_blk_effective = col_blk;
                G_idx = 0;
            }
            else if (col_blk >= HCU_start && col_blk < m_PCM->N_b - m_PCM->M_b + m_PCM->punct_col_num) {
                if (mn % 2 == 0) {
                    if (col_blk == HCU_start)                                { col_blk_effective = HCU_start; G_idx = 0; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b - 1)         { col_blk_effective = HCU_start; G_idx = 1; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b)             { col_blk_effective = m_PCM->N_b - m_PCM->M_b - 1; G_idx = 0; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b + 1)         { col_blk_effective = m_PCM->N_b - m_PCM->M_b - 1; G_idx = 1; }
                }
                else {
                    if (col_blk == HCU_start)                                { col_blk_effective = HCU_start; G_idx = 1; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b - 1)         { col_blk_effective = HCU_start; G_idx = 0; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b)             { col_blk_effective = m_PCM->N_b - m_PCM->M_b - 1; G_idx = 1; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b + 1)         { col_blk_effective = m_PCM->N_b - m_PCM->M_b - 1; G_idx = 0; }
                }
            }
            else {
                col_blk_effective = col_blk - m_PCM->punct_col_num; G_idx = 0;
            }
            // Col Blk 0, 1 Puncturing Case
            /*
            if (col_blk > 3) { col_blk_effective = col_blk - 2; G_idx = 0; }
            else {
                if (mn % 2 == 0) {
                    if (col_blk == 0) { col_blk_effective = 0;G_idx = 0; }
                }
                else {
                    if (col_blk == 0) { col_blk_effective = 0;G_idx = 1; }
                    else if (col_blk == 1) { col_blk_effective = 0;G_idx = 0; }
                    else if (col_blk == 2) { col_blk_effective = 1;G_idx = 1; }
                    else if (col_blk == 3) { col_blk_effective = 1;G_idx = 0; }
                }
            }
            */
            //fprintf(fp_VNU_IN_HCU, "iter: %3d\tcol : %3d\tGroup : %d\n", mn, col_blk_effective, G_idx);
            // sign (1bit x 256)
            for (ii = 0; ii < MAX_DV_GLOBAL_HALF; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_VNU_IN_HCU, "col : %3d\tmux_idx : %d\t", col_blk, ii);
#endif
                for (kk = 0; kk < m_PCM->z_sb; kk = kk + HEX_BITS) {
                    temp_bin4 = 1 * vtc_inp[ii][n + kk + 3]
                        + 2 * vtc_inp[ii][n + kk + 2]
                        + 4 * vtc_inp[ii][n + kk + 1]
                        + 8 * vtc_inp[ii][n + kk];
                    fprintf(fp_VNU_IN_HCU, "%x", temp_bin4);
                }
                fprintf(fp_VNU_IN_HCU, "\n");
            }
            // mag (2bit x 256)
            for (ii = 0; ii < MAX_DV_GLOBAL_HALF; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_VNU_IN_HCU, "col : %3d\tii : %d\t", col_blk, ii);
#endif
                for (kk = 0; kk < (2 * m_PCM->z_sb); kk = kk + HEX_BITS) {
                    temp_bin4 = 1 * vtc_inp[ii][n + m_PCM->z_sb + kk + 3]
                        + 2 * vtc_inp[ii][n + m_PCM->z_sb + kk + 2]
                        + 4 * vtc_inp[ii][n + m_PCM->z_sb + kk + 1]
                        + 8 * vtc_inp[ii][n + m_PCM->z_sb + kk];
                    fprintf(fp_VNU_IN_HCU, "%x", temp_bin4);
                }
                fprintf(fp_VNU_IN_HCU, "\n");
            }
#if defined (__ECC_TV_ITER__)
            fprintf(fp_VNU_IN_HCU, "\n");
#endif
        }
    }
}
#endif
//=============================================
// cwc ???
//=============================================
void TV_Dec_Inter::Print_TV_cwc(int * cwc, int mn, int skip_idx)
{
    int n;
    int kk;
    int temp_bin4;
    int col_blk;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_ITR_OUT, "iter : %d\n", mn);
#endif
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) {
        for (n = 0; n < m_PCM->z_sb * (m_PCM->N_b - m_PCM->M_b); n = n + m_PCM->z_sb) {
            col_blk = n / m_PCM->z_sb;
#if defined (__RUN_ITER34_HIGH_DV_SKIP__)
            if ((MODE_DEC_HD == m_param_dec->init_n) &&
                //((mn == 4 + ITER_MAX_HBF) || (mn == 4)) &&
                //(mn == 4 + ITER_MAX_HBF) &&
                ((mn == 4 + ITER_MAX_HBF) || (mn == 3 + ITER_MAX_HBF)) &&
                (col_blk < skip_idx)) {
                Intentional_Blank();
            }
            else {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_ITR_OUT, "col : %3d\t", col_blk);
#endif
                for (kk = 0; kk < m_PCM->z_sb; kk = kk + HEX_BITS) {
                    temp_bin4 = 8 * cwc[n + m_PCM->z_sb - kk - 1]
                        + 4 * cwc[n + m_PCM->z_sb - kk - 2]
                        + 2 * cwc[n + m_PCM->z_sb - kk - 3]
                        + 1 * cwc[n + m_PCM->z_sb - kk - 4];
                    fprintf(fp_ITR_OUT, "%x", temp_bin4);
                }
                fprintf(fp_ITR_OUT, "\n");
            }
#else
            for (kk = 0; kk < m_PCM->z_sb; kk = kk + HEX_BITS) {
                temp_bin4 = 8 * cwc[n + m_PCM->z_sb - kk - 1]
                    + 4 * cwc[n + m_PCM->z_sb - kk - 2]
                    + 2 * cwc[n + m_PCM->z_sb - kk - 3]
                    + 1 * cwc[n + m_PCM->z_sb - kk - 4];
                fprintf(fp_ITR_OUT, "%x", temp_bin4);
            }
            fprintf(fp_ITR_OUT, "\n");
#endif
        }
    }
    fprintf(fp_ITR_OUT, "\n");
}
//=============================================
//
//=============================================
void TV_Dec_Inter::Print_TV_new_sgn(int ** vnu_out, int mn, int PCRC_done, int last_col, int skip_idx)
{
    int n, ii, kk;
    int col_blk;
    int temp_bin4;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_VNU_OUT, "iter : %d\n", mn);
#endif
    for (n = 0; n < 3 * m_PCM->N; n = n + m_PCM->z_sb * 3) {
        col_blk = n / (m_PCM->z_sb * 3);
#if defined (__RUN_ITER34_HIGH_DV_SKIP__)
        if ((MODE_DEC_HD == m_param_dec->init_n) &&
            //((mn == 4 + ITER_MAX_HBF) || (mn == 4)) &&
            //(mn == 4 + ITER_MAX_HBF) &&
            ((mn == 4 + ITER_MAX_HBF) || (mn == 3 + ITER_MAX_HBF)) &&
            (col_blk < skip_idx)) {
            Intentional_Blank();
        }
        else if ((TRUE == PCRC_done) && (col_blk > last_col)) {
            Intentional_Blank();
        }
        else {
            for (ii = 0; ii < MAX_DV_GLOBAL; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_VNU_OUT, "col : %3d\tii : %d\t", col_blk, ii);
#endif
                // sign (1bit x 256)
                for (kk = 0; kk < m_PCM->z_sb; kk = kk + HEX_BITS) {
                    temp_bin4 = 1 * vnu_out[ii][n + 3 + kk]
                        + 2 * vnu_out[ii][n + 2 + kk]
                        + 4 * vnu_out[ii][n + 1 + kk]
                        + 8 * vnu_out[ii][n + kk];
                    fprintf(fp_VNU_OUT, "%x", temp_bin4);
                }
                fprintf(fp_VNU_OUT, "\n");
            }
            for (ii = 0; ii < MAX_DV_GLOBAL; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_VNU_OUT, "col : %3d\tii : %d\t", col_blk, ii);
#endif
                // mag (2bit x 256)
                for (kk = 0; kk < 2 * m_PCM->z_sb; kk = kk + HEX_BITS) {
                    temp_bin4 = 1 * vnu_out[ii][n + m_PCM->z_sb + 3 + kk]
                        + 2 * vnu_out[ii][n + m_PCM->z_sb + 2 + kk]
                        + 4 * vnu_out[ii][n + m_PCM->z_sb + 1 + kk]
                        + 8 * vnu_out[ii][n + m_PCM->z_sb + kk];
                    fprintf(fp_VNU_OUT, "%x", temp_bin4);
                }
                fprintf(fp_VNU_OUT, "\n");
            }
            fprintf(fp_VNU_OUT, "\n");
        }
#else
        if ((TRUE == PCRC_done) && (col_blk > last_col)) {
            Intentional_Blank();
        }
        else {
            for (ii = 0; ii < MAX_DV_GLOBAL; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_VNU_OUT, "col : %3d\tii : %d\t", col_blk, ii);
#endif
                // sign (1bit x 256)
                for (kk = 0; kk < m_PCM->z_sb; kk = kk + HEX_BITS) {
                    temp_bin4 = 1 * vnu_out[ii][n + 3 + kk]
                        + 2 * vnu_out[ii][n + 2 + kk]
                        + 4 * vnu_out[ii][n + 1 + kk]
                        + 8 * vnu_out[ii][n + 0 + kk];
                    fprintf(fp_VNU_OUT, "%x", temp_bin4);
                }
                fprintf(fp_VNU_OUT, "\n");
            }
            for (ii = 0; ii < MAX_DV_GLOBAL; ii++) {
#if defined (__ECC_TV_ITER__)
                fprintf(fp_VNU_OUT, "col : %3d\tii : %d\t", col_blk, ii);
#endif
                // mag (2bit x 256)
                for (kk = 0; kk < 2 * m_PCM->z_sb; kk = kk + HEX_BITS) {
                    temp_bin4 = 1 * vnu_out[ii][n + m_PCM->z_sb + 3 + kk]
                        + 2 * vnu_out[ii][n + m_PCM->z_sb + 2 + kk]
                        + 4 * vnu_out[ii][n + m_PCM->z_sb + 1 + kk]
                        + 8 * vnu_out[ii][n + m_PCM->z_sb + kk];
                    fprintf(fp_VNU_OUT, "%x", temp_bin4);
                }
                fprintf(fp_VNU_OUT, "\n");
            }
            fprintf(fp_VNU_OUT, "\n");
        }
#endif
    }
}
#if defined(__HALF_COL_UPDATE__)
void TV_Dec_Inter::Print_TV_new_sgn_HCU(int** vnu_out_in, int** vnu_out_in_nq, int** vnu_out, int mn, int PCRC_done, int last_col, int skip_idx)
{
    int n, ii, kk;
    int col_blk;
    int temp_bin4;
    int col_blk_effective;
    int G_idx;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_VNU_OUT_HCU, "iter : %d\n", mn);
    fprintf(fp_VNU_OUT_HCU_in_mag, "iter : %d\n", mn);
    fprintf(fp_VNU_OUT_HCU_in_sgn, "iter : %d\n", mn);
    fprintf(fp_VNU_OUT_HCU_in_mag_nq, "iter : %d\n", mn);
    fprintf(fp_VNU_OUT_HCU_in_sgn_nq, "iter : %d\n", mn);
#endif
    for (n = 0; n < (3 * (m_PCM->N + m_PCM->punct_col_num * m_PCM->z_sb)); n = n + m_PCM->z_sb * 3) {
        col_blk = n / (m_PCM->z_sb * 3);
        if ((TRUE == PCRC_done) && (col_blk > last_col)) {
            Intentional_Blank();
        }
        else {
            if (col_blk < HCU_start) {
                col_blk_effective = col_blk; G_idx = 0;
            }
            else if (col_blk >= HCU_start && col_blk < m_PCM->N_b - m_PCM->M_b + m_PCM->punct_col_num) {
                if (mn % 2 == 0) {
                    if (col_blk == HCU_start) { col_blk_effective = HCU_start; G_idx = 0; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b - 1) { col_blk_effective = HCU_start; G_idx = 1; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b) { col_blk_effective = m_PCM->N_b - m_PCM->M_b - 1; G_idx = 0; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b + 1) { col_blk_effective = m_PCM->N_b - m_PCM->M_b - 1; G_idx = 1; }
                }
                else {
                    if (col_blk == HCU_start) { col_blk_effective = HCU_start; G_idx = 1; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b - 1) { col_blk_effective = HCU_start; G_idx = 0; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b) { col_blk_effective = m_PCM->N_b - m_PCM->M_b - 1; G_idx = 1; }
                    else if (col_blk == m_PCM->N_b - m_PCM->M_b + 1) { col_blk_effective = m_PCM->N_b - m_PCM->M_b - 1; G_idx = 0; }
                }
            }
            else {
                col_blk_effective = col_blk - m_PCM->punct_col_num; G_idx = 0;
            }
        // Col Blk 0, 1 Puncturing Case
        /*
        if (col_blk > 3) { col_blk_effective = col_blk - 2; G_idx = 0; }
        else {
            if (mn % 2 == 0) {
                if (col_blk == 0) { col_blk_effective = 0;G_idx = 0; }
                else if (col_blk == 1) { col_blk_effective = 0;G_idx = 1; }
                else if (col_blk == 2) { col_blk_effective = 1;G_idx = 0; }
                else if (col_blk == 3) { col_blk_effective = 1;G_idx = 1; }
            }
            else {
                if (col_blk == 0) { col_blk_effective = 0;G_idx = 1; }
                else if (col_blk == 1) { col_blk_effective = 0;G_idx = 0; }
                else if (col_blk == 2) { col_blk_effective = 1;G_idx = 1; }
                else if (col_blk == 3) { col_blk_effective = 1;G_idx = 0; }
            }
        }
        */
        //fprintf(fp_VNU_OUT_HCU, "iter: %3d\tcol : %3d\tGroup : %d\n", mn, col_blk_effective, G_idx);
        for (ii = 0; ii < MAX_DV_GLOBAL_HALF; ii++) {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_VNU_OUT_HCU, "col : %3d\tmux_idx : %d\t", col_blk, ii);
#endif
            // sign (1bit x 256)
            for (kk = 0; kk < m_PCM->z_sb; kk = kk + HEX_BITS) {
                temp_bin4 = 1 * vnu_out[ii][n + 3 + kk]
                    + 2 * vnu_out[ii][n + 2 + kk]
                    + 4 * vnu_out[ii][n + 1 + kk]
                    + 8 * vnu_out[ii][n + 0 + kk];
                fprintf(fp_VNU_OUT_HCU, "%x", temp_bin4);
            }
            fprintf(fp_VNU_OUT_HCU, "\n");
        }
        for (ii = 0; ii < MAX_DV_GLOBAL_HALF; ii++) {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_VNU_OUT_HCU, "col : %3d\tmux_idx : %d\t", col_blk, ii);
#endif
            // mag (2bit x 256)
            for (kk = 0; kk < 2 * m_PCM->z_sb; kk = kk + HEX_BITS) {
                temp_bin4 = 1 * vnu_out[ii][n + m_PCM->z_sb + 3 + kk]
                    + 2 * vnu_out[ii][n + m_PCM->z_sb + 2 + kk]
                    + 4 * vnu_out[ii][n + m_PCM->z_sb + 1 + kk]
                    + 8 * vnu_out[ii][n + m_PCM->z_sb + kk];
                fprintf(fp_VNU_OUT_HCU, "%x", temp_bin4);
            }
            fprintf(fp_VNU_OUT_HCU, "\n");
        }
        fprintf(fp_VNU_OUT_HCU, "\n");
        for (ii = 0; ii < MAX_DV_GLOBAL_HALF; ii++) {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_VNU_OUT_HCU_in_mag, "[col : %3d\tmux_idx : %d]\t", col_blk, ii);
            fprintf(fp_VNU_OUT_HCU_in_sgn, "[col : %3d\tmux_idx : %d]\t", col_blk, ii);
            fprintf(fp_VNU_OUT_HCU_in_mag_nq, "[col : %3d\tmux_idx : %d]\t", col_blk, ii);
            fprintf(fp_VNU_OUT_HCU_in_sgn_nq, "[col : %3d\tmux_idx : %d]\t", col_blk, ii);
#endif
            for (kk = 0; kk < m_PCM->z_sb; kk++) {
                temp_bin4 = vnu_out_in[ii][col_blk * m_PCM->z_sb + kk];
                fprintf(fp_VNU_OUT_HCU_in_mag, "%d", abs(temp_bin4));
                if (temp_bin4>=0) fprintf(fp_VNU_OUT_HCU_in_sgn, "%d", 0);
                else fprintf(fp_VNU_OUT_HCU_in_sgn, "%d", 1);
                if (((kk + 1) % 8 == 0) && (kk + 1 < m_PCM->z_sb)) {
                    fprintf(fp_VNU_OUT_HCU_in_mag, "_");
                    fprintf(fp_VNU_OUT_HCU_in_sgn, "_");
                }
                temp_bin4 = vnu_out_in_nq[ii][col_blk * m_PCM->z_sb + kk];
                fprintf(fp_VNU_OUT_HCU_in_mag_nq, "%d ", abs(temp_bin4));
                if (temp_bin4 >= 0) fprintf(fp_VNU_OUT_HCU_in_sgn_nq, "%d", 0);
                else fprintf(fp_VNU_OUT_HCU_in_sgn_nq, "%d", 1);
                if (((kk + 1) % 8 == 0) && (kk + 1 < m_PCM->z_sb)) {
                    fprintf(fp_VNU_OUT_HCU_in_mag_nq, "_");
                    fprintf(fp_VNU_OUT_HCU_in_sgn_nq, "_");
                }
            }
            fprintf(fp_VNU_OUT_HCU_in_mag, "\n");
            fprintf(fp_VNU_OUT_HCU_in_sgn, "\n");
            fprintf(fp_VNU_OUT_HCU_in_mag_nq, "\n");
            fprintf(fp_VNU_OUT_HCU_in_sgn_nq, "\n");
        }
    }
    }
}
#endif
//=============================================
//
//=============================================
void TV_Dec_Inter::Print_TV_cnd_min(int* upt, int* val1, int* val2, int mn, int jj, int clk)
{
    int temp_i;
    int temp_bin4;
    int i, j;
    int z_sb = m_PCM->z_sb;
#if defined (__ECC_TV_ITER__)
    int pos = 0;
    int* active_row = new int[GT_HW_MAX_ROW];
    for (i = 0; i < GT_HW_MAX_ROW; i++) { active_row[i] = FALSE; }
    if (CYCLE_END != jj) {
        for (i = 0; i < m_PCM->ColW[jj]; i++) { active_row[m_PCM->V_net_b[jj][i]] = TRUE; }
    }
    if (CYCLE_END == jj) {
        fprintf(fp_MIN_UPT, "iter: %d\n", mn);
        fprintf(fp_MIN_VAL, "iter: %d\n", mn);
        fprintf(fp_MIN_VAL2, "iter: %d\n", mn);
    }
    else {
        fprintf(fp_MIN_UPT, "iter: %d\tcol: %d (clk : %d)\n", mn, jj, clk);
        fprintf(fp_MIN_VAL, "iter: %d\tcol: %d (clk : %d)\n", mn, jj, clk);
        fprintf(fp_MIN_VAL2, "iter: %d\tcol: %d (clk : %d)\n", mn, jj, clk);
    }
#endif
    temp_i = 0;
    for (i = 0; i < GT_HW_MAX_ROW; i++) {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_MIN_UPT, "row : %2d\t", i);
            fprintf(fp_MIN_VAL, "row : %2d\t", i);
            fprintf(fp_MIN_VAL2, "row : %2d\t", i);
#endif
        if (m_PCM->ar[i] == 1) {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_MIN_UPT, "active\t");
            fprintf(fp_MIN_VAL, "active\t");
            fprintf(fp_MIN_VAL2, "active\t");
            if (active_row[pos] == TRUE) {
                fprintf(fp_MIN_UPT, "active\t");
                fprintf(fp_MIN_VAL, "active\t");
                fprintf(fp_MIN_VAL2, "active\t");
            }
            else {
                fprintf(fp_MIN_UPT, "      \t");
                fprintf(fp_MIN_VAL, "      \t");
                fprintf(fp_MIN_VAL2, "      \t");
            }
            pos++;
#endif
            for (j = 0; j < z_sb; j = j + HEX_BITS) {
                temp_bin4 = 8 * upt[z_sb * temp_i + j]
                    + 4 * upt[z_sb * temp_i + j + 1]
                    + 2 * upt[z_sb * temp_i + j + 2]
                    + 1 * upt[z_sb * temp_i + j + 3];
                fprintf(fp_MIN_UPT, "%x", temp_bin4);
                //=============================================//
                temp_bin4 = 8 * ((val1[z_sb * temp_i + j] >> 1) & 0x01)
                    + 4 * (val1[z_sb * temp_i + j] & 0x01)
                    + 2 * ((val1[z_sb * temp_i + j + 1] >> 1) & 0x01)
                    + 1 * (val1[z_sb * temp_i + j + 1] & 0x01);
                fprintf(fp_MIN_VAL, "%x", temp_bin4);
                temp_bin4 = 8 * ((val1[z_sb * temp_i + j + 2] >> 1) & 0x01)
                    + 4 * (val1[z_sb * temp_i + j + 2] & 0x01)
                    + 2 * ((val1[z_sb * temp_i + j + 3] >> 1) & 0x01)
                    + 1 * (val1[z_sb * temp_i + j + 3] & 0x01);
                fprintf(fp_MIN_VAL, "%x", temp_bin4);
                temp_bin4 = 8 * ((val2[z_sb * temp_i + j] >> 1) & 0x01)
                    + 4 * (val2[z_sb * temp_i + j] & 0x01)
                    + 2 * ((val2[z_sb * temp_i + j + 1] >> 1) & 0x01)
                    + 1 * (val2[z_sb * temp_i + j + 1] & 0x01);
                fprintf(fp_MIN_VAL2, "%x", temp_bin4);
                temp_bin4 = 8 * ((val2[z_sb * temp_i + j + 2] >> 1) & 0x01)
                    + 4 * (val2[z_sb * temp_i + j + 2] & 0x01)
                    + 2 * ((val2[z_sb * temp_i + j + 3] >> 1) & 0x01)
                    + 1 * (val2[z_sb * temp_i + j + 3] & 0x01);
                fprintf(fp_MIN_VAL2, "%x", temp_bin4);
            }
            fprintf(fp_MIN_UPT, "\n");
            fprintf(fp_MIN_VAL, "\n");
            fprintf(fp_MIN_VAL2, "\n");
            temp_i++;
        }
        else {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_MIN_UPT, "      \t");
            fprintf(fp_MIN_VAL, "      \t");
            fprintf(fp_MIN_VAL2, "      \t");
            fprintf(fp_MIN_UPT, "      \t");
            fprintf(fp_MIN_VAL, "      \t");
            fprintf(fp_MIN_VAL2, "      \t");
#endif
            for (j = 0; j < z_sb; j = j + HEX_BITS) {
                temp_bin4 = 8 * upt[z_sb * temp_i + j]
                    + 4 * upt[z_sb * temp_i + j + 1]
                    + 2 * upt[z_sb * temp_i + j + 2]
                    + 1 * upt[z_sb * temp_i + j + 3];
                fprintf(fp_MIN_UPT, "%x", temp_bin4);
                //=============================================//
                temp_bin4 = 8 * ((val1[z_sb * temp_i + j] >> 1) & 0x01)
                    + 4 * (val1[z_sb * temp_i + j] & 0x01)
                    + 2 * ((val1[z_sb * temp_i + j + 1] >> 1) & 0x01)
                    + 1 * (val1[z_sb * temp_i + j + 1] & 0x01);
                fprintf(fp_MIN_VAL, "%x", temp_bin4);
                temp_bin4 = 8 * ((val1[z_sb * temp_i + j + 2] >> 1) & 0x01)
                    + 4 * (val1[z_sb * temp_i + j + 2] & 0x01)
                    + 2 * ((val1[z_sb * temp_i + j + 3] >> 1) & 0x01)
                    + 1 * (val1[z_sb * temp_i + j + 3] & 0x01);
                fprintf(fp_MIN_VAL, "%x", temp_bin4);
                //=============================================//
                temp_bin4 = 8 * ((val2[z_sb * temp_i + j] >> 1) & 0x01)
                    + 4 * (val2[z_sb * temp_i + j] & 0x01)
                    + 2 * ((val2[z_sb * temp_i + j + 1] >> 1) & 0x01)
                    + 1 * (val2[z_sb * temp_i + j + 1] & 0x01);
                fprintf(fp_MIN_VAL2, "%x", temp_bin4);
                temp_bin4 = 8 * ((val2[z_sb * temp_i + j + 2] >> 1) & 0x01)
                    + 4 * (val2[z_sb * temp_i + j + 2] & 0x01)
                    + 2 * ((val2[z_sb * temp_i + j + 3] >> 1) & 0x01)
                    + 1 * (val2[z_sb * temp_i + j + 3] & 0x01);
                fprintf(fp_MIN_VAL2, "%x", temp_bin4);
            }
            fprintf(fp_MIN_UPT, "\n");
            fprintf(fp_MIN_VAL, "\n");
            fprintf(fp_MIN_VAL2, "\n");
        }
    }
    fprintf(fp_MIN_UPT, "\n");
    fprintf(fp_MIN_VAL, "\n");
    fprintf(fp_MIN_VAL2, "\n");
#if defined (__ECC_TV_ITER__)
    delete[] active_row;
#endif
}
/*
void TV_Dec_Inter::Print_TV_cnd_min(int * upt, int * val1, int * val2, int mn, int jj, int clk)
{
    int temp_i, temp_j;
    int temp_bin4;
    int i, j;
    int z_sb = m_PCM->z_sb;
#if defined (__ECC_TV_ITER__)
    int pos = 0;
    int * active_row = new int[GT_HW_MAX_ROW];
    for (i = 0; i < GT_HW_MAX_ROW; i++) { active_row[i] = FALSE; }
    if (CYCLE_END != jj) {
        for (i = 0; i < m_PCM->ColW[jj]; i++) { active_row[m_PCM->V_net_b[jj][i]] = TRUE; }
    }
    if (CYCLE_END == jj) {
        fprintf(fp_MIN_UPT, "iter: %d\n", mn);
        fprintf(fp_MIN_VAL, "iter: %d\n", mn);
        fprintf(fp_MIN_VAL2, "iter: %d\n", mn);
    }
    else {
        fprintf(fp_MIN_UPT, "iter: %d\tcol: %d (clk : %d)\n", mn, jj, clk);
        fprintf(fp_MIN_VAL, "iter: %d\tcol: %d (clk : %d)\n", mn, jj, clk);
        fprintf(fp_MIN_VAL2, "iter: %d\tcol: %d (clk : %d)\n", mn, jj, clk);
    }
#endif
    temp_i = 0;
    temp_j = 0;
    for (i = 0; i < GT_HW_MAX_ROW; i++) {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_MIN_UPT, "row : %2d\t", i);
            fprintf(fp_MIN_VAL, "row : %2d\t", i);
            fprintf(fp_MIN_VAL2, "row : %2d\t", i);
#endif
        if (m_PCM->ar[i] == 1) {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_MIN_UPT, "active\t");
            fprintf(fp_MIN_VAL, "active\t");
            fprintf(fp_MIN_VAL2, "active\t");
            if (active_row[pos] == TRUE) {
                fprintf(fp_MIN_UPT, "active\t");
                fprintf(fp_MIN_VAL, "active\t");
                fprintf(fp_MIN_VAL2, "active\t");
            }
            else {
                fprintf(fp_MIN_UPT, "      \t");
                fprintf(fp_MIN_VAL, "      \t");
                fprintf(fp_MIN_VAL2, "      \t");
            }
            pos++;
#endif
            for (j = 0; j < z_sb; j = j + HEX_BITS) {
                temp_bin4 =   8 * upt[(z_sb * temp_i) + j]
                    + 4 * upt[(z_sb * temp_i) + j + 1]
                    + 2 * upt[(z_sb * temp_i) + j + 2]
                    + 1 * upt[(z_sb * temp_i) + j + 3];
                fprintf(fp_MIN_UPT, "%x", temp_bin4);
            }
            fprintf(fp_MIN_UPT, "\n");
            temp_i++;
            for (j = 0; j < z_sb; j++) {
                temp_bin4 =   4 * ((val1[(z_sb * temp_j) + j] >> 2) & 0x01)
                    + 2 * ((val1[(z_sb * temp_j) + j] >> 1) & 0x01)
                    + 1 * ( val1[(z_sb * temp_j) + j]       & 0x01);
                fprintf(fp_MIN_VAL, "%x", temp_bin4);
                temp_bin4 =   4 * ((val2[(z_sb * temp_j) + j] >> 2) & 0x01)
                    + 2 * ((val2[(z_sb * temp_j) + j] >> 1) & 0x01)
                    + 1 * ( val2[(z_sb * temp_j) + j]       & 0x01);
                fprintf(fp_MIN_VAL2, "%x", temp_bin4);
            }
            fprintf(fp_MIN_VAL, "\n");
            fprintf(fp_MIN_VAL2, "\n");
            temp_j++;
        }
        else {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_MIN_UPT, "      \t");
            fprintf(fp_MIN_VAL, "      \t");
            fprintf(fp_MIN_VAL2, "      \t");
            fprintf(fp_MIN_UPT, "      \t");
            fprintf(fp_MIN_VAL, "      \t");
            fprintf(fp_MIN_VAL2, "      \t");
#endif
            for (j = 0; j < z_sb; j = j + HEX_BITS) {
                temp_bin4 =   8 * upt[(z_sb * temp_i) + j]
                    + 4 * upt[(z_sb * temp_i) + j + 1]
                    + 2 * upt[(z_sb * temp_i) + j + 2]
                    + 1 * upt[(z_sb * temp_i) + j + 3];
                fprintf(fp_MIN_UPT, "%x", temp_bin4);
            }
            fprintf(fp_MIN_UPT, "\n");
            temp_i++;
            for (j = 0; j < z_sb; j++) {
                temp_bin4 =   4 * ((val1[(z_sb * temp_j) + j] >> 2) & 0x01)
                    + 2 * ((val1[(z_sb * temp_j) + j] >> 1) & 0x01)
                    + 1 * ( val1[(z_sb * temp_j) + j]       & 0x01);
                fprintf(fp_MIN_VAL, "%x", temp_bin4);
                temp_bin4 =   4 * ((val2[(z_sb * temp_j) + j] >> 2) & 0x01)
                    + 2 * ((val2[(z_sb * temp_j) + j] >> 1) & 0x01)
                    + 1 * ( val2[(z_sb * temp_j) + j]       & 0x01);
                fprintf(fp_MIN_VAL2, "%x", temp_bin4);
                //=============================================//
//              temp_bin4 = 8 * ((val1[(z_sb * temp_j) + j + 0] >> 1)   & 0x01)
//                  + 4 * ( val1[(z_sb * temp_j) + j + 0]               & 0x01)
//                  + 2 * ((val1[(z_sb * temp_j) + j + 1] >> 1)         & 0x01)
//                  + 1 * ( val1[(z_sb * temp_j) + j + 1]               & 0x01);
//              fprintf(fp_MIN_VAL, "%x", temp_bin4);
//
//              temp_bin4 = 8 * ((val1[(z_sb * temp_j) + j + 2] >> 1)   & 0x01)
//                  + 4 * ( val1[(z_sb * temp_j) + j + 2]               & 0x01)
//                  + 2 * ((val1[(z_sb * temp_j) + j + 3] >> 1)         & 0x01)
//                  + 1 * ( val1[(z_sb * temp_j) + j + 3]               & 0x01);
//              fprintf(fp_MIN_VAL, "%x", temp_bin4);
//
//              //=============================================//
//              temp_bin4 = 8 * ((val2[(z_sb * temp_j) + j] >> 1)       & 0x01)
//                  + 4 * ( val2[(z_sb * temp_j) + j]                   & 0x01)
//                  + 2 * ((val2[(z_sb * temp_j) + j + 1] >> 1)         & 0x01)
//                  + 1 * ( val2[(z_sb * temp_j) + j + 1]               & 0x01);
//              fprintf(fp_MIN_VAL2, "%x", temp_bin4);
//
//              temp_bin4 = 8 * ((val2[(z_sb * temp_j) + j + 2] >> 1) & 0x01)
//                  + 4 * ( val2[(z_sb * temp_j) + j + 2]             & 0x01)
//                  + 2 * ((val2[(z_sb * temp_j) + j + 3] >> 1) & 0x01)
//                  + 1 * ( val2[(z_sb * temp_j) + j + 3]             & 0x01);
//              fprintf(fp_MIN_VAL2, "%x", temp_bin4);
            }
            fprintf(fp_MIN_VAL, "\n");
            fprintf(fp_MIN_VAL2, "\n");
            temp_j++;
        }
    }
    fprintf(fp_MIN_UPT, "\n");
    fprintf(fp_MIN_VAL, "\n");
    fprintf(fp_MIN_VAL2, "\n");
#if defined (__ECC_TV_ITER__)
    delete[] active_row;
#endif
}*/
//=============================================
// full crc flag output (0,1)
//=============================================
void TV_Dec_Inter::Print_TV_crc_flag(int CRC_flag)
{
    fprintf(fp_RESULT, "%x\n", CRC_flag);
}
//=============================================
// iter_num output (HEX 3bit)
//=============================================
void TV_Dec_Inter::Print_TV_iter_num(int iter_num)
{
    fprintf(fp_RESULT, "%03x\n", iter_num);
}
//=============================================
// info_err_count output (HEX 3bit)
//=============================================
void TV_Dec_Inter::Print_TV_info_err_cnt(int info_err_count)
{
    fprintf(fp_RESULT, "%03x\n", info_err_count);
}
//=============================================
// str_err_count output (HEX 3bit)
//=============================================
void TV_Dec_Inter::Print_TV_strong_err_cnt(int str_err_count)
{
    fprintf(fp_RESULT, "%03x\n", str_err_count);
}
//=============================================
// str_err_count output (HEX 4bit)
//=============================================
void TV_Dec_Inter::Print_TV_weak_cor_cnt(int weak_cor_count)
{
    fprintf(fp_RESULT, "%04x\n", weak_cor_count);
}
//=============================================
// BF_on_flag output (0,1)
//=============================================
void TV_Dec_Inter::Print_TV_BF_on_flag(int BF_on_flag)
{
    fprintf(fp_RESULT, "%d\n", BF_on_flag);
}
//=============================================
// idx_PCRC_termination output (0,1,2,3)
//=============================================
void TV_Dec_Inter::Print_TV_PCRC_termination(int idx_PCRC_termination)
{
    fprintf(fp_RESULT, "%03x\n", idx_PCRC_termination);
}
//=============================================
// 0 or 1 flip bit output (HEX 3bit)
//=============================================
void TV_Dec_Inter::Print_TV_flip_cnt(int flip_counter)
{
    fprintf(fp_RESULT, "%03x\n", flip_counter);
}
//=============================================
// 1 bit output (HEX 4bit)
//=============================================
void TV_Dec_Inter::Print_TV_bit_cnt(int bit_counter)
{
    fprintf(fp_RESULT, "%04x\n", bit_counter);
}
//=============================================
// endl
//=============================================
void TV_Dec_Inter::Print_TV_cfp_flag_endl()
{
    fprintf(fp_RESULT, "\n");
}
//=============================================
// min pos output
//=============================================
void TV_Dec_Inter::Print_TV_min_pos(int * min_pos, int mn)
{
    int i, j;
    int z_sb = m_PCM->z_sb;
#if defined (__ECC_TV_ITER__)
    fprintf(fp_MIN_POS, "iter: %d\n", mn);
#endif
    for (i = 0; i < GT_HW_MAX_ROW; i++) {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_MIN_POS, "row : %2d\t", i);
#endif
        if (m_PCM->ar[i] == 1) {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_MIN_POS, "active\t");
#endif
            for (j = 0; j < z_sb; j++) {
                //printf("min_pos(i=%d, j=%d)=%d (%02x)\n",i,j, min_pos[i * z_sb + j], min_pos[i * z_sb + j]);
                fprintf(fp_MIN_POS, "%02x", min_pos[i * z_sb + j]);
            }
            fprintf(fp_MIN_POS, "\n");
        }
        else {
#if defined (__ECC_TV_ITER__)
            fprintf(fp_MIN_POS, "      \t");
#endif
            for (j = 0; j < z_sb; j++) {
                fprintf(fp_MIN_POS, "%02x", 0);
            }
            fprintf(fp_MIN_POS, "\n");
        }
    }
#if defined (__ECC_TV_ITER__)
    fprintf(fp_MIN_POS, "\n");
#endif
}
