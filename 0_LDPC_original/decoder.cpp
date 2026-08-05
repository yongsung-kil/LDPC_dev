#include "Decoder.h"
//=============================================
// 생성자
//=============================================
Decoder::Decoder()
{
    Initialize_Dec();
}
//=============================================
// 소멸자
//=============================================
Decoder::~Decoder()
{
    Release_Dec();
}
//=============================================
// Initialize pointers
//=============================================
void Decoder::Initialize_Dec()
{
    /* pointers */
    m_ecc_info = NULL;
    m_PCM = NULL;
    m_param_dec = NULL;
    REG_min1_pos = NULL;
    REG_min1_value = NULL;
    REG_min2_value = NULL;
    Check_SRAM_sgn = NULL;
    Check_REG = NULL;
    Variable_mem = NULL;
    z_mem_shift = NULL;
    VNU_in = NULL;
    VNU_out = NULL;
    VNU_out2 = NULL;
    VNU_out3 = NULL;
    VNU_out_nq = NULL;
    VNU_out2_nq = NULL;
    VNU_out3_nq = NULL;
    VNU_out3_temp = NULL;
    Sum_t_OLD_G0 = NULL;
    Sum_t_OLD_G1 = NULL;
    pre_exist_sgn_reg = NULL;
    pre_exist_sgn_reg2 = NULL;
    pre_exist_sgn_reg3 = NULL;
    pre_exist_sgn_reg_BS = NULL;
    pre_exist_sgn_reg2_BS = NULL;
    pre_exist_sgn_reg3_BS = NULL;
    Syndrome = NULL;
    Syndrome_intermediate = NULL;
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
    Syndrome_intermediate_internal = NULL;
    Punc_vote_Mag = NULL;
    Punc_vote_Mag_Row = NULL;
    Punc_vote_Mag_Row_before_BS = NULL;
    Punc_vote_decision = NULL;
#endif
    cwc = NULL;
    prev_cwc = NULL;
    PMU_SRAM = NULL;
    FIFO_level = NULL;
    MAIN_SRAM_read_rq = NULL;
    MAIN_SRAM_read_rq2 = NULL;
    MAIN_SRAM_write_rq = NULL;
    Soft_LLR = NULL;
    Soft_LLR_weak_degree = NULL;
    Soft_LLR_PRIME = NULL;
    CD = NULL;
    dec_d = NULL;
    lfsr_TP1 = NULL;
    lfsr_TP2 = NULL;
    lfsr_TP3 = NULL;
    lfsr_TP4 = NULL;
    pcrc_checksum = NULL;
    crc_dec_LFSR_iter = NULL;
    m_genie_inv_cw = NULL;
    //PR_bit_flip_cnt = NULL;
    PR_weak_cnt0 = NULL;
    PR_weak_cnt1 = NULL;
    PR_weak_cnt2 = NULL;
    PR_weak_cnt3 = NULL;
    PR_weak_cnt0_acc = NULL;
    PR_weak_cnt1_acc = NULL;
    PR_weak_cnt2_acc = NULL;
    PR_weak_cnt3_acc = NULL;
#if defined (__ECC_TV__)
    tv_llr_out = NULL;
    tv_vtc_inp = NULL;
    tv_old_mag = NULL;
    tv_old_sgn = NULL;
    tv_upt_min = NULL;
    tv_min_weak = NULL;
    tv_min_weak2 = NULL;
    tv_new_sgn_mag = NULL;
    crc_dec_LFSR_internal = NULL;
    Punc_one_cnt = NULL;
#if defined(__HALF_COL_UPDATE__)
    tv_vtc_inp_HCU = NULL;
    tv_new_sgn_mag_HCU = NULL;
    tv_new_sgn_mag_HCU_in = NULL;
    tv_new_sgn_mag_HCU_in2 = NULL;
    tv_new_sgn_mag_HCU_in3 = NULL;
    tv_new_sgn_mag_HCU_in_nq = NULL;
    tv_new_sgn_mag_HCU_in2_nq = NULL;
    tv_new_sgn_mag_HCU_in3_nq = NULL;
    tv_old_sgn_HCU = NULL;
#endif
#endif
    m_TV_cycle_based_on = TRUE;
    m_log_VNU_in = NULL;
    m_log_VNU_out = NULL;
    m_log_sum_t = NULL;
    m_log_ch_llr = NULL;
}
//=============================================
// Dynamic memory allocation
//=============================================
void Decoder::Alloc_Dec()
{
    int i, j;
    int tot_PMU_len;
    int factor;
    int PMU_inst_num;
    int N = m_PCM->N;
    int M = m_PCM->M;
    int K = m_PCM->K;
    int J = m_PCM->J;
    int z_sb = m_PCM->z_sb;
    REG_min1_pos = new int[M];
    REG_min1_value = new int[M];
    REG_min2_value = new int[M];
    Check_SRAM_sgn = new int*[M]; for (i = 0; i < M; i++) Check_SRAM_sgn[i] = new int[K];
    Check_REG = new int*[M]; for (i = 0; i < M; i++) Check_REG[i] = new int[2];
    Variable_mem = new int[N];
    z_mem_shift = new int[z_sb];
    VNU_in = new int*[J]; for (i = 0; i < J; i++) VNU_in[i] = new int[z_sb];
    VNU_out = new int*[J]; for (i = 0; i < J; i++) VNU_out[i] = new int[z_sb];
    VNU_out2 = new int*[J]; for (i = 0; i < J; i++) VNU_out2[i] = new int[z_sb];
    VNU_out3 = new int*[J]; for (i = 0; i < J; i++) VNU_out3[i] = new int[z_sb];
    VNU_out_nq = new int* [J]; for (i = 0; i < J; i++) VNU_out_nq[i] = new int[z_sb];
    VNU_out2_nq = new int* [J]; for (i = 0; i < J; i++) VNU_out2_nq[i] = new int[z_sb];
    VNU_out3_nq = new int* [J]; for (i = 0; i < J; i++) VNU_out3_nq[i] = new int[z_sb];
    VNU_out3_temp = new int*[J]; for (i = 0; i < J; i++) VNU_out3_temp[i] = new int[z_sb];
    Sum_t_OLD_G0 = new int* [m_PCM->punct_col_num]; for (i = 0;i < m_PCM->punct_col_num;i++) Sum_t_OLD_G0[i] = new int[z_sb];
    Sum_t_OLD_G1 = new int* [m_PCM->punct_col_num]; for (i = 0;i < m_PCM->punct_col_num;i++) Sum_t_OLD_G1[i] = new int[z_sb];
    pre_exist_sgn_reg = new int*[J]; for (i = 0; i < J; i++) pre_exist_sgn_reg[i] = new int[z_sb];
    pre_exist_sgn_reg2 = new int*[J]; for (i = 0; i < J; i++) pre_exist_sgn_reg2[i] = new int[z_sb];
    pre_exist_sgn_reg3 = new int*[J]; for (i = 0; i < J; i++) pre_exist_sgn_reg3[i] = new int[z_sb];
    pre_exist_sgn_reg_BS = new int*[J]; for (i = 0; i < J; i++) pre_exist_sgn_reg_BS[i] = new int[z_sb];
    pre_exist_sgn_reg2_BS = new int*[J]; for (i = 0; i < J; i++) pre_exist_sgn_reg2_BS[i] = new int[z_sb];
    pre_exist_sgn_reg3_BS = new int*[J]; for (i = 0; i < J; i++) pre_exist_sgn_reg3_BS[i] = new int[z_sb];
    Syndrome = new int[M];
    Syndrome_intermediate = new int[M];
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
    Syndrome_intermediate_internal = new int*[m_PCM->N_b];
    for (i = 0;i < m_PCM->N_b;i++) Syndrome_intermediate_internal[i] = new int[m_PCM->M];
    //Syndrome_intermediate_internal = new int* [m_PCM->N_b - m_PCM->punct_col_num];
    //for (i = 0; i < m_PCM->N_b - m_PCM->punct_col_num; i++) Syndrome_intermediate_internal[i] = new int[m_PCM->M];
    Punc_vote_Mag = new int* [m_PCM->punct_col_num];
    for (i = 0;i < m_PCM->punct_col_num;i++) Punc_vote_Mag[i] = new int[m_PCM->z_sb];
    Punc_vote_Mag_Row = new int** [m_PCM->punct_col_num];
    for (i = 0;i < m_PCM->punct_col_num;i++) Punc_vote_Mag_Row[i] = new int* [m_PCM->M_b];
    for (i = 0;i < m_PCM->punct_col_num;i++) {
        for (j = 0;j < m_PCM->M_b;j++) Punc_vote_Mag_Row[i][j] = new int[m_PCM->z_sb];
    }
    Punc_vote_Mag_Row_before_BS = new int** [m_PCM->punct_col_num];
    for (i = 0;i < m_PCM->punct_col_num;i++) Punc_vote_Mag_Row_before_BS[i] = new int* [m_PCM->M_b];
    for (i = 0;i < m_PCM->punct_col_num;i++) {
        for (j = 0;j < m_PCM->M_b;j++) Punc_vote_Mag_Row_before_BS[i][j] = new int[m_PCM->z_sb];
    }
    Punc_vote_decision = new int* [m_PCM->punct_col_num];
    for (i = 0;i < m_PCM->punct_col_num;i++) Punc_vote_decision[i] = new int[m_PCM->z_sb];
#endif
    cwc = new int[N];
    prev_cwc = new int[m_PCM->punct_col_num* m_PCM->z_sb];
#if defined(__HALF_COL_UPDATE__)
    factor = z_sb / PMU_UNIT_SIZE;
    PMU_inst_num = factor * MAX_DV_GLOBAL_HALF;
    tot_PMU_len = PMU_inst_num * PMU_UNIT_WIDTH;
    PMU_SRAM = new int* [m_PCM->N_b+m_PCM->punct_col_num];
    for (i = 0; i < m_PCM->N_b + m_PCM->punct_col_num; i++) { PMU_SRAM[i] = new int[tot_PMU_len]; }
    FIFO_level = new int[PMU_inst_num];
    MAIN_SRAM_read_rq = new int[PMU_inst_num];
    MAIN_SRAM_read_rq2 = new int[PMU_inst_num];
    MAIN_SRAM_write_rq = new int[PMU_inst_num];
    HCU_start = m_PCM->N_b - m_PCM->M_b - m_PCM->punct_col_num;
    HCU_end = m_PCM->N_b - m_PCM->M_b - 1;
#else
    factor = z_sb / PMU_UNIT_SIZE;
    PMU_inst_num = factor * MAX_DV_GLOBAL;
    tot_PMU_len = PMU_inst_num * PMU_UNIT_WIDTH;
    PMU_SRAM = new int* [m_PCM->N_b];
    for (i = 0; i < m_PCM->N_b; i++) { PMU_SRAM[i] = new int[tot_PMU_len]; }
    FIFO_level = new int[PMU_inst_num];
    MAIN_SRAM_read_rq = new int[PMU_inst_num];
    MAIN_SRAM_read_rq2 = new int[PMU_inst_num];
    MAIN_SRAM_write_rq = new int[PMU_inst_num];
#endif
    Soft_LLR = new int[N];
    Soft_LLR_weak_degree = new int[N];
    Soft_LLR_PRIME = new int[N];
    CD = new int[N];
    // Partial CRC
    dec_d = new int[DEC_D_LEN];
    lfsr_TP1 = new int[CRC_LEN];
    lfsr_TP2 = new int[CRC_LEN];
    lfsr_TP3 = new int[CRC_LEN];
    lfsr_TP4 = new int[CRC_LEN];
    pcrc_checksum = new int[CRC_LEN];
    m_genie_inv_cw = new int[N];
    //PR_bit_flip_cnt = new int[m_PCM->punct_col_num * m_PCM->z_sb];
    PR_weak_cnt0 = new int[m_PCM->z_sb];
    PR_weak_cnt1 = new int[m_PCM->z_sb];
    PR_weak_cnt2 = new int[m_PCM->z_sb];
    PR_weak_cnt3 = new int[m_PCM->z_sb];
    PR_weak_cnt0_acc = new int[m_PCM->z_sb];
    PR_weak_cnt1_acc = new int[m_PCM->z_sb];
    PR_weak_cnt2_acc = new int[m_PCM->z_sb];
    PR_weak_cnt3_acc = new int[m_PCM->z_sb];
#if defined (__ECC_TV__)
    tv_llr_out = new int[N];
#if defined(__4_BIT_LLR__)
    /*  4-bit precision: sign 1, mag 3 */
    tv_vtc_inp = new int* [MAX_DV_GLOBAL];  for (i = 0; i < MAX_DV_GLOBAL; i++) tv_vtc_inp[i] = new int[4 * N];
    tv_new_sgn_mag = new int* [MAX_DV_GLOBAL];  for (i = 0; i < MAX_DV_GLOBAL; i++) tv_new_sgn_mag[i] = new int[4 * N];
#else
    /*  3-bit precision: sign 1, mag 2 */
    tv_vtc_inp = new int* [MAX_DV_GLOBAL];                  for (i = 0; i < MAX_DV_GLOBAL; i++)    tv_vtc_inp[i] = new int[3 * N];
    tv_new_sgn_mag = new int* [MAX_DV_GLOBAL];              for (i = 0; i < MAX_DV_GLOBAL; i++)    tv_new_sgn_mag[i] = new int[3 * N];
#if defined(__HALF_COL_UPDATE__)
    tv_vtc_inp_HCU = new int* [MAX_DV_GLOBAL_HALF];        for (i = 0; i < MAX_DV_GLOBAL_HALF; i++) tv_vtc_inp_HCU[i] = new int[3 * (N + m_PCM->punct_col_num * m_PCM->z_sb)];
    tv_new_sgn_mag_HCU = new int* [MAX_DV_GLOBAL_HALF];    for (i = 0; i < MAX_DV_GLOBAL_HALF; i++) tv_new_sgn_mag_HCU[i] = new int[3 * (N + m_PCM->punct_col_num * m_PCM->z_sb)];
    tv_new_sgn_mag_HCU_in = new int* [MAX_DV_GLOBAL_HALF];  for (i = 0; i < MAX_DV_GLOBAL_HALF; i++) tv_new_sgn_mag_HCU_in[i] = new int[N + m_PCM->punct_col_num * m_PCM->z_sb];
    tv_new_sgn_mag_HCU_in2 = new int* [MAX_DV_GLOBAL_HALF];  for (i = 0; i < MAX_DV_GLOBAL_HALF; i++) tv_new_sgn_mag_HCU_in2[i] = new int[N + m_PCM->punct_col_num * m_PCM->z_sb];
    tv_new_sgn_mag_HCU_in3 = new int* [MAX_DV_GLOBAL_HALF];  for (i = 0; i < MAX_DV_GLOBAL_HALF; i++) tv_new_sgn_mag_HCU_in3[i] = new int[N + m_PCM->punct_col_num * m_PCM->z_sb];
    tv_new_sgn_mag_HCU_in_nq = new int* [MAX_DV_GLOBAL_HALF];  for (i = 0; i < MAX_DV_GLOBAL_HALF; i++) tv_new_sgn_mag_HCU_in_nq[i] = new int[N + m_PCM->punct_col_num * m_PCM->z_sb];
    tv_new_sgn_mag_HCU_in2_nq = new int* [MAX_DV_GLOBAL_HALF];  for (i = 0; i < MAX_DV_GLOBAL_HALF; i++) tv_new_sgn_mag_HCU_in2_nq[i] = new int[N + m_PCM->punct_col_num * m_PCM->z_sb];
    tv_new_sgn_mag_HCU_in3_nq = new int* [MAX_DV_GLOBAL_HALF];  for (i = 0; i < MAX_DV_GLOBAL_HALF; i++) tv_new_sgn_mag_HCU_in3_nq[i] = new int[N + m_PCM->punct_col_num * m_PCM->z_sb];
#endif
#endif
    tv_old_mag = new int*[MAX_DV_GLOBAL];
    tv_old_sgn = new int*[MAX_DV_GLOBAL];
    for (i = 0; i < MAX_DV_GLOBAL; i++) {
        tv_old_mag[i] = new int[N];
        tv_old_sgn[i] = new int[N];
    }
#if defined(__HALF_COL_UPDATE__)
    tv_old_sgn_HCU = new int* [MAX_DV_GLOBAL_HALF];
    for (i = 0; i < MAX_DV_GLOBAL_HALF; i++) {
        tv_old_sgn_HCU[i] = new int[N + m_PCM->punct_col_num * m_PCM->z_sb];
    }
#endif
    int hw_row_num = GT_HW_MAX_ROW * z_sb;
    tv_upt_min = new int[hw_row_num];
    tv_min_weak = new int[hw_row_num];
    tv_min_weak2 = new int[hw_row_num];
    Punc_one_cnt = new int[N];
    crc_dec_LFSR_internal = new int*[4 * (m_PCM->N_b- m_PCM->M_b)];
    for (i = 0; i < 4 * (m_PCM->N_b - m_PCM->M_b); i++)
        crc_dec_LFSR_internal[i] = new int[CRC_LEN];
#endif
    Alloc_Log_Data();
    m_log_VNU_in = new int*[J]; for (i = 0; i < J; i++) m_log_VNU_in[i] = new int[N];
    m_log_VNU_out = new int*[J]; for (i = 0; i < J; i++) m_log_VNU_out[i] = new int[N];
    m_log_sum_t = new int[N];
    m_log_ch_llr = new int[N];
}
//=============================================
// Release memory
//=============================================
void Decoder::Release_Dec()
{
    int i, j;
    int M = m_PCM->M;
    int J = m_PCM->J;
    delete[] REG_min1_pos;
    delete[] REG_min1_value;
    delete[] REG_min2_value;
    for (i = 0; i < M; i++) {
        delete[] Check_SRAM_sgn[i];
        delete[] Check_REG[i];
    }
    delete[] Check_SRAM_sgn;
    delete[] Check_REG;
    delete[] Variable_mem;
    delete[] z_mem_shift;
    for (i = 0; i < J; i++) {
        delete[] VNU_in[i];
        delete[] VNU_out[i];
        delete[] VNU_out2[i];
        delete[] VNU_out3[i];
        delete[] VNU_out_nq[i];
        delete[] VNU_out2_nq[i];
        delete[] VNU_out3_nq[i];
        delete[] VNU_out3_temp[i];
    }
    delete[] VNU_in;    delete[] VNU_out;    delete[] VNU_out2; delete[] VNU_out3; delete[] VNU_out3_temp;
    delete[] VNU_out_nq;    delete[] VNU_out2_nq;  delete[] VNU_out3_nq;
    for (i = 0;i < m_PCM->punct_col_num;i++) delete[] Sum_t_OLD_G0[i];
    delete[] Sum_t_OLD_G0;
    for (i = 0;i < m_PCM->punct_col_num;i++) delete[] Sum_t_OLD_G1[i];
    delete[] Sum_t_OLD_G1;
    for (i = 0; i < J; i++) {
        delete[] pre_exist_sgn_reg[i];
        delete[] pre_exist_sgn_reg2[i];
        delete[] pre_exist_sgn_reg3[i];
        delete[] pre_exist_sgn_reg_BS[i];
        delete[] pre_exist_sgn_reg2_BS[i];
        delete[] pre_exist_sgn_reg3_BS[i];
    }
    delete[] pre_exist_sgn_reg; delete[] pre_exist_sgn_reg2; delete[] pre_exist_sgn_reg3;
    delete[] pre_exist_sgn_reg_BS; delete[] pre_exist_sgn_reg2_BS; delete[] pre_exist_sgn_reg3_BS;
    delete[] Syndrome;
    delete[] Syndrome_intermediate;
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
    for (i = 0;i < m_PCM->N_b;i++) delete[] Syndrome_intermediate_internal[i];
    //for (i = 0; i < m_PCM->N_b - m_PCM->punct_col_num; i++) delete[] Syndrome_intermediate_internal[i];
    delete[] Syndrome_intermediate_internal;
    for (i = 0;i < m_PCM->punct_col_num;i++) delete[] Punc_vote_Mag[i];
    delete[] Punc_vote_Mag;
    for (i = 0;i < m_PCM->punct_col_num;i++) {
        for (j = 0;j < m_PCM->M_b;j++) {
            delete[] Punc_vote_Mag_Row[i][j];
            delete[] Punc_vote_Mag_Row_before_BS[i][j];
        }
        delete[] Punc_vote_Mag_Row[i];
        delete[] Punc_vote_Mag_Row_before_BS[i];
    }
    delete[] Punc_vote_Mag_Row;
    delete[] Punc_vote_Mag_Row_before_BS;
    for (i = 0;i < m_PCM->punct_col_num;i++) delete[] Punc_vote_decision[i];
    delete[] Punc_vote_decision;
#endif
    delete[] cwc;
    delete[] prev_cwc;
    //for (int tt = 0; tt < 10; tt++) {
    //  delete[] out_err_cnt[tt];
    //}
    //delete[] out_err_cnt;
#if defined(__HALF_COL_UPDATE__)
    for (i = 0; i < m_PCM->N_b+ m_PCM->punct_col_num; i++) {
        delete[] PMU_SRAM[i];
    }
#else
    for (i = 0; i < m_PCM->N_b; i++) {
        delete[] PMU_SRAM[i];
    }
#endif
    delete[] PMU_SRAM;
    delete[] FIFO_level;
    delete[] MAIN_SRAM_read_rq;
    delete[] MAIN_SRAM_read_rq2;
    delete[] MAIN_SRAM_write_rq;
    delete[] Soft_LLR;
    delete[] Soft_LLR_weak_degree;
    delete[] Soft_LLR_PRIME;
    delete[] CD;
    // Partial CRC
    delete[] dec_d;
    delete[] lfsr_TP1;
    delete[] lfsr_TP2;
    delete[] lfsr_TP3;
    delete[] lfsr_TP4;
    delete[] pcrc_checksum;
    delete[] crc_dec_LFSR_iter;
    delete[] m_genie_inv_cw;
    //delete[] PR_bit_flip_cnt;
    delete[] PR_weak_cnt0;
    delete[] PR_weak_cnt1;
    delete[] PR_weak_cnt2;
    delete[] PR_weak_cnt3;
    delete[] PR_weak_cnt0_acc;
    delete[] PR_weak_cnt1_acc;
    delete[] PR_weak_cnt2_acc;
    delete[] PR_weak_cnt3_acc;
#if defined (__ECC_TV__)
    delete[] tv_llr_out;
    for (i = 0; i < J; i++) {
        delete[] tv_vtc_inp[i];
        delete[] tv_old_mag[i];
        delete[] tv_old_sgn[i];
        delete[] tv_new_sgn_mag[i];
    }
    delete[] tv_vtc_inp;
    delete[] tv_old_mag;
    delete[] tv_old_sgn;
    delete[] tv_upt_min;
    delete[] tv_min_weak;
    delete[] tv_min_weak2;
    delete[] tv_new_sgn_mag;
    for (i = 0; i < 4 * (m_PCM->N_b - m_PCM->M_b); i++) {
        delete[] crc_dec_LFSR_internal[i];
    }
    delete[] crc_dec_LFSR_internal;
    delete[] Punc_one_cnt;
#if defined(__HALF_COL_UPDATE__)
    for (i = 0;i < MAX_DV_GLOBAL_HALF;i++) {
        delete[] tv_vtc_inp_HCU[i];
        delete[] tv_new_sgn_mag_HCU[i];
        delete[] tv_new_sgn_mag_HCU_in[i];
        delete[] tv_new_sgn_mag_HCU_in2[i];
        delete[] tv_new_sgn_mag_HCU_in3[i];
        delete[] tv_old_sgn_HCU[i];
        delete[] tv_new_sgn_mag_HCU_in_nq[i];
        delete[] tv_new_sgn_mag_HCU_in2_nq[i];
        delete[] tv_new_sgn_mag_HCU_in3_nq[i];
    }
    delete[] tv_vtc_inp_HCU;
    delete[] tv_new_sgn_mag_HCU;
    delete[] tv_new_sgn_mag_HCU_in;
    delete[] tv_new_sgn_mag_HCU_in2;
    delete[] tv_new_sgn_mag_HCU_in3;
    delete[] tv_new_sgn_mag_HCU_in_nq;
    delete[] tv_new_sgn_mag_HCU_in2_nq;
    delete[] tv_new_sgn_mag_HCU_in3_nq;
    delete[] tv_old_sgn_HCU;
#endif
#endif
    Release_Log_Data();
    for (i = 0; i < J; i++) {
        delete[] m_log_VNU_in[i];
        delete[] m_log_VNU_out[i];
    }
    delete[] m_log_VNU_in;
    delete[] m_log_VNU_out;
    delete[] m_log_sum_t;
    delete[] m_log_ch_llr;
}
//=============================================
// Set parameters of decoder
//=============================================
void Decoder::Init_Dec(ECC_INFO* info, PCM* pcm, PARAM_DEC* param, PARAM_LLR* param_LLR, int myrank)
{
    m_ecc_info = info;
    m_PCM = pcm;
    m_param_dec = param;
    m_param_LLR = param_LLR;
    m_myrank = myrank;
    /* dynamic memory allocation */
    Alloc_Dec();
}
void Decoder::Init_Dec(ECC_INFO* info, PCM* pcm, PARAM_DEC* param, int myrank)
{
    m_ecc_info = info;
    m_PCM = pcm;
    m_param_dec = param;
    /* dynamic memory allocation */
    Alloc_Dec();
}
//=============================================
// Set decoder options
//=============================================
void Decoder::Init_Dec_Option()
{
    int i;
    int MN_max;
    int type = 0;
/******************************/
// HBF 진입 판단 SW threshold
    switch (m_ecc_info->matrix_sel) {
    //case LAYOUT_PRIME_520B_TLC_VSS_ON: { syn_th_BF = SW_TH_BF_520B_TLC_ON; break; }
    //case LAYOUT_PRIME_520B_TLC_VSS_OFF: { syn_th_BF = SW_TH_BF_520B_TLC_OFF; break; }
    //case LAYOUT_PRIME_512B_TLC_VSS_ON: { syn_th_BF = SW_TH_BF_512B_TLC_ON; break; }
    //case LAYOUT_PRIME_512B_TLC_VSS_OFF: { syn_th_BF = SW_TH_BF_512B_TLC_OFF; break; }
    //case LAYOUT_PRIME_512B_QLC_VSS_ON: { syn_th_BF = SW_TH_BF_512B_QLC_ON; break; }
    //case LAYOUT_PRIME_512B_QLC_VSS_OFF: { syn_th_BF = SW_TH_BF_512B_QLC_OFF; break; }
    case LAYOUT_PRIME_512B_TLC_VSS_OFF: {
        syn_th_BF0 = SW_TH_BF0_512B_TLC_OFF;
        syn_th_BF1 = SW_TH_BF1_512B_TLC_OFF;
        //syn_th_BF2 = SW_TH_BF2_512B_TLC_OFF;
        break;
    }
    default: { syn_th_BF = SW_TH_BF_DEFAULT; break; }
    }
    /**************************************/
    // 5_8 Set mode 진입 판단 SW threshold
    switch (m_ecc_info->matrix_sel) {
    //case LAYOUT_PRIME_520B_TLC_VSS_ON: { syn_th_5_8_Set_0 = SW_TH_5_8_SET0_520B_TLC_ON; break; }
    //case LAYOUT_PRIME_520B_TLC_VSS_OFF: { syn_th_5_8_Set_0 = SW_TH_5_8_SET0_520B_TLC_OFF; break; }
    //case LAYOUT_PRIME_512B_TLC_VSS_ON: { syn_th_5_8_Set_0 = SW_TH_5_8_SET0_512B_TLC_ON; break; }
    case LAYOUT_PRIME_512B_TLC_VSS_OFF: { syn_th_5_8_Set_0 = SW_TH_5_8_SET0_512B_TLC_OFF; break; }
                    //case LAYOUT_PRIME_512B_QLC_VSS_ON: { syn_th_5_8_Set_0 = SW_TH_5_8_SET0_512B_QLC_ON; break; }
                    //case LAYOUT_PRIME_512B_QLC_VSS_OFF: { syn_th_5_8_Set_0 = SW_TH_5_8_SET0_512B_QLC_OFF; break; }
    default: { syn_th_5_8_Set_0 = SW_TH_5_8_SET0_DEFAULT; break; }
    }
    switch (m_ecc_info->matrix_sel) {
    //case LAYOUT_PRIME_520B_TLC_VSS_ON: { syn_th_5_8_Set_1 = SW_TH_5_8_SET1_520B_TLC_ON; break; }
    //case LAYOUT_PRIME_520B_TLC_VSS_OFF: { syn_th_5_8_Set_1 = SW_TH_5_8_SET1_520B_TLC_OFF; break; }
    //case LAYOUT_PRIME_512B_TLC_VSS_ON: { syn_th_5_8_Set_1 = SW_TH_5_8_SET1_512B_TLC_ON; break; }
    case LAYOUT_PRIME_512B_TLC_VSS_OFF: { syn_th_5_8_Set_1 = SW_TH_5_8_SET1_512B_TLC_OFF; break; }
                    //case LAYOUT_PRIME_512B_QLC_VSS_ON: { syn_th_5_8_Set_1 = SW_TH_5_8_SET1_512B_QLC_ON; break; }
                    //case LAYOUT_PRIME_512B_QLC_VSS_OFF: { syn_th_5_8_Set_1 = SW_TH_5_8_SET1_512B_QLC_OFF; break; }
    default: { syn_th_5_8_Set_1 = SW_TH_5_8_SET1_DEFAULT; break; }
    }
#if defined(__HD_FLOOR_SET__)
    switch (m_ecc_info->matrix_sel) {
    //case LAYOUT_PRIME_520B_TLC_VSS_ON: { Floor_Detect_CSW_TH1 = HD_FLOOR_CSW_TH1_520B_TLC_ON; Floor_Detect_CSW_TH2 = HD_FLOOR_CSW_TH2_520B_TLC_ON; break; }
    //case LAYOUT_PRIME_520B_TLC_VSS_OFF: { Floor_Detect_CSW_TH1 = HD_FLOOR_CSW_TH1_520B_TLC_OFF; Floor_Detect_CSW_TH2 = HD_FLOOR_CSW_TH2_520B_TLC_OFF; break; }
    case LAYOUT_PRIME_512B_TLC_VSS_ON: { Floor_Detect_CSW_TH1 = HD_FLOOR_CSW_TH1_512B_TLC_ON; Floor_Detect_CSW_TH2 = HD_FLOOR_CSW_TH2_512B_TLC_ON; break; }
    case LAYOUT_PRIME_512B_TLC_VSS_OFF: { Floor_Detect_CSW_TH1 = HD_FLOOR_CSW_TH1_512B_TLC_OFF; Floor_Detect_CSW_TH2 = HD_FLOOR_CSW_TH2_512B_TLC_OFF; break; }
    case LAYOUT_PRIME_512B_QLC_VSS_ON: { Floor_Detect_CSW_TH1 = HD_FLOOR_CSW_TH1_512B_QLC_ON; Floor_Detect_CSW_TH2 = HD_FLOOR_CSW_TH2_512B_QLC_ON; break; }
    case LAYOUT_PRIME_512B_QLC_VSS_OFF: { Floor_Detect_CSW_TH1 = HD_FLOOR_CSW_TH1_512B_QLC_OFF; Floor_Detect_CSW_TH2 = HD_FLOOR_CSW_TH2_512B_QLC_OFF; break; }
    }
#endif
    /************************************/
#if defined(__AUTO_LLR_OPT__)
    m_param_dec->power_index = MODE_POWER_STOPPING_OFF;
#else
    //m_param_dec->power_index = MODE_POWER_STOPPING_ON;
    m_param_dec->power_index = MODE_POWER_STOPPING_OFF; //(Q)
#endif
    if (MODE_POWER_STOPPING_ON == m_param_dec->power_index) {
        m_param_dec->stopping_criteria = MODE_STOPPING_CRITERIA_CYCLE;
        if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
            m_param_dec->diverse_th = HD_POWER_STOPPING_TH;
    }
    else {
        m_param_dec->diverse_th = SD_POWER_STOPPING_TH;
    }
    }
    else {
        m_param_dec->stopping_criteria = MODE_STOPPING_CRITERIA_ITER;
        m_param_dec->diverse_th = m_PCM->N + 1;
    }
#ifdef __WIN_OS__
#ifndef __VSS_ECC_TOP__
#ifndef __AUTO_LLR_OPT__
    if (m_myrank == ID_ROOT) {
        printf("* Power stopping (1: on, 2: off): %d\n", m_param_dec->power_index);
        printf("* Power stopping criteria (1: iter, 2: cycle): %d\n", m_param_dec->stopping_criteria);
        printf("* Power stopping threshold : %d\n", m_param_dec->diverse_th);
    }
#endif
#endif
#endif
    /**************************************/
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) {
        idxTermination[0] = PCRC_TERMINATION_POINT_PRIME_512B_1;
        idxTermination[1] = PCRC_TERMINATION_POINT_PRIME_512B_2;
        idxTermination[2] = PCRC_TERMINATION_POINT_PRIME_512B_3;
        idxTermination[3] = PCRC_TERMINATION_POINT_PRIME_512B_4;
    }
    //skip_idx = idxTermination[0] + 1;
    skip_idx = 2;
    //skip_idx = 46;
    skip_idx = 24;
#ifdef __WIN_OS__
#ifndef __VSS_ECC_TOP__
#ifndef __AUTO_LLR_OPT__
    if (MODE_CRC_PARTIAL == m_param_dec->CRC_Option_F_P || MODE_PCRC_GENIE == m_param_dec->CRC_Option_F_P) {
        if (m_myrank == ID_ROOT) {
            printf("* PCRC termination point : %d, %d, %d, %d\n", idxTermination[0], idxTermination[1], idxTermination[2], idxTermination[3]);
        }
    }
    else if (MODE_CRC_PARTIAL_LAST_ONLY == m_param_dec->CRC_Option_F_P) {
        if (m_myrank == ID_ROOT) {
            //printf("* PCRC termination point : %d\n", idxTermination[3]);
            printf("* PCRC termination point : %d\n", idxTermination[0]);
        }
    }
#endif
#endif
#endif
    /**************************************/
    MN_max = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF;
    crc_dec_LFSR_iter = new int[MN_max * CRC_LEN];
    for (i = 0; i < MN_max * CRC_LEN; i++) {
        crc_dec_LFSR_iter[i] = 0;
    }
#ifdef __WIN_OS__
#ifndef __AUTO_LLR_OPT__
    if (MODE_DEC_HD == m_param_dec->init_n) {
        if (m_myrank == ID_ROOT) {
#if defined (__RUN_PARITY_SKIP__)
            printf("* Parity skip @ iter 1 : on\n");
#else
            printf("* Parity skip @ iter 1 : off\n");
#endif
#if defined (__RUN_ITER34_HIGH_DV_SKIP__)
            printf("* Dv9,8 skip @ iter 4 : on\n");
#else
            printf("* Dv9,8 skip @ iter 4 : off\n");
#endif
            //printf("* ITER_5_8_SW_TH : %d, %d\n", syn_th_5_8_Set_0, syn_th_5_8_Set_1);
        }
    }
    if (m_myrank == ID_ROOT) {
        printf("* Max iter : %d\n", m_param_dec->MN[m_param_dec->MN_num - 1]);
#if defined(__DUAL_UPDATE__)
        printf("* Dual update : on\n");
#else
        printf("* Dual update : off\n");
#endif
#if defined(__PMU_READ__)
        printf("* PMU Read : on\n");
#else
        printf("* PMU Read : off\n");
#endif
        printf("\n");
    }
#endif
#endif
}
//=============================================
// Clear flags used in decoding process
//=============================================
void Decoder::Clear_Flag()
{
    real_mn = 0;
    flag_BF_on = FLAG_LOW;
    flag_dec_1iter = FLAG_LOW;
    //flag_HBF_HD_SMN = FLAG_LOW;
    flag_HD_1_4_Set = FLAG_LOW;
    flag_HD_5_8_Set = FLAG_LOW;
    state_hd_error_floor_set = FLAG_HD_FLOOR_TYPE_0;
    cnt_hd_error_floor = 0;
}
//=============================================
// Initialize counters and registers
// at the beginning of iteration
//=============================================
void Decoder::Clear_Iter_Start()
{
    Force_stopping = 0;
    pre_Force_stopping = FALSE;
    Error_count_reg = 0;
    cur_variable_node = CYCLE_BEFORE_START;
    prev_variable_node = CYCLE_BEFORE_START;
    prev_variable_node2 = CYCLE_BEFORE_START;
    prev_variable_node2_print = CYCLE_BEFORE_START;
    stop_by_partial_crc = PCRC_STOP_NO;
}
//=============================================
// Clear check node information stored in
// register
//=============================================
void Decoder::Clear_CN_REG(int type)
{
    int i;
    for (i = 0; i < m_PCM->M; i++) {
        Check_REG[i][type] = 0;
    }
}
//=============================================
// Clear edge message stored in SRAM
// (Mag and Sign)
//=============================================
void Decoder::Clear_Edge_SRAM()
{
    int i, j;
    for (i = 0; i < m_PCM->M; i++) {
        for (j = 0; j < m_PCM->K; j++) {
            Check_SRAM_sgn[i][j] = 0;
        }
    }
}
//=============================================
// Consider 2 clock dealy
//=============================================
void Decoder::Delay_2clk(int parity_skip)
{
    int ii;
    int i;
    if (TRUE == parity_skip) {
        prev_variable_node2 = prev_variable_node;
        prev_variable_node2_G_idx = prev_variable_node_G_idx;
        prev_variable_node = CYCLE_IDLE;
        prev_variable_node_G_idx = CYCLE_IDLE;
    }
    else {
        prev_variable_node2 = prev_variable_node;
        prev_variable_node2_G_idx = prev_variable_node_G_idx;
        prev_variable_node = cur_variable_node;
        prev_variable_node_G_idx = cur_variable_node_G_idx;
    }
#if defined (__ONLY_FOR_DEBUG__)
    cout << "Delay_2clk()  prev2 <== " << prev_variable_node2 << "\tprev <== " << prev_variable_node << endl;
#endif
    for (ii = 0; ii < m_PCM->J; ii++) {
        for (i = 0; i < m_PCM->z_sb; i++) {
            pre_exist_sgn_reg3[ii][i] = pre_exist_sgn_reg2[ii][i];
            pre_exist_sgn_reg2[ii][i] = pre_exist_sgn_reg[ii][i];
            pre_exist_sgn_reg3_BS[ii][i] = pre_exist_sgn_reg2_BS[ii][i];
            pre_exist_sgn_reg2_BS[ii][i] = pre_exist_sgn_reg_BS[ii][i];
            VNU_out3[ii][i] = VNU_out2[ii][i];
            VNU_out2[ii][i] = VNU_out[ii][i];
            VNU_out3_nq[ii][i] = VNU_out2_nq[ii][i];
            VNU_out2_nq[ii][i] = VNU_out_nq[ii][i];
        }
    }
}
//=============================================
// Initialize registers for partial CRC
//=============================================
void Decoder::Init_PCRC_REG(int jj)
{
    int i;
    if (jj == 0) {
        for (i = 0; i < CRC_LEN; i++) { lfsr_TP1[i] = 0; lfsr_TP2[i] = 0; lfsr_TP3[i] = 0;lfsr_TP4[i] = 0;}
    }
    /*
    if (jj == 0) { for (i = 0; i < CRC_LEN; i++) { lfsr_TP1[i] = 0; } }
    else if (jj == idxTermination[0] + 1) { for (i = 0; i < CRC_LEN; i++) { lfsr_TP2[i] = 0; } }
    else if (jj == idxTermination[1] + 1) { for (i = 0; i < CRC_LEN; i++) { lfsr_TP3[i] = 0; } }
    else if (jj == idxTermination[2] + 1) { for (i = 0; i < CRC_LEN; i++) { lfsr_TP4[i] = 0; } }*/
}
//=============================================
// Edge 값을 다 지우고 새로 시작한다.
//=============================================
void Decoder::Clear_Edge_Restart()
{
    if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
        if (TRUE == Is_Iter_Type_Edge_Clear(mn)) {
            Clear_REG_min_pos();
            Clear_REG_min_value(TRUE, TRUE);
            Clear_CN_REG(IDX_CHECK_SUM);
            Clear_Edge_SRAM_Sgn();
            //Clear_Syndrome 없음, HD는 Syndrome을 계속 들고감, Edge clear 할때마다 Check sum으로 복사
            Clear_PMU();
            Clear_Sum_t_OLD();
#if defined (__ECC_TV__)
            Clear_TV_buffer();
#endif
        }
    }
    else if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
        if (TRUE == Is_Iter_Type_Edge_Clear(mn)) {
            Clear_REG_min_pos();
            Clear_REG_min_value(TRUE, TRUE);
            Clear_CN_REG(IDX_CHECK_SUM);
            Clear_Edge_SRAM_Sgn();
            Clear_Syndrome();
            Clear_PMU();
            Clear_Sum_t_OLD();
#if defined (__ECC_TV__)
            Clear_TV_buffer();
#endif
        }
    }
}
//=============================================
// C2V, V2C와 store 연산 간 2 clk delay 반영을
// 위한 변수를 초기화 한다.
//=============================================
void Decoder::Clear_Delay_REG()
{
    int ii, i;
    for (ii = 0; ii < m_PCM->J; ii++) {
        for (i = 0; i < m_PCM->z_sb; i++) {
            pre_exist_sgn_reg3[ii][i] = 0;
            pre_exist_sgn_reg2[ii][i] = 0;
            pre_exist_sgn_reg3_BS[ii][i] = 0;
            pre_exist_sgn_reg2_BS[ii][i] = 0;
            VNU_out3_temp[ii][i] = 0;
            VNU_out3[ii][i] = 0;
            VNU_out2[ii][i] = 0;
        }
    }
}
//=============================================
// TV를 위한 임시 변수들을 초기화 시킨다.
//=============================================
void Decoder::Clear_TV_buffer()
{
    int i;
    int n;
    for (n = 0; n < m_PCM->N; n++) {
        for (i = 0; i < MAX_DV_GLOBAL; i++) {
            tv_old_sgn[i][n] = 0;
            tv_old_mag[i][n] = 0;
        }
        tv_llr_out[n] = 0;
    }
#if defined(__HALF_COL_UPDATE__)
    for (n = 0; n < m_PCM->N + m_PCM->punct_col_num * m_PCM->z_sb; n++) {
        for (i = 0; i < MAX_DV_GLOBAL_HALF; i++) {
            tv_old_sgn_HCU[i][n] = 0;
        }
    }
#endif
#if defined(__4_BIT_LLR__)
    //////////// mag 3bit, sign 1bit ////////////
    for (n = 0; n < (4 * m_PCM->N); n = n + (m_PCM->z_sb * 4)) {
        for (i = 0; i < MAX_DV_GLOBAL; i++) {
            for (int kk = 0; kk < m_PCM->z_sb; kk++) {
                tv_new_sgn_mag[i][n + kk] = 0;  // sign
            tv_vtc_inp[i][n + kk] = 0; // sign
        }
        for (int kk = 0; kk < (3 * m_PCM->z_sb); kk = kk + 3) {
            tv_new_sgn_mag[i][n + m_PCM->z_sb + kk] = 0;    // mag MSB
            tv_new_sgn_mag[i][n + m_PCM->z_sb + kk + 1] = 0;// mag CSB
            tv_new_sgn_mag[i][n + m_PCM->z_sb + kk + 2] = 0;// mag LSB
            tv_vtc_inp[i][n + m_PCM->z_sb + kk] = 0;        // mag MSB
            tv_vtc_inp[i][n + m_PCM->z_sb + kk + 1] = 0;    // mag CSB
            tv_vtc_inp[i][n + m_PCM->z_sb + kk + 2] = 0;    // mag LSB
        }
    }
    }
#else
    //////////// mag 2bit, sign 1bit ////////////
    for (n = 0; n < (3 * m_PCM->N); n = n + (m_PCM->z_sb * 3)) {
        for (i = 0; i < MAX_DV_GLOBAL; i++) {
            for (int kk = 0; kk < m_PCM->z_sb; kk++) {
                tv_new_sgn_mag[i][n + kk] = 0;  // sign
                tv_vtc_inp[i][n + kk] = 0; // sign
            }
            for (int kk = 0; kk < (2 * m_PCM->z_sb); kk = kk + 2) {
                tv_new_sgn_mag[i][n + m_PCM->z_sb + kk] = 0;    // mag MSB
                tv_new_sgn_mag[i][n + m_PCM->z_sb + kk + 1] = 0;    // mag LSB
                tv_vtc_inp[i][n + m_PCM->z_sb + kk] = 0; // mag MSB
                tv_vtc_inp[i][n + m_PCM->z_sb + kk + 1] = 0; // mag LSB
            }
        }
    }
#if defined(__HALF_COL_UPDATE__)
    for (n = 0; n < 3 * (m_PCM->N + m_PCM->punct_col_num * m_PCM->z_sb); n = n + (m_PCM->z_sb * 3)) {
        for (i = 0; i < MAX_DV_GLOBAL_HALF; i++) {
            for (int kk = 0; kk < m_PCM->z_sb; kk++) {
                tv_vtc_inp_HCU[i][n + kk] = 0; // sign
                tv_new_sgn_mag_HCU[i][n + kk] = 0; // sign
            }
            for (int kk = 0; kk < (2 * m_PCM->z_sb); kk = kk + 2) {
                tv_vtc_inp_HCU[i][n + m_PCM->z_sb + kk] = 0; // mag MSB
                tv_vtc_inp_HCU[i][n + m_PCM->z_sb + kk + 1] = 0; // mag LSB
                tv_new_sgn_mag_HCU[i][n + m_PCM->z_sb + kk] = 0; // mag MSB
                tv_new_sgn_mag_HCU[i][n + m_PCM->z_sb + kk + 1] = 0; // mag LSB
            }
        }
    }
    for (n = 0;n < m_PCM->N + m_PCM->punct_col_num * m_PCM->z_sb;n = n + m_PCM->z_sb) {
        for (i = 0;i < MAX_DV_GLOBAL_HALF;i++) {
            for (int kk = 0; kk < m_PCM->z_sb; kk++) {
                tv_new_sgn_mag_HCU_in[i][n + kk] = 0; // value
                tv_new_sgn_mag_HCU_in2[i][n + kk] = 0; // value
                tv_new_sgn_mag_HCU_in3[i][n + kk] = 0; // value
                tv_new_sgn_mag_HCU_in_nq[i][n + kk] = 0; // value
                tv_new_sgn_mag_HCU_in2_nq[i][n + kk] = 0; // value
                tv_new_sgn_mag_HCU_in3_nq[i][n + kk] = 0; // value
            }
        }
    }
    #endif
    #endif
        Clear_TV_Min_Val();
        Clear_TV_Min_Upt();
    }
    //================================================
    // TV buf 값
    // min value를 strong으로 초기화 시킨다. (수정 전)
    // min value를 very_strong으로 초기화 시킨다. (수정 후, 21.06.15 KHY)
    //================================================
    void Decoder::Clear_TV_Min_Val()
    {
        int n;
        int hw_row_num = GT_HW_MAX_ROW * m_PCM->z_sb;
        for (n = 0; n < hw_row_num; n++) {
            if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
    #if defined (__4_BIT_LLR__)
                tv_min_weak[n] = V_MAG7;
                tv_min_weak2[n] = V_MAG7;
    #else
                tv_min_weak[n] = V_VERY_STRONG;
                tv_min_weak2[n] = V_VERY_STRONG;
    #endif
            }
            else if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
                //tv_min_weak[n] = V_NORMAL_STRONG;
#if defined (__4_BIT_LLR__)
            tv_min_weak[n] = V_MAG7;
            tv_min_weak2[n] = V_MAG7;
#else
            tv_min_weak[n] = V_VERY_STRONG;
            tv_min_weak2[n] = V_VERY_STRONG;
#endif
        }
    }
}
//================================================
// TV buf 값
// update event가 발생하기 전까지는
// 항상 low로 만든다.
//================================================
void Decoder::Clear_TV_Min_Upt()
{
    int n;
    int hw_row_num = GT_HW_MAX_ROW * m_PCM->z_sb;
    for (n = 0; n < hw_row_num; n++) {
        tv_upt_min[n] = FLAG_LOW;
    }
}
//================================================
// Clear edge message stored in SRAM (Sign)
//================================================
void Decoder::Clear_Edge_SRAM_Sgn()
{
    int i, j;
    for (i = 0; i < m_PCM->M; i++) {
        for (j = 0; j < m_PCM->K; j++) {
            Check_SRAM_sgn[i][j] = 0;
        }
    }
}
void Decoder::Clear_Syndrome()
{
    int i;
    for (i = 0; i < m_PCM->M; i++) {
        Syndrome[i] = 0;
        // ITER=0 Puncturing Recovery시에만 사용하긴 하지만 Clear syndrome시 같이 clear 수행하도록 해놓음.
        Syndrome_intermediate[i] = 0;
    }
}
//================================================
// clear min position
//================================================
void Decoder::Clear_REG_min_pos()
{
    int i, j;
    for (i = 0; i < m_PCM->M_b; i++) {
        for (j = 0; j < m_PCM->z_sb; j++) {
            REG_min1_pos[(i * m_PCM->z_sb) + j] = Get_Default_Min_Pos(i);
        }
    }
}
//================================================
// clear min1, min2 value
//================================================
void Decoder::Clear_REG_min_value(int bMin1, int bMin2)
{
    int i;
    for (i = 0; i < m_PCM->M; i++) {
        if (TRUE == bMin1) {
            //REG_min1_value[i] = V_NORMAL_STRONG;
            if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
#if defined(__4_BIT_LLR__)
                REG_min1_value[i] = V_MAG7;
#else
                REG_min1_value[i] = V_VERY_STRONG;
#endif
            }
            else if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
#if defined(__4_BIT_LLR__)
                REG_min1_value[i] = V_MAG7;
#else
                REG_min1_value[i] = V_VERY_STRONG;
#endif
            }
        }
        if (TRUE == bMin2) {
#if defined(__4_BIT_LLR__)
            REG_min2_value[i] = V_MAG7;
#else
            REG_min2_value[i] = V_VERY_STRONG;
#endif
        }
    }
}
void Decoder::LDPC_Decoder(
    int* i_HD_input,
    int* i_SD_input,
    int* i_CC_input,
    int* i_CD_input,
    int i_DecOpt,
    int* i_genie_inv_msg,
    int i_TV_idx,
    int i_TV_sub_idx,
    int* o_iter_num,
    int* o_CRC_flag,
    int* o_n_error,
    int* o_str_n_error,
    int* o_1_counter,
    int* o_0_1_flip_counter,
    int* o_dec_d,
    int* o_BF_on,
    int* o_overall_clk,
    int* o_weak_correct_cnt)
{
    LDPC_Decoder(
        i_HD_input,
        i_SD_input,
        i_CC_input,
        i_CD_input,
        i_DecOpt,
        i_genie_inv_msg,
        i_TV_idx,
        i_TV_sub_idx,
        o_iter_num,
        o_CRC_flag,
        o_n_error,
        o_str_n_error,
        o_1_counter,
        o_0_1_flip_counter,
        o_dec_d,
        o_BF_on,
        o_overall_clk,
        o_weak_correct_cnt, NULL);
}
//================================================
// Column by Column decoder
//================================================
void Decoder::LDPC_Decoder(
    int* i_HD_input,
    int* i_SD_input,
    int* i_CC_input,
    int* i_CD_input,
    int  i_DecOpt,
    int* i_genie_inv_cw,
    int  i_TV_idx,
    int  i_TV_sub_idx,
    int* o_iter_num,
    int* o_CRC_flag,
    int* o_error_cnt,
    int* o_strong_error_cnt,
    int* o_1_counter,
    int* o_0_1_flip_counter,
    int* o_dec_output,
    int* o_BF_on,
    int* o_overall_clk,
    int* o_weak_correct_cnt,
    CornerChecker* io_corner)
{
    int n;
    int i;
    int temp = 0;
    int clk;
    int end_clk;
    int overall_clk;
    int log_print = FALSE;
    int N = m_PCM->N;
    int M = m_PCM->M;
    int N_b = m_PCM->N_b;
    int M_b = m_PCM->M_b;
    int K = m_PCM->K;
    int J = m_PCM->J;
    int z_sb = m_PCM->z_sb;
#if defined(__CORNER_CHECKER__)
    m_corner = io_corner;
#endif
    clk_copy = 0;
#if defined (__ECC_TV__)
    m_TV_idx = i_TV_idx;
    m_TV_sub_idx = i_TV_sub_idx;
    m_tv_dec_inter.Set_Param(m_ecc_info, m_param_dec, m_PCM);
    m_tv_dec_inter.Set_TV_idx(m_TV_idx, m_TV_sub_idx);
    m_tv_dec_inter.Open();
#endif
    Copy_1D_Array(m_genie_inv_cw, i_genie_inv_cw, N);
    m_sector_idx = i_TV_idx;
#if defined (__ONLY_FOR_DEBUG__)
    cout << "LDPC idx : " << m_sector_idx << endl;
#endif
    Init_Log_Data();
    Open_Log_Files();
    /* Set LLR */
    if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
        Make_LLR(i_HD_input, i_SD_input, i_CC_input, i_CD_input);
    }
    if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
        /* HD data inverting */
        for (n = 0; n < N; n++) {
            if (i_HD_input[n] == 1) Variable_mem[n] = 0;
            else                    Variable_mem[n] = 1;
        }
    }
    else if (MODE_ALL_ZERO_CODEWORD == m_ecc_info->mode_all_one_cw) {
        /* HD data copy */
        for (n = 0; n < N; n++) {
            if (i_HD_input[n] == 1) Variable_mem[n] = 1;
            else                    Variable_mem[n] = 0;
        }
    }
    //int cnt_err = 0;
    /* Fix HD input for punctured and shortened bits */
    for (n = 0; n < N; n++) {
        if ((n >= m_ecc_info->bit_pos.info_sh_start) && (n < m_ecc_info->bit_pos.info_sh_end)) {
            /* shortening */
            Variable_mem[n] = 0;
        }
        else if ((n >= m_ecc_info->bit_pos.info_punc_start1) && (n < m_ecc_info->bit_pos.info_punc_end1)) {
            /* puncturing (info part) */
            Variable_mem[n] = 0;
        }
        else if ((n >= m_ecc_info->bit_pos.info_punc_start2) && (n < m_ecc_info->bit_pos.info_punc_end2)) {
            /* puncturing (info part) */
            Variable_mem[n] = 0;
        }
        else if ((n >= m_ecc_info->bit_pos.parity_punc_start) && (n < m_ecc_info->bit_pos.parity_punc_end)) {
            /* puncturing (parity part) */
            Variable_mem[n] = 0;
        }
    }
    /* Initialize flags and buffer */
    Clear_Flag();
    Clear_Delay_REG();
    Clear_PMU();
    Clear_Syndrome();
#if defined(__HALF_COL_UPDATE__)
    Clear_Sum_t_OLD();
#endif
    overall_clk = 0;
    for (int k = 0; k < m_PCM->punct_col_num; k++) {
        Init_Buf(m_PCM->punct_vote[k], m_PCM->z_sb);
        Init_Buf(m_PCM->punct_vote_disjoint[k], m_PCM->z_sb);
    }
    //Init_Buf(PR_bit_flip_cnt, m_PCM->z_sb * m_PCM->punct_col_num);
#if defined (__ECC_TV__)
    Clear_TV_buffer();
    for (int i = 0; i < m_PCM->N - m_PCM->M - m_ecc_info->punctured_bit_info - m_ecc_info->shortened_bit_info; i++) {
        Punc_one_cnt[i] = Variable_mem[i];
    }
    for (int i = m_PCM->N - m_PCM->M; i < m_PCM->N; i++) {
        Punc_one_cnt[i] = Variable_mem[i];
    }
    // Col Blk 0, 1 puncturing case
    //for (int i = m_PCM->z_sb*2; i < m_PCM->N; i++) {
    //  Punc_one_cnt[i] = Variable_mem[i];
    //}
#endif
    /* Max iteration */
    MN = m_param_dec->MN[m_param_dec->MN_num - 1];
    /* Main Loop */
    for (mn = 0; mn < MN + 1; mn++) {
#if defined (__LOG_VNU_IN_OUT__)
        for (int j = 0; j < m_PCM->N; j++) {
            for (int i = 0; i < m_PCM->J; i++) {
                m_log_VNU_in[i][j] = 0;
                m_log_VNU_out[i][j] = 0;
            }
            m_log_ch_llr[j] = 0;
            m_log_sum_t[j] = 0;
        }
#endif
        Clear_Iter_Start();
        /* Edge clear */
        Clear_Edge_Restart();
        /* Column update start */
        Clk_Init();
        if (mn > 0) {
#if defined(__AUTO_LLR_OPT__)
            cur_set_idx = Get_Cur_LLR_Idx_FILE(mn);
#else
            cur_set_idx = Get_VNU_Table_Idx(mn);
#endif
        }
        else {
            cur_set_idx = 0;
        }
#if defined (__RUN_PREPROCESSING__)
        if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
            if ((TRUE == flag_BF_on && mn == 1) ||
                (FALSE == flag_BF_on && mn == ITER_MAX_HBF + 1)) { //BF mode 진입하면 Iter 1전에 Preprocessing, 진입하지 않으면 Iter 5전
                Preprocessing();
#if defined (__ECC_TV__)
                m_tv_dec_inter.Print_TV_check_sum(Check_REG, Syndrome, TRUE, mn, CYCLE_END);
#endif
            }
        }
#endif
        /*
        #if defined(__RUN_PUNCT_RECOVERY__)
            //if (MODE_DEC_HD == m_param_dec->init_n) {
            {
                int cnt;
                if (mn == 0) {
                    for (int k = 0; k < m_PCM->punct_col_num; k++) {
                        for (int j = 0; j < m_PCM->z_sb; j++) {
                            m_PCM->punct_vote[k][j] = 0;
                            //m_PCM->punct_vote_b[k][j][0] = 0;
                            //m_PCM->punct_vote_b[k][j][1] = 0;
                        }
                    }
        #ifdef __GENIE_PUNCT_RECOVERY__
                    // Puncturing Bit Error Count
                    cnt = 0;
                    for (n = m_ecc_info->bit_pos.info_punc_start; n < m_ecc_info->bit_pos.info_punc_end; n++) {
                        if (Variable_mem[n] != m_genie_inv_cw[n])
                            cnt++;
                        // Genie
                        Variable_mem[n] = m_genie_inv_cw[n];
                        //if (rand() % 100 < 10)
                        //  Variable_mem[n] = 1 - Variable_mem[n];
                    }
        #else
            #if defined(__HACRC_IKD_5B__)
                    for (int i = 0; i < m_PCM->M_b; i++) {
                        if (m_PCM->PCM_b[i][1] != -1 && m_PCM->PCM_b[i][2] == -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            int synd_val = 0;
                            for (int sub_idx = 1; sub_idx < m_PCM->RowW[i]; sub_idx++) {
                                synd_val += Variable_mem[m_PCM->C_net[idx_cn][sub_idx]];
                            }
                            if (synd_val % 2 == 0)
                                m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                            else
                                m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                        }
                    }
                    else if (m_PCM->PCM_b[i][1] == -1 && m_PCM->PCM_b[i][2] != -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            int synd_val = 0;
                            for (int sub_idx = 1; sub_idx < m_PCM->RowW[i]; sub_idx++) {
                                synd_val += Variable_mem[m_PCM->C_net[idx_cn][sub_idx]];
                            }
                            if (synd_val % 2 == 0)
                                m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                            else
                                m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                        }
                    }
                }
                    for (int i = 0; i < m_PCM->M_b; i++) {
                        if (m_PCM->PCM_b[i][0] == -1 && m_PCM->PCM_b[i][1] != -1 && m_PCM->PCM_b[i][2] != -1) {
                            for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            int synd_val = 0;
                            for (int sub_idx = 2; sub_idx < m_PCM->RowW[i]; sub_idx++) {
                                synd_val += Variable_mem[m_PCM->C_net[idx_cn][sub_idx]];
                            }
                            if (synd_val % 2 == 0) {
                                if (m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] > 0) {
                                    m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]++;
                                }
                                else {
                                    m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]--;
                                }
                                if (m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb] > 0) {
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                                }
                                else {
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                                }
                            }
                            else {
                                if (m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] > 0) {
                                    m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]--;
                                }
                                else {
                                    m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]++;
                                }
                                if (m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb] > 0) {
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                                }
                                else {
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                                }
                            }
                        }
                    }
                    else if (m_PCM->PCM_b[i][0] != -1 && m_PCM->PCM_b[i][1] != -1 && m_PCM->PCM_b[i][2] != -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            if (m_PCM->C_net[idx_cn][0] >= m_ecc_info->bit_pos.info_sh_start &&
                                m_PCM->C_net[idx_cn][0] < m_ecc_info->bit_pos.info_sh_end) {
                                int synd_val = 0;
                                for (int sub_idx = 3; sub_idx < m_PCM->RowW[i]; sub_idx++) {
                                    synd_val += Variable_mem[m_PCM->C_net[idx_cn][sub_idx]];
                                }
                                if (synd_val % 2 == 0) {
                                    if (m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb] > 0) {
                                        m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][2] % m_PCM->z_sb]++;
                                    }
                                    else {
                                        m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][2] % m_PCM->z_sb]--;
                                    }
                                    if (m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][2] % m_PCM->z_sb] > 0) {
                                        m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]++;
                                    }
                                    else {
                                        m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]--;
                                    }
                                }
                                else {
                                    if (m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb] > 0) {
                                        m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][2] % m_PCM->z_sb]--;
                                    }
                                    else {
                                        m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][2] % m_PCM->z_sb]++;
                                    }
                                    if (m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][2] % m_PCM->z_sb] > 0) {
                                        m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]--;
                                    }
                                    else {
                                        m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]++;
                                    }
                                }
                            }
                        }
                    }
                }
            }
                    for (int z = 0; z < m_PCM->z_sb; z++) {
                        if (m_PCM->punct_vote[0][z] > 0) {
                            Variable_mem[m_PCM->z_sb + z] = 0;
                        }
                        else {
                            Variable_mem[m_PCM->z_sb + z] = 1;
                        }
                        if (m_PCM->punct_vote[1][z] > 0) {
                            Variable_mem[m_PCM->z_sb * 2 + z] = 0;
                        }
                        else {
                            Variable_mem[m_PCM->z_sb * 2 + z] = 1;
                        }
                    }
        #else
                    for (int i = 0; i < m_PCM->M_b; i++) {
                        if (m_PCM->PCM_b[i][0] != -1 && m_PCM->PCM_b[i][1] == -1) {
                            for (int z = 0; z < m_PCM->z_sb; z++) {
                                int idx_cn = m_PCM->z_sb * i + z;
                                int synd_val = 0;
                                for (int sub_idx = 1; sub_idx < m_PCM->RowW[i]; sub_idx++) {
                                    synd_val += Variable_mem[m_PCM->C_net[idx_cn][sub_idx]];
                                }
                                if (synd_val % 2 == 0)
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                                else
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                            }
                        }
                        else if (m_PCM->PCM_b[i][0] == -1 && m_PCM->PCM_b[i][1] != -1) {
                            for (int z = 0; z < m_PCM->z_sb; z++) {
                                int idx_cn = m_PCM->z_sb * i + z;
                                int synd_val = 0;
                                for (int sub_idx = 1; sub_idx < m_PCM->RowW[i]; sub_idx++) {
                                    synd_val += Variable_mem[m_PCM->C_net[idx_cn][sub_idx]];
                                }
                                if (synd_val % 2 == 0)
                                    m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                                else
                                    m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                            }
                        }
                    for (int i = 0; i < m_PCM->M_b; i++) {
                        if (m_PCM->PCM_b[i][0] != -1 && m_PCM->PCM_b[i][1] != -1) {
                            for (int z = 0; z < m_PCM->z_sb; z++) {
                                int idx_cn = m_PCM->z_sb * i + z;
                                int synd_val = 0;
                                for (int sub_idx = 2; sub_idx < m_PCM->RowW[i]; sub_idx++) {
                                    synd_val += Variable_mem[m_PCM->C_net[idx_cn][sub_idx]];
                                }
                                if (synd_val % 2 == 0) {
                                    if (m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] > 0) {
                                        m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]++;
                                    }
                                    else {
                                        m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]--;
                                    }
                                    if (m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb] > 0) {
                                        m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                                    }
                                    else {
                                        m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                                    }
                                }
                                else {
                                    if (m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] > 0) {
                                        m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]--;
                                    }
                                    else {
                                        m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]++;
                                    }
                                    if (m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb] > 0) {
                                        m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                                    }
                                    else {
                                        m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                                    }
                                }
                            }
                        }
                    }
                    for (int z = 0; z < m_PCM->z_sb; z++) {
                        if (z >= m_ecc_info->bit_pos.info_punc_start && z < m_ecc_info->bit_pos.info_punc_end) {
                            if (m_PCM->punct_vote[0][z] > 0) {
                                Variable_mem[z] = 0;
                            }
                            else {
                                Variable_mem[z] = 1;
                            }
                        }
                        if (m_PCM->z_sb + z >= m_ecc_info->bit_pos.info_punc_start && m_PCM->z_sb + z < m_ecc_info->bit_pos.info_punc_end) {
                            if (m_PCM->punct_vote[1][z] > 0) {
                                Variable_mem[m_PCM->z_sb + z] = 0;
                            }
                            else {
                                Variable_mem[m_PCM->z_sb + z] = 1;
                            }
                        }
                    }
        #endif
        #endif // !__GENIE_PUNCT_RECOVERY__
                }
            }
        #endif
        */
        for (clk = 0; ; clk++) {
            clk_copy = clk;
#if defined (__ONLY_FOR_DEBUG__)
            cout << "--------------------------------" << endl;
            cout << "clk : " << clk << endl;
            cout << "col_M1 : " << col_M1 << "\tcol_Z : " << col_Z << "\tcol_P2 : " << col_P2 << "\tcol_P4 : " << col_P4 << endl;
#endif
            Init_Main_SRAM_RQ(FALSE);
            flag_parity_skip = FALSE;
#if defined (__ECC_TV__)
            Clear_TV_Min_Upt();
#endif
            /* DU manager */
#if defined(__DUAL_UPDATE__)
            DU_Manager();
#endif
            /* PMU (part 1) */
#if defined(__PMU_READ__)
            if (TRUE == DU_flag_Z) {
                if (Clk_Valid_Col(PHASE_Z)) {
                    PMU_Read(col_Z);
                    PMU_Read(col_Z + 1);
                }
            }
            else {
                if (Clk_Valid_Col(PHASE_Z)) {
#if defined(__HALF_COL_UPDATE__)
#if defined(__HACRC_IKD_5B__)
#else
                    if (col_Z >= m_PCM->N_b- m_PCM->M_b- m_PCM->punct_col_num && col_Z < m_PCM->N_b - m_PCM->M_b) {
                        PMU_Read_HCU(col_Z, col_Z_G);
                    }
                    else {
                        PMU_Read(col_Z);
                    }
#endif
#else
                    PMU_READ(col_Z);
#endif
                }
            }
#endif
            /* Power stopping algorithm (Part 2) */
            if (TRUE == pre_Force_stopping) Force_stopping++;
            cur_variable_node = col_P2;
            cur_variable_node_G_idx = col_P2_G;
            /* main body */
            if (Clk_Valid_Col(PHASE_P2)) {
                stop_by_partial_crc = PCRC_STOP_NO;
                /* Parity skip (part 1) ==> only store module */
#if defined (__RUN_PARITY_SKIP__)
                if (MODE_DEC_HD == m_param_dec->init_n) {
                    if ((mn == 1) || (mn == ITER_MAX_HBF + 1)) {
                        if ((col_P2 >= N_b - M_b + 1) && (col_P2 < N_b - 1)) {
                            /* skip C2V and V2C operations */
                            flag_parity_skip = TRUE;
#if defined (__ONLY_FOR_DEBUG__)
                            cout << "*** flag_parity_skip : " << col_P2 << endl;
#endif
                            if ((col_P2 == N_b - M_b + 1) && ((N_b - M_b) % 2 == (N_b - 1) % 2)) { // (even, even) or (odd, odd)
                                if (True == DU_flag_P4){
                                    V2C_Store(prev_variable_node2, FALSE);
                                    V2C_Store(prev_variable_node2 + 1, FALSE);
                                }
                                else {
                                    V2C_Store(prev_variable_node2, FALSE);
                                }
                                Delay_2clk(TRUE);
#if defined (__ECC_TV__)
                                if (TRUE == m_TV_cycle_based_on) {
                                    Print_TV_Cycle_Based(prev_variable_node2_print, clk);
                                }
#endif
                            }
                        }
                    }
                }
#endif
                if (FALSE == flag_parity_skip) {
                    /* Init PCRC */
                    if ((MODE_CRC_PARTIAL == m_param_dec->CRC_Option_F_P) || (MODE_CRC_PARTIAL_LAST_ONLY == m_param_dec->CRC_Option_F_P)) {
                        Init_PCRC_REG(col_P2);
                    }
                    /*  Update input of VNU (C2V) */
                    if (TRUE == DU_flag_P2) {
                        C2V_cal(col_P2);
                        C2V_cal(col_P2 + 1);
                    }
                    else {
#if defined(__HALF_COL_UPDATE__)
#if defined(__HACRC_IKD_5B__)
#else
                        if (col_P2 >= HCU_start && col_P2< HCU_end + 1) {
                            C2V_cal_HCU(col_P2, col_P2_G);
                        }
                        else {
                            C2V_cal(col_P2);
                        }
#endif
#else
                        C2V_cal(col_P2);
#endif
                    }
                    /* Update output of VNU and make hard decision */
                    if (TRUE == DU_flag_P2) {
                        V2C_Cal(col_P2);
                        /* Partial CRC algorithm */
                        if (MODE_CRC_PARTIAL == m_param_dec->CRC_Option_F_P) {
                            Cal_PCRC(col_P2);
                        }
                        else if (MODE_CRC_PARTIAL_LAST_ONLY == m_param_dec->CRC_Option_F_P) {
                            Cal_PCRC_Last_Only(col_P2);
                        }
                        else if (MODE_PCRC_GENIE == m_param_dec->CRC_Option_F_P) {
                            Check_Genie_PCRC(col_P2);
                        }
                        V2C_Cal(col_P2 + 1);
                        /* Partial CRC algorithm */
                        if (MODE_CRC_PARTIAL == m_param_dec->CRC_Option_F_P) {
                            Cal_PCRC(col_P2 + 1);
                        }
                        else if (MODE_CRC_PARTIAL_LAST_ONLY == m_param_dec->CRC_Option_F_P) {
                            Cal_PCRC_Last_Only(col_P2 + 1);
                        }
                        else if (MODE_PCRC_GENIE == m_param_dec->CRC_Option_F_P) {
                            Check_Genie_PCRC(col_P2 + 1);
                        }
                        //printf("DU_FLAG=%d, col=%d, %d\n", DU_flag_P2, col_P2, col_P2 + 1);
                    }
                    else {
#if defined(__HALF_COL_UPDATE__)
#if defined(__HACRC_IKD_5B__)
#else
                        if (col_P2 >= HCU_start && col_P2 < HCU_end + 1) {
                            V2C_Cal_HCU(col_P2, col_P2_G);
                        }
                        else {
                            V2C_Cal(col_P2);
                        }
                        /////////////////////////
                        //if (col_P2 < m_PCM->punct_col_num) { V2C_Cal_HCU(col_P2, col_P2_G); }
                        //else { V2C_Cal(col_P2); }
#endif
#else
                        V2C_Cal(col_P2);
#endif
                        /* Partial CRC algorithm */
                        if (MODE_CRC_PARTIAL == m_param_dec->CRC_Option_F_P) {
#if defined(__HALF_COL_UPDATE__)
#if defined(__HACRC_IKD_5B__)
#else
                            if (col_P2 >= HCU_start && col_P2 < HCU_end + 1) {
                                if (col_P2_G == 1) {
                                    Cal_PCRC(col_P2);
                                }
                            }
                            else {
                                Cal_PCRC(col_P2);
                            }
                            /////////////////////////
                            //if (col_P2 < m_PCM->punct_col_num) {
                            //  if (col_P2_G == 1) Cal_PCRC(col_P2);
                            //}
                            //else { Cal_PCRC(col_P2); }
                            /////////////////////////
#endif
#else
                            Cal_PCRC(col_P2);
#endif
                        }
                        else if (MODE_CRC_PARTIAL_LAST_ONLY == m_param_dec->CRC_Option_F_P) {
#if defined(__HALF_COL_UPDATE__)
#if defined(__HACRC_IKD_5B__)
#else
                            if (col_P2 >= HCU_start && col_P2 < HCU_end + 1) {
                                if (col_P2_G == 1) {
                                    Cal_PCRC_Last_Only(col_P2);
                                }
                            }
                            else {
                                Cal_PCRC_Last_Only(col_P2);
                            }
                            /////////////////////////
                            //if (col_P2 < m_PCM->punct_col_num) {
                            //  if (col_P2_G == 1) { Cal_PCRC_Last_Only(col_P2);
                            //  }
                            //}
                            //else { Cal_PCRC_Last_Only(col_P2);
                            //}
                            /////////////////////////
#endif
#else
                            Cal_PCRC_Last_Only(col_P2);
#endif
                        }
                        else if (MODE_PCRC_GENIE == m_param_dec->CRC_Option_F_P) {
#if defined(__HALF_COL_UPDATE__)
#if defined(__HACRC_IKD_5B__)
#else
                            if (col_P2 >= HCU_start && col_P2 < HCU_end + 1) {
                                if (col_P2_G == 1) {
                                    Check_Genie_PCRC(col_P2);
                                }
                            }
                            else {
                                Check_Genie_PCRC(col_P2);
                            }
                            /////////////////////////
                            //if (col_P2 < m_PCM->punct_col_num) {
                            //  if (col_P2_G == 1) Check_Genie_PCRC(col_P2);
                            //}
                            //else { Check_Genie_PCRC(col_P2); }
                            /////////////////////////
#endif
#else
                            Check_Genie_PCRC(col_P2);
#endif
                        }
                    }
                }
            }
            if (Clk_Valid_Col(PHASE_P2) || Clk_Valid_Col(PHASE_P4) || (CYCLE_END == col_P2)) {
                if (FALSE == flag_parity_skip) {
                    if ((col_P4 != CYCLE_IDLE) && (col_P4 != CYCLE_BEFORE_START)) {
#if defined (__RUN_PARITY_SKIP__)
                    if (MODE_DEC_HD == m_param_dec->init_n){
                        if (((mn == 1) || (mn == ITER_MAX_HBF + 1)) &&
                            (col_P4 == N_b - 2) && ((N_b - M_b) % 2 == (N_b - 1) % 2)) { // (even, even) or (odd, odd)
                            Intentional_Blank();
                        }
                        else {
                            if (TRUE == DU_flag_P4) {
                                V2C_Store(prev_variable_node2, FALSE);
                                V2C_Store(prev_variable_node2 + 1, FALSE);
                            }
                            else {
#if defined(__HALF_COL_UPDATE__)
#if defined(__HACRC_IKD_5B__)
#else
                            if (prev_variable_node2 >= HCU_start && prev_variable_node2 < HCU_end + 1) {
                                V2C_Store_HCU(prev_variable_node2, prev_variable_node2_G_idx, FALSE);
                            }
                            else {
                                V2C_Store(prev_variable_node2, FALSE);
                            }
#endif
#else
                            V2C_Store(prev_variable_node2, FALSE);
#endif
                        }
                    }
                }
                else{
                    if(TRUE == DU_flag_P4){
                        V2C_Store(prev_variable_node2, FALSE);
                        V2C_Store(prev_variable_node2 + 1, FALSE);
                    }
                    else {
#if defined(__HALF_COL_UPDATE__)
#if defined(__HACRC_IKD_5B__)
#else
                        if (prev_variable_node2 >= HCU_start && prev_variable_node2 < HCU_end + 1) {
                            V2C_Store_HCU(prev_variable_node2, prev_variable_node2_G_idx, FALSE);
                        }
                        else {
                            V2C_Store(prev_variable_node2, FALSE);
                        }
#endif
#else
                        V2C_Store(prev_variable_node2, FALSE);
#endif
                    }
                }
#else
                    if (TRUE == DU_flag_P4) {
                        V2C_Store(prev_variable_node2, FALSE);
                        V2C_Store(prev_variable_node2 + 1, FALSE);
                    }
                    else {
#if defined(__HALF_COL_UPDATE__)
#if defined(__HACRC_IKD_5B__)

#else
                        if (prev_variable_node2 >= HCU_start && prev_variable_node2 < HCU_end + 1) {
                            V2C_Store_HCU(prev_variable_node2, prev_variable_node2_G_idx, FALSE);
                        }
                        else {
                            V2C_Store(prev_variable_node2, FALSE);
                        }
                        /////////////////////////
                        //if (prev_variable_node2 < m_PCM->punct_col_num) {
                        //  V2C_Store_HCU(prev_variable_node2, prev_variable_node2_G_idx, FALSE);
                        //}
                        //else { V2C_Store(prev_variable_node2, FALSE); }
                        /////////////////////////
#endif
#else
                        V2C_Store(prev_variable_node2, FALSE);
#endif
                    }
#endif
                }
                Delay_2clk(FALSE);
            }
        }
#if defined (__ECC_TV__)
            if (clk >= PHASE_GAP) {
                if (FALSE == flag_parity_skip) {
                    if (TRUE == m_TV_cycle_based_on) {
                        Print_TV_Cycle_Based(prev_variable_node2_print, clk);
                    }
                }
            }
#endif
#if defined (__TV_LOG_FIFO_POWER_STOPPING__)
            Print_Log_FIFO(FALSE, FALSE);
            Print_Log_Power_Stopping(FALSE);
#endif
            if (Clk_Valid_Col(PHASE_P2) || Clk_Valid_Col(PHASE_P4)) {
                if (FALSE == flag_parity_skip) {
                    if (TRUE == DU_flag_P2) {
                        /* Count the number of flipped bits */
                        Count_Flip_Bits(col_P2);
                        Count_Flip_Bits(col_P2 + 1);
                        /* Power stopping algorithm (Part 1) */
                        Check_Power_Stopping_Cond(col_P2 + 1);
                    }
                    else {
                        /* Count the number of flipped bits */
                        Count_Flip_Bits(col_P2);
                        /* Power stopping algorithm (Part 1) */
                        Check_Power_Stopping_Cond(col_P2);
                    }
                    
                    /* Partial CRC algorithm */
                    if ((PCRC_STOP_TYPE_1 == stop_by_partial_crc) || (PCRC_STOP_TYPE_2 == stop_by_partial_crc)){
#if defined (__ONLY_FOR_DEBUG__)
                    cout << "PCRC termination ==> col_P2 : " << col_P2 << " type : " << stop_by_partial_crc << endl;
#endif
#if defined(__CORNER_CHECKER__)
                    if (out_last_column <= idxTermination[0]) {
                        m_corner->Event_Flag(CornerChecker::IDX_FLAG_PCRC_POINT_0);
                    }
                    else if (out_last_column <= idxTermination[1]) {
                        m_corner->Event_Flag(CornerChecker::IDX_FLAG_PCRC_POINT_1);
                    }
                    else if (out_last_column <= idxTermination[2]) {
                        m_corner->Event_Flag(CornerChecker::IDX_FLAG_PCRC_POINT_2);
                    }
                    else {
                        m_corner->Event_Flag(CornerChecker::IDX_FLAG_PCRC_POINT_3);
                    }
#endif
                    for (i = 0; i < stop_by_partial_crc; i++) {
                        Clk_Inc(clk); //Stop signal이 뜬 이후 clk을 진행시켜야 col_P4가 증가되고 DU_manager가 정상 동작, 2021.03.26 KHY 추가
#if defined(__DUAL_UPDATE__)
                        DU_Manager(); //DU_flag_P4 upate, 2021.03.26 KHY 추가
#endif
#if defined (__ECC_TV__)
                        Clear_TV_Min_Upt();
#endif

                        if (TRUE == DU_flag_P4) {
                            V2C_Store(prev_variable_node2, TRUE);
                            V2C_Store(prev_variable_node2 + 1, TRUE);
                        }
                        else {
    #if defined(__HALF_COL_UPDATE__)
    #if defined(__HACRC_IKD_5B__)
    #else
                        if (prev_variable_node2 >= HCU_start && prev_variable_node2 < HCU_end + 1) {
                            V2C_Store_HCU(prev_variable_node2, prev_variable_node2_G_idx, TRUE);
                        }
                        else {
                            V2C_Store(prev_variable_node2, TRUE);
                        }
                        ////////////////////////
                        //if (prev_variable_node2 < m_PCM->punct_col_num) {
                        //  V2C_Store_HCU(prev_variable_node2, prev_variable_node2_G_idx, TRUE);
                        //}
                        //else { V2C_Store(prev_variable_node2, TRUE); }
                        ////////////////////////
    #endif
    #else
                            V2C_Store(prev_variable_node2, TRUE);
    #endif
                    }
                    Delay_2clk(FALSE);
#if defined (__ECC_TV__)
                    if (TRUE == m_TV_cycle_based_on) {
                        Print_TV_Cycle_Based(prev_variable_node2_print, clk);
                    }
#endif

#if defined (__TV_LOG_FIFO_POWER_STOPPING__)
                Print_Log_Power_Stopping(FALSE);
                Print_Log_FIFO(FALSE, TRUE);
#endif
            }
            Print_CRC_result(out_last_column);
        }
    }
}
        Clk_Manager(clk);
        Clk_Delay_REG();
        end_clk = Clk_Inc(clk);
        /* column update termination */
        if ((TRUE == end_clk) ||
            (PCRC_STOP_TYPE_1 == stop_by_partial_crc) || (PCRC_STOP_TYPE_2 == stop_by_partial_crc)) {
            break;
        }
    }// end for loop (clk)
    /* clk counter */
    if ((MODE_DEC_HD == m_param_dec->init_n) && (mn == 0)) {
        Intentional_Blank();
    }
    else {
        overall_clk += clk;
#if defined (__RUN_PREPROCESSING__)
        if (MODE_DEC_HD == m_param_dec->init_n) {
            if ((TRUE == flag_BF_on) &&
                (mn == 1)) {
                overall_clk += CYCLE_FOR_PREPROCESSING;
            }
            else if ((FALSE == flag_BF_on) &&
                (mn == ITER_MAX_HBF + 1)) {
                overall_clk += CYCLE_FOR_PREPROCESSING;
            }
        }
#endif
#if defined (__RUN_PARITY_SKIP__)
        if (MODE_DEC_HD == m_param_dec->init_n) {
            if ((mn == 1) || (mn == ITER_MAX_HBF + 1)) {
                overall_clk -= M_b - 2;
            }
        }
#endif
        if ((PCRC_STOP_TYPE_1 == stop_by_partial_crc) || (PCRC_STOP_TYPE_2 == stop_by_partial_crc)) {
            overall_clk += PHASE_GAP_RTL + 1; //CRC_check 까지 걸리는 delay, 정확하지 않음 (21.05.27 KHY)
        }
        else {
            overall_clk += PHASE_GAP_RTL;
        }
    }
#if defined (__ECC_TV__)
        if (mn == 0) {
            m_tv_dec_inter.Print_TV_syndrome(Syndrome);
            m_tv_dec_inter.Print_TV_syndrome_intermediate(Syndrome_intermediate);
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
            m_tv_dec_inter.Print_TV_syndrome_intermediate_internal(Syndrome_intermediate_internal);
            m_tv_dec_inter.Print_TV_punc_vote_internal(Punc_vote_Mag_Row, Punc_vote_Mag_Row_before_BS, Punc_vote_Mag, Punc_vote_decision);
#endif
        }
        if ((((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) && (mn > 0)) ||
            //(((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) && (mn > 0)) ||
            (((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) && (mn > -1))) {
        if (TV_PRINT == 0) {
            if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
                if (MODE_CRC_PARTIAL == m_param_dec->CRC_Option_F_P ||
                    MODE_CRC_PARTIAL_LAST_ONLY == m_param_dec->CRC_Option_F_P) {
#ifndef __FULL_CRC__
                    m_tv_dec_inter.Print_TV_PCRC(lfsr_TP1, lfsr_TP2, lfsr_TP3, lfsr_TP4, mn);
#endif
                }
            }
            else {
                if (MODE_CRC_PARTIAL_LAST_ONLY == m_param_dec->CRC_Option_F_P) {
                    if (mn > 0) {
#ifndef __FULL_CRC__
                        m_tv_dec_inter.Print_TV_PCRC(lfsr_TP1, lfsr_TP2, lfsr_TP3, lfsr_TP4, mn); /* 수정 2021.07.29 */
#endif
                    }
                    }
                }
            }
            m_tv_dec_inter.Print_TV_check_sum(Check_REG, Syndrome, FALSE, mn, CYCLE_END);
            m_tv_dec_inter.Print_TV_min_pos(REG_min1_pos, mn);
            if ((PCRC_STOP_TYPE_1 == stop_by_partial_crc) || (PCRC_STOP_TYPE_2 == stop_by_partial_crc)) {
                m_tv_dec_inter.Print_TV_llr_out(tv_llr_out, Variable_mem, mn, TRUE, out_last_column, skip_idx);
                m_tv_dec_inter.Print_TV_vtc_inp(tv_vtc_inp, mn, TRUE, out_last_column, skip_idx);
                m_tv_dec_inter.Print_TV_old_sgn(tv_old_sgn, mn, TRUE, out_last_column, skip_idx);
#if defined(__HALF_COL_UPDATE__)
                m_tv_dec_inter.Print_TV_vtc_inp_HCU(tv_vtc_inp_HCU, mn, TRUE, out_last_column, skip_idx);
                m_tv_dec_inter.Print_TV_old_sgn_HCU(tv_old_sgn_HCU, mn, TRUE, out_last_column, skip_idx);
#endif
            }
            else {
                m_tv_dec_inter.Print_TV_llr_out(tv_llr_out, Variable_mem, mn, FALSE, N_b - 1, skip_idx);
                m_tv_dec_inter.Print_TV_vtc_inp(tv_vtc_inp, mn, FALSE, N_b - 1, skip_idx);
                m_tv_dec_inter.Print_TV_old_sgn(tv_old_sgn, mn, FALSE, N_b - 1, skip_idx);
#if defined(__HALF_COL_UPDATE__)
                m_tv_dec_inter.Print_TV_vtc_inp_HCU(tv_vtc_inp_HCU, mn, FALSE, N_b - 1, skip_idx);
                m_tv_dec_inter.Print_TV_old_sgn_HCU(tv_old_sgn_HCU, mn, FALSE, N_b - 1, skip_idx);
#endif
            }
            if ((PCRC_STOP_TYPE_1 == stop_by_partial_crc) || (PCRC_STOP_TYPE_2 == stop_by_partial_crc)) {
                m_tv_dec_inter.Print_TV_new_sgn(tv_new_sgn_mag, mn, TRUE, out_last_column, skip_idx);
#if defined(__HALF_COL_UPDATE__)
                m_tv_dec_inter.Print_TV_new_sgn_HCU(tv_new_sgn_mag_HCU_in, tv_new_sgn_mag_HCU_in_nq, tv_new_sgn_mag_HCU, mn, TRUE, out_last_column, skip_idx);
#endif
            }
            else {
                m_tv_dec_inter.Print_TV_new_sgn(tv_new_sgn_mag, mn, FALSE, N_b - 1, skip_idx);
#if defined(__HALF_COL_UPDATE__)
                m_tv_dec_inter.Print_TV_new_sgn_HCU(tv_new_sgn_mag_HCU_in, tv_new_sgn_mag_HCU_in_nq, tv_new_sgn_mag_HCU, mn, FALSE, N_b - 1, skip_idx);
#endif
            }
        }
        if (mn > 0) { // iteration 별 decoding output은 0번째는 찍지 말라는 HW 측의 요청
            m_tv_dec_inter.Print_TV_cwc(cwc, mn, skip_idx);
        }
        if ((((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) && (mn > 0)) ||
            (((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) && (mn > -1))) {
            //(((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) && (mn > 0))) {
            m_tv_dec_inter.Print_TV_iter_endl(mn);
        }
#endif
#if defined (__TV_LOG_FIFO_POWER_STOPPING__)
        Print_Log_FIFO(TRUE, FALSE);
        Print_Log_Power_Stopping(TRUE);
#endif
#ifdef __AUTO_LLR_OPT__
        if (m_param_dec->flag_print_CSW_log) {
            m_log_CSW_auto[mn] = Compute_CSW_Auto();
        }
#endif // __AUTO_LLR_OPT__
#if defined(__LOG_DECODING_STATUS__)
        Update_Log_Data(mn);
#endif
#if defined (__LOG_VNU_IN_OUT__)
        if ((MODE_DEC_HD == m_param_dec->init_n || MODE_DEC_1_5SD == m_param_dec->init_n)) {
            if (FLAG_HIGH == flag_BF_on && mn > 0)
                log_print = TRUE;
            else if (FLAG_LOW == flag_BF_on && mn > ITER_MAX_HBF)
                log_print = TRUE;
            else
                log_print = FALSE;
        }
        else {
            if (mn > 0)
                log_print = TRUE;
            else
                log_print = FALSE;
        }
        if (TRUE == log_print) {
            Print_Log_VNU_in(LOG_SHOW_TYPE_ALL);
            Print_Log_VNU_out(LOG_SHOW_TYPE_ALL);
            Print_Log_Sum_T(LOG_SHOW_TYPE_ALL);
        }
#endif
        /* Check CRC done */
        if (mn == 0) {
            CRC_flag = FLAG_HIGH; // 0번째 crc 체크는 무조건 실패하도록 setting
        }
        else {
            if (TRUE == Check_End_Iter(&mn)) {
#if defined(__CORNER_CHECKER__)
                if (MODE_CRC_FULL == m_param_dec->CRC_Option_F_P) {
                    m_corner->Event_Flag(CornerChecker::IDX_FLAG_FULL_CRC);
                }
#endif
                break;
            }
        }
        /* Power stopping algorithm (Part 3) */
        if (MODE_POWER_STOPPING_ON == m_param_dec->power_index) {
            if (TRUE == Jump_Iter(&mn)) {
                break;
            }
        }
        real_mn++;
        /* HBF algorithm (Part 1) */
        if (mn == 0) {
            Select_BF();
        }
    }// end for loop (mn)
    /* Output */
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) {
        if ((MODE_DEC_HD == m_param_dec->init_n || MODE_DEC_1_5SD == m_param_dec->init_n)) {
            if (FLAG_LOW == flag_BF_on) {
                iter_num -= ITER_MAX_HBF;
            }
        }
    }
    /*
    20210624 전보환 수정
    for (n = 0; n < N; n++) {
        o_dec_output[n] = (cwc[n] + 1) % 2;
    }
    */
    if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
        /* HD data inverting */
        for (n = 0; n < N; n++) {
            o_dec_output[n] = (cwc[n] + 1) % 2;
        }
    }
    else if (MODE_ALL_ZERO_CODEWORD == m_ecc_info->mode_all_one_cw) {
        /* HD data copy */
        for (n = 0; n < N; n++) {
            o_dec_output[n] = cwc[n];
        }
    }
    *o_iter_num = iter_num;
    *o_CRC_flag = CRC_flag;
    *o_1_counter = Get_One_Cnt(o_dec_output);
    Get_Err_Cnt(i_HD_input, i_SD_input, o_dec_output, o_error_cnt, o_strong_error_cnt, o_0_1_flip_counter, o_weak_correct_cnt);
#if defined(__ECC_TV__)
    m_tv_dec_inter.Print_TV_str_err_cnt_BLK(Variable_mem,cwc,i_SD_input);
#endif
#if defined(__ECC_TV_CNT_DEBUG__)
    int temp_cnt = 0;
    int temp_cnt2;
    for (n = m_ecc_info->shortened_bit_info;n < (m_PCM->N - m_PCM->M) - m_ecc_info->shortened_bit_info_offset_end;n++) temp_cnt= temp_cnt + (Variable_mem[n]+1)%2;
    temp_cnt2 = temp_cnt + *o_error_cnt - 2 * (*o_0_1_flip_counter);
    if (temp_cnt2 != *o_1_counter) {
        printf("temp_cnt=%d\n", temp_cnt);
        printf("err_cnt=%d\n", *o_error_cnt);
        printf("one_cnt=%d\n", *o_1_counter);
        printf("0-1 cnt=%d\n", *o_0_1_flip_counter);
    }
#endif
    // uncor case
    if (FLAG_HIGH == CRC_flag) {
        *o_error_cnt = 0x7FF;
        *o_strong_error_cnt = 0x7FF;
        *o_0_1_flip_counter = 0x7FF;
        *o_1_counter = 0xFFFF;
        *o_weak_correct_cnt = 0xFFFF;
    }
    *o_BF_on = flag_BF_on;
    *o_overall_clk = overall_clk;
    /*
    if (MODE_DEC_HD == m_param_dec->init_n) {
        if ((MODE_CRC_PARTIAL == m_param_dec->CRC_Option_F_P) || (MODE_PCRC_GENIE == m_param_dec->CRC_Option_F_P) || (MODE_CRC_PARTIAL_LAST_ONLY == m_param_dec->CRC_Option_F_P)) {
            if (FLAG_HIGH == CRC_flag) {
                temp = 0;    // uncor
            }
            else {
                // cor
                if (out_last_column > 120)      temp = 3;
                else if (out_last_column > 90)  temp = 2;
                else if (out_last_column > 60)  temp = 1;
                else                            temp = 0;
            }
        }
        else {
            temp = 0;    // don't care
        }
        *o_strong_error_cnt = temp;
    }*/
    if ((MODE_CRC_PARTIAL == m_param_dec->CRC_Option_F_P) ||
        (MODE_PCRC_GENIE == m_param_dec->CRC_Option_F_P) ||
        (MODE_CRC_PARTIAL_LAST_ONLY == m_param_dec->CRC_Option_F_P)) {
        memcpy(&crc_dec_LFSR_iter[CRC_LEN * 0], lfsr_TP1, sizeof(int) * CRC_LEN);
        memcpy(&crc_dec_LFSR_iter[CRC_LEN * 1], lfsr_TP2, sizeof(int) * CRC_LEN);
        memcpy(&crc_dec_LFSR_iter[CRC_LEN * 2], lfsr_TP3, sizeof(int) * CRC_LEN);
        memcpy(&crc_dec_LFSR_iter[CRC_LEN * 3], lfsr_TP4, sizeof(int) * CRC_LEN);
    }
#if defined (__ECC_TV__)
    m_tv_dec_inter.Print_TV_crc_flag(CRC_flag);
    m_tv_dec_inter.Print_TV_iter_num(iter_num);
    m_tv_dec_inter.Print_TV_info_err_cnt(*o_error_cnt);
    m_tv_dec_inter.Print_TV_strong_err_cnt(*o_strong_error_cnt);
    m_tv_dec_inter.Print_TV_weak_cor_cnt(*o_weak_correct_cnt);
    m_tv_dec_inter.Print_TV_bit_cnt(*o_1_counter);
    m_tv_dec_inter.Print_TV_flip_cnt(*o_0_1_flip_counter);
    m_tv_dec_inter.Print_TV_BF_on_flag(flag_BF_on);
    m_tv_dec_inter.Print_TV_cfp_flag_endl();
    m_tv_dec_inter.Close();
#endif
#if defined (__ONLY_FOR_DEBUG__)
    cout << "CRC_flag : " << CRC_flag << endl;
#endif
    Padding_Zero_Log(mn, CRC_flag);
    Print_Log_Files();
    Close_Log_Files();
#if defined(__CORNER_CHECKER__)
    if (TRUE == flag_BF_on) {
        m_corner->Event_Flag(CornerChecker::IDX_FLAG_HBF_ON);
    }
    m_corner->Event_Result(CRC_flag, iter_num, *o_error_cnt);
#endif
}
//=================================================
// BF 진입 여부 판단
//=================================================
void Decoder::Select_BF()
{
#if defined (__AUTO_LLR_OPT__)
    flag_BF_on = FLAG_LOW;
#else
    if (MODE_DEC_HD == m_param_dec->init_n) {
        if ((MODE_BF_ON == m_param_dec->BF_mode) && (syn_weight < syn_th_BF0)) {
            flag_BF_on = FLAG_HIGH;
            flag_HD_1_4_Set = FLAG_HD_1_4_SET_TYPE_0;
            flag_HD_5_8_Set = FLAG_HD_5_8_SET_TYPE_0;
#if defined(__CORNER_CHECKER__)
            m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_0);
#endif
        }
        else {
            mn = mn + ITER_MAX_HBF;
            MN = MN + ITER_MAX_HBF;
            if (syn_weight < syn_th_5_8_Set_0) {
                flag_HD_5_8_Set = FLAG_HD_5_8_SET_TYPE_0;
#if defined(__CORNER_CHECKER__)
                m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_0);
#endif
            }
            else{
                flag_HD_5_8_Set = FLAG_HD_5_8_SET_TYPE_1;
#if defined(__CORNER_CHECKER__)
                m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_1);
#endif
            }
        }
    }
    else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
        mn = mn + ITER_MAX_HBF;
        MN = MN + ITER_MAX_HBF;
        if (psyn_weight < syn_th_5_8_Set_0) {
            flag_HD_5_8_Set = FLAG_HD_5_8_SET_TYPE_0;
#if defined(__CORNER_CHECKER__)
            m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_0);
#endif
        }
        else {
            flag_HD_5_8_Set = FLAG_HD_5_8_SET_TYPE_1;
#if defined(__CORNER_CHECKER__)
            m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_1);
#endif
        }
    }
#endif //__AUTO_LLR_OPT__
}
//==========================================
// Calculate partial CRC
// jj-th column block
//==========================================
void Decoder::Cal_PCRC(int jj)
{
    int ii;
    int crc_shortened_bits = CRC_LOGIC_SHORTENED;
    if ((mn >= 1) && (jj >= 0) && (jj < m_PCM->N_b - m_PCM->M_b)) {
        if (jj <= idxTermination[0])        partial_crc_HW_T4(dec_d, lfsr_TP1, jj, crc_shortened_bits, idxTermination);
        else if (jj <= idxTermination[1])    partial_crc_HW_T4(dec_d, lfsr_TP2, jj, crc_shortened_bits, idxTermination);
        else if (jj <= idxTermination[2])    partial_crc_HW_T4(dec_d, lfsr_TP3, jj, crc_shortened_bits, idxTermination);
        else                                 partial_crc_HW_T4(dec_d, lfsr_TP4, jj, crc_shortened_bits, idxTermination);
#if defined (__ECC_TV__)
        if (TV_PRINT == 1) {
#ifndef __FULL_CRC__
            m_tv_dec_inter.Print_TV_PCRC(lfsr_TP1, lfsr_TP2, lfsr_TP3, lfsr_TP4, mn);
#endif
        }
#endif
    }
    if ((mn >= 1) && (jj == idxTermination[0] || jj == idxTermination[1] || jj == idxTermination[2] || jj == idxTermination[3])) {
        /* Check CRC is satisfied at the predefied termination points */
        for (ii = 0; ii < CRC_LEN; ii++) {
            pcrc_checksum[ii] = (lfsr_TP1[ii] + lfsr_TP2[ii] + lfsr_TP3[ii] + lfsr_TP4[ii]) % 2;
        }
        flagPassPCRC = 0;
        for (ii = 0; ii < CRC_LEN; ii++)
            flagPassPCRC = flagPassPCRC + pcrc_checksum[ii];
#if defined (__ECC_TV__)
            if (TV_PRINT == 2) {
#ifndef __FULL_CRC__
                m_tv_dec_inter.Print_TV_PCRC(lfsr_TP1, lfsr_TP2, lfsr_TP3, lfsr_TP4, mn);
#endif
            }
#endif
        /* control flag */
#if defined(__DUAL_UPDATE__)
        if (((mn == 1) || (mn == ITER_MAX_HBF + 1))) {
            if ((jj == idxTermination[3]) &&
                (flagPassPCRC == FLAG_LOW)) {
                /* 해당 iteration에서는 마지막 termination point에서만 종료할 수 있음 */
                out_last_column = jj;
                stop_by_partial_crc = PCRC_STOP_TYPE_2;
            }
        }
        else {
            if (((jj == idxTermination[1]) || (jj == idxTermination[2])) &&
                (flagPassPCRC == FLAG_LOW)) {
                out_last_column = jj;
                stop_by_partial_crc = PCRC_STOP_TYPE_2; // HD에서 PCRC 미사용시 termination point를 실제 위치 (RTL과 동일하게)인 3으로 변경. 관거 수정 22.02.07
            }
            else if (((jj == idxTermination[0]) || (jj == idxTermination[3])) &&
            (flagPassPCRC == FLAG_LOW)){
                out_last_column = jj;
                stop_by_partial_crc = PCRC_STOP_TYPE_2;
            }
        }
#else
        if (((mn == 1) || (mn == ITER_MAX_HBF + 1))) {
            if ((jj == idxTermination[3]) &&
                (flagPassPCRC == FLAG_LOW)) {
                /* 해당 iteration에서는 마지막 termination point에서만 종료할 수 있음 */
                out_last_column = jj;
                stop_by_partial_crc = PCRC_STOP_TYPE_2;
            }
        }
        else {
            if (((jj == idxTermination[0]) || (jj == idxTermination[1]) || (jj == idxTermination[2]) || (jj == idxTermination[3])) &&
                (flagPassPCRC == FLAG_LOW)) {
                out_last_column = jj;
                stop_by_partial_crc = PCRC_STOP_TYPE_2;
            }
        }
#endif
    }
}
void Decoder::Cal_PCRC_Last_Only(int jj)
{
    int ii;
    int crc_shortened_bits = CRC_LOGIC_SHORTENED;
    if ((mn >= 1) && (jj >= 0) && (jj < m_PCM->N_b - m_PCM->M_b)) {
        if (jj <= idxTermination[0]) {
            partial_crc_HW_T4(dec_d, lfsr_TP1, jj, crc_shortened_bits, idxTermination);}
        //else if (jj <= idxTermination[1]) { partial_crc_HW_T4(dec_d, lfsr_TP2, jj, crc_shortened_bits, idxTermination); }
        //else if (jj <= idxTermination[2]) { partial_crc_HW_T4(dec_d, lfsr_TP3, jj, crc_shortened_bits, idxTermination); }
        //else { partial_crc_HW_T4(dec_d, lfsr_TP4, jj, crc_shortened_bits, idxTermination); }
            if (jj <= idxTermination[0]) {
#if defined (__ECC_TV__)
                if (TV_PRINT == 1) {
#ifndef __FULL_CRC__
                    m_tv_dec_inter.Print_TV_PCRC(dec_d, lfsr_TP1, lfsr_TP2, lfsr_TP3, lfsr_TP4, mn, jj);
#endif
                }
            // m_tv_dec_inter.Print_TV_PCRC_Cycle_based(lfsr_TP1, lfsr_TP2, lfsr_TP3, lfsr_TP4, mn, jj); //debug 용도 2021.08.02
#endif
            }
        }
    if ((mn >= 1) && (jj == idxTermination[3])) {
        /* Check CRC is satisfied at the predefied termination points */
        for (ii = 0; ii < CRC_LEN; ii++) {
            pcrc_checksum[ii] = lfsr_TP1[ii];
            //pcrc_checksum[ii] = (lfsr_TP1[ii] + lfsr_TP2[ii] + lfsr_TP3[ii] + lfsr_TP4[ii]) % 2;
        }
        flagPassPCRC = 0;
        for (ii = 0; ii < CRC_LEN; ii++)
            flagPassPCRC = flagPassPCRC + pcrc_checksum[ii];
#if defined (__ECC_TV__)
            if (TV_PRINT == 2) {
#ifndef __FULL_CRC__
                m_tv_dec_inter.Print_TV_PCRC(lfsr_TP1, lfsr_TP2, lfsr_TP3, lfsr_TP4, mn);
#endif
            }
#endif
        /* control flag */
        if (flagPassPCRC == FLAG_LOW) {
            out_last_column = jj;
            stop_by_partial_crc = PCRC_STOP_TYPE_2;
        }
    }
}
//=================================================
// Genie aided PCRC
// Compare with the original codeword
//=================================================
void Decoder::Check_Genie_PCRC(int jj)
{
    int en = 0;
    if ((mn >= 1) && (jj == idxTermination[0] || jj == idxTermination[1] || jj == idxTermination[2] || jj == idxTermination[3])) {
        flagPassPCRC = FLAG_LOW;
        for (int q = 0; q < m_PCM->N - m_PCM->M; q++) {
            if (cwc[q] != m_genie_inv_cw[q]) {
                en++;
                flagPassPCRC = FLAG_HIGH;
            }
        }
        /* control flag */
#if defined(__DUAL_UPDATE__)
        if (((jj == idxTermination[1]) || (jj == idxTermination[2])) &&
            (flagPassPCRC == FLAG_LOW)) {
            out_last_column = jj;
            stop_by_partial_crc = PCRC_STOP_TYPE_1;
        }
        else if (((jj == idxTermination[0]) || (jj == idxTermination[3])) &&
            (flagPassPCRC == FLAG_LOW)) {
            out_last_column = jj;
            stop_by_partial_crc = PCRC_STOP_TYPE_2;
        }
#else
        if (((jj == idxTermination[0]) || (jj == idxTermination[1]) || (jj == idxTermination[2]) || (jj == idxTermination[3])) &&
            (flagPassPCRC == FLAG_LOW)) {
            out_last_column = jj;
            stop_by_partial_crc = PCRC_STOP_TYPE_2;
        }
#endif
    }
}
//=================================================
// C2V sign 값 결정
// SD: Restart 다음 iteration에서 old_sgn을 읽어 오지 않음
// HD: Restart iteration에서 old_sgn을 읽어 오지 않음
// HD (Pre_processing on): Iteration 1에서 Pre-processing한 node에 대해서는 old_sgn 읽음 (예외)
// Syndrome-aided decoding에서는 자신의 HD sign은
// 항상 plus (즉, "0")라고 생각한다.
// 이에 decoding 시작 iteration에서는 old_sign은
// 항상 0임 (SRAM에서 읽지 않음)
// Restart가 적용됐을때는 syndrome값이 VNU_in의 sign이 됨
//=================================================
int Decoder::C2V_Cal_New_Sgn(int iter, int synd, int check_sum, int edge_sgn, int col_idx)
{
    int t = 0;
    if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
#if defined (__RUN_PREPROCESSING__)
        if ((TRUE == flag_BF_on) &&
            (iter == 1) &&
            (col_idx == m_PCM->N_b - m_PCM->M_b - 3 || col_idx == m_PCM->N_b - m_PCM->M_b - 2)) {
            Intentional_Blank();    // read 0, BF_mode에서 Iter 1 직전에 Pre-processing을 N_b - M_b - 1에서 수행 -> 해당 column은 read 수행
        }
        else if ((FALSE == flag_BF_on) &&
            (iter == ITER_MAX_HBF + 1) &&
            (col_idx == m_PCM->N_b - m_PCM->M_b - 3 || col_idx == m_PCM->N_b - m_PCM->M_b - 2)) {
            Intentional_Blank();    // read 0, BF_mode_on에서 Iter ITER_MAX_HBF + 1 직전에 Pre-processing을 N_b - M_b - 1에서 수행 -> 해당 column read 수행
        }
        else if (TRUE == Is_Iter_Type_Edge_Clear(iter)) {
            edge_sgn = 0; // read x
        }
        else {
            Intentional_Blank();    // read o
        }
#else
        if (TRUE == Is_Iter_Type_Edge_Clear(iter)) //Restart하는 iteration에서는 old_sgn을 읽지 않음 (HD)
        {
            edge_sgn = 0;
        }    // read x
#endif
    }
    else if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
        if (Is_Iter_Type_Edge_Clear(iter - 1)) //Restart 다음 iteration에서는 old_sgn을 읽지 않음 (SD)
        {
            edge_sgn = 0;
        }    // read x
    }
    t = (synd + check_sum + edge_sgn) % 2;
    return t;
}
//=================================================
// Calculate C2V message (VNU_in)
// jj-th column block
// ii-th connected MUX
//=================================================
void Decoder::C2V_Cal(int jj, int ii, int iter)
{
    int j;
    int row_idx, s, position_c;
    int idx_offset;
    int row_idx_r, new_sgn;
    int synd;
    int check_out;
    int check_sum;
    int edge_sgn;
    int min1_pos;
    int min1_value;
    int min2_value;
    int check_out_temp;
    int mux_index;
    int v_deg;
    row_idx = m_PCM->V_net_b[jj][ii];
    s = m_PCM->PCM_b[row_idx][jj];
    shift_mem(z_mem_shift, m_PCM->z_sb, s, 0);
    position_c = m_PCM->VtoC_ID[row_idx][jj];
    idx_offset = row_idx * m_PCM->z_sb;
    mux_index = m_PCM->Mux_idx[ii][jj];
    v_deg = m_PCM->ColW[jj];
    for (j = 0; j < m_PCM->z_sb; j++) { //VN ordering (before BS)
        row_idx_r = idx_offset + z_mem_shift[j];
        /* C2V sgn calculation */
        synd = Syndrome[row_idx_r];
        check_sum = Check_REG[row_idx_r][IDX_CHECK_SUM];
        edge_sgn = Check_SRAM_sgn[row_idx_r][position_c];    // HW 구현과 다르게 PMU로부터 읽지 않음
        /* Syndrome aided decoding algorithm */
        new_sgn = C2V_Cal_New_Sgn(iter, synd, check_sum, edge_sgn, jj);
        /* C2V mag calculation */
        if ((TRUE == flag_BF_on) &&
#ifdef __AUTO_LLR_OPT__
            (iter <= 4) &&
#else
            (iter <= ITER_MAX_HBF) &&
#endif
            (v_deg > DV_5)) { //Dv > 5 인 column은 1bit precision -> mag는 4로 고정
#if defined (__4_BIT_LLR__)
                check_out = EDGE_MAG_8;
#else
                check_out = EDGE_MAG_7;
#endif
        }
        else { //그외엔 3bit precision
            min1_value = REG_min1_value[row_idx_r];
            min2_value = REG_min2_value[row_idx_r];
            min1_pos = REG_min1_pos[row_idx_r];
            if (min1_pos == position_c) { check_out_temp = min2_value; }
            else { check_out_temp = min1_value; }
#if defined (__4_BIT_LLR__)
            if (check_out_temp == V_MAG7) { check_out = EDGE_MAG_8; }
            else if (check_out_temp == V_MAG6) { check_out = EDGE_MAG_7; }
            else if (check_out_temp == V_MAG5) { check_out = EDGE_MAG_6; }
            else if (check_out_temp == V_MAG4) { check_out = EDGE_MAG_5; }
            else if (check_out_temp == V_MAG3) { check_out = EDGE_MAG_4; }
            else if (check_out_temp == V_MAG2) { check_out = EDGE_MAG_3; }
            else if (check_out_temp == V_MAG1) { check_out = EDGE_MAG_2; }
            else { check_out = EDGE_MAG_1; }
#else
            if (check_out_temp == V_VERY_STRONG) { check_out = EDGE_MAG_7; }
            else if (check_out_temp == V_NORMAL_STRONG) { check_out = EDGE_MAG_5; }
            else if (check_out_temp == V_NORMAL_WEAK) { check_out = EDGE_MAG_3; }
            else { check_out = EDGE_MAG_1; }
#endif
        }
        /* real output */
        if (new_sgn % 2 == 1) { check_out = -check_out; }    // minus sign
        VNU_in[mux_index][j] = check_out;
        pre_exist_sgn_reg[mux_index][z_mem_shift[j]] = edge_sgn;
        pre_exist_sgn_reg_BS[mux_index][j] = edge_sgn;
#if defined (__ECC_TV__)
#if defined (__4_BIT_LLR__)
        /* 4-bit precision */
        if (new_sgn % 2 == 1)       tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + j] = V_MINUS;    // minus sign
        else                        tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + j] = V_PLUS;     // plus sign
        if (abs(check_out) == EDGE_MAG_8) {
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 1;    // mag LSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 1;    // mag LSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 1;    // mag LSB
        }
        else if (abs(check_out) == EDGE_MAG_7) {
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 1;        // mag MSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 1;    // mag CSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 0;    // mag LSB
        }
        else if (abs(check_out) == EDGE_MAG_6) {
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 1;        // mag MSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 0;    // mag CSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 1;    // mag LSB
        }
        else if (abs(check_out) == EDGE_MAG_5) {
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 1;        // mag MSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 0;    // mag CSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 0;    // mag LSB
        }
        else if (abs(check_out) == EDGE_MAG_4) {
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 0;        // mag MSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 1;    // mag CSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 1;    // mag LSB
        }
        else if (abs(check_out) == EDGE_MAG_3) {
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 0;        // mag MSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 1;    // mag CSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 0;    // mag LSB
        }
        else if (abs(check_out) == EDGE_MAG_2) {
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 0] = 0;    // mag LSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 0;    // mag LSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 1;    // mag LSB
        }
        else {
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 0;        // mag MSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 0;    // mag CSB
            tv_vtc_inp[mux_index][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 0;    // mag LSB
        }
#else
        /* 3-bit precision */
        if (new_sgn % 2 == 1)       tv_vtc_inp[mux_index][3 * (m_PCM->z_sb * jj) + j] = V_MINUS;        // minus sign
        else                        tv_vtc_inp[mux_index][3 * (m_PCM->z_sb * jj) + j] = V_PLUS;         // plus sign
        if (abs(check_out) == EDGE_MAG_7) {
            tv_vtc_inp[mux_index][3 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2)] = 1; // mag MSB
            tv_vtc_inp[mux_index][3 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2) + 1] = 1; // mag LSB
        }
        else if (abs(check_out) == EDGE_MAG_5) {
            tv_vtc_inp[mux_index][3 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2)] = 1;// mag MSB
            tv_vtc_inp[mux_index][3 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2) + 1] = 0;// mag LSB
        }
        else if (abs(check_out) == EDGE_MAG_3) {
            tv_vtc_inp[mux_index][3 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2)] = 0;// mag MSB
            tv_vtc_inp[mux_index][3 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2) + 1] = 1;// mag LSB
        }
        else {
            tv_vtc_inp[mux_index][3 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2)] = 0;// mag MSB
            tv_vtc_inp[mux_index][3 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2) + 1] = 0;// mag LSB
        }
#if defined (__HALF_COL_UPDATE__)
        int jj_temp;
        int mux_index_temp;
        int current_G_idx = (col_P2_G + mn) % 2;
#ifdef __HALF_COL_MODIFIED__
        if (jj < HCU_start) {
            jj_temp = jj; mux_index_temp = mux_index;
        }
        else if (jj == HCU_start && mux_index < 8) {
            if (iter % 2 == 0) { jj_temp = HCU_start; mux_index_temp = mux_index; }
            else { jj_temp = HCU_start + 1; mux_index_temp = mux_index; }
        }
        else if (jj == HCU_start && mux_index >= 8) {
            if (iter % 2 == 0) { jj_temp = HCU_start + 1; mux_index_temp = mux_index - 8; }
            else { jj_temp = HCU_start; mux_index_temp = mux_index - 8; }
        }
        else if (jj == HCU_end && mux_index < 8) {
            if (iter % 2 == 0) { jj_temp = HCU_end + 1; mux_index_temp = mux_index; }
            else { jj_temp = HCU_end + 2; mux_index_temp = mux_index; }
        }
        else if (jj == HCU_end && mux_index >= 8) {
            if (iter % 2 == 0) { jj_temp = HCU_end + 2; mux_index_temp = mux_index - 8; }
            else { jj_temp = HCU_end + 1; mux_index_temp = mux_index - 8; }
        }
        else {
            jj_temp = jj + m_PCM->punct_col_num; mux_index_temp = mux_index;
        }
        //printf("jj_temp=%d, mux_index=%d (<-%d)\n",jj_temp, mux_index_temp, mux_index);
        if (new_sgn % 2 == 1)       tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + j] = V_MINUS;    // minus sign
        else                        tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + j] = V_PLUS;     // plus sign
        
        if (abs(check_out) == EDGE_MAG_7) {
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2)] = 1; // mag MSB
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2) + 1] = 1; // mag LSB
        }
        else if (abs(check_out) == EDGE_MAG_5) {
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2)] = 1;// mag MSB
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2) + 1] = 0;// mag LSB
        }
        else if (abs(check_out) == EDGE_MAG_3) {
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2)] = 0;// mag MSB
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2) + 1] = 1;// mag LSB
        }
        else {
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2)] = 0;// mag MSB
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2) + 1] = 0;// mag LSB
        }
#else
        if (jj == 0 && mux_index < 8) {
            if (iter % 2 == 0) { jj_temp = 0; mux_index_temp = mux_index; }
            else { jj_temp = 1; mux_index_temp = mux_index; }
        }
        else if (jj == 0 && mux_index >= 8) {
            if (iter % 2 == 0) { jj_temp = 1; mux_index_temp = mux_index - 8; }
            else { jj_temp = 0; mux_index_temp = mux_index - 8; }
        }
        else if (jj == 1 && mux_index < 8) {
            if (iter % 2 == 0) { jj_temp = 2; mux_index_temp = mux_index; }
            else { jj_temp = 3; mux_index_temp = mux_index; }
        }
        else if (jj == 1 && mux_index >= 8) {
            if (iter % 2 == 0) { jj_temp = 3; mux_index_temp = mux_index; }
            else { jj_temp = 2; mux_index_temp = mux_index - 8; }
        }
        else { jj_temp = jj + 2; mux_index_temp = mux_index; }
        //printf("jj_temp=%d, mux_index=%d (<-%d)\n",jj_temp, mux_index_temp, mux_index);
        if (new_sgn % 2 == 1)       tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + j] = V_MINUS;    // minus sign
        else                        tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + j] = V_PLUS;     // plus sign
        if (abs(check_out) == EDGE_MAG_7) {
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2)] = 1; // mag MSB
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2) + 1] = 1; // mag LSB
        }
        else if (abs(check_out) == EDGE_MAG_5) {
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2)] = 1;// mag MSB
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2) + 1] = 0;// mag LSB
        }
        else if (abs(check_out) == EDGE_MAG_3) {
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2)] = 0;// mag MSB
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2) + 1] = 1;// mag LSB
        }
        else {
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2)] = 0;// mag MSB
            tv_vtc_inp_HCU[mux_index_temp][3 * (m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2) + 1] = 0;// mag LSB
        }
#endif // __HALF_COL_MODIFIED__
#endif
#endif
    #endif
        }// end for loop (j)
    }
    //================================================
    // Calculate C2V message (VNU_in)
    // jj-th column block
    //================================================
    void Decoder::C2V_cal(int jj)
    {
    #if defined (__ONLY_FOR_DEBUG__)
        cout << "C2V_cal() : " << jj << endl;
    #endif
        int ii;
        if (FALSE == Is_Iter_Type_Init(mn)) {
            for (ii = 0; ii < m_PCM->ColW[jj]; ii++) {
                C2V_Cal(jj, ii, mn);
            }
        }
    }
    //================================================
    // Half Column Update 특성 반영
    // Calculate C2V message (VNU_in)
    // jj-th column block
    //================================================
    void Decoder::C2V_cal_HCU(int jj, int G_idx)
    {
    #if defined (__ONLY_FOR_DEBUG__)
        cout << "C2V_cal() : " << jj << endl;
    #endif
        int separate_v_deg = 0;
        if (jj == HCU_start) {
            separate_v_deg = SEPARATE_V_DEG_1;
        }
        else if (jj == HCU_end) {
            separate_v_deg = SEPARATE_V_DEG_2;
        }
        int current_G_idx = (G_idx + mn) % 2;
        if (FALSE == Is_Iter_Type_Init(mn)) {
            if (current_G_idx == 0) {
                for (int ii = 0; ii < separate_v_deg; ii++) {
                    C2V_Cal(jj, ii, mn);
                }
            }
            else if (current_G_idx == 1) {
                for (int ii = separate_v_deg; ii < m_PCM->ColW[jj]; ii++) {
                    C2V_Cal(jj, ii, mn);
                }
            }
        }
    }
    //================================================
    // VNU 결과를 REG, SRAM에 저장한다.
    //================================================
    void Decoder::V2C_Store(int jj, int skip)
    {
    #if defined (__ONLY_FOR_DEBUG__)
        if ((jj >= 0) && (jj < m_PCM->N_b)) {
            cout << "V2C_store() : " << jj << endl;
        }
    #endif
        if ((jj >= 0) && (jj < m_PCM->N_b)) {
            for (int ii = 0; ii < m_PCM->ColW[jj]; ii++) {
                V2C_Store(jj, ii, mn, TRUE, TRUE, TRUE);
            }
            /* delay */
            //prev_variable_node2_print = prev_variable_node2;
            prev_variable_node2_print = jj;
            for (int ii = 0; ii < m_PCM->J; ii++) {
                for (int i = 0; i < m_PCM->z_sb; i++) {
                    VNU_out3_temp[ii][i] = VNU_out3[ii][i];
                }
            }
        if (FALSE == skip) {
            PMU_Write(prev_variable_node2_print);
        }
    }
    }
    //================================================
    // Half Column Update용
    // VNU 결과를 REG, SRAM에 저장한다.
    //================================================
    void Decoder::V2C_Store_HCU(int jj, int G_idx, int skip)
    {
        int current_G_idx = (G_idx + mn) % 2;
        int separate_v_deg = 0;
        if (jj == HCU_start) {
            separate_v_deg = SEPARATE_V_DEG_1;
        }
        else if (jj == HCU_end) {
            separate_v_deg = SEPARATE_V_DEG_2;
        }
    #if defined (__ONLY_FOR_DEBUG__)
        if ((jj >= 0) && (jj < m_PCM->N_b)) {
            cout << "V2C_store() : " << jj << endl;
        }
    #endif
        if ((jj >= 0) && (jj < m_PCM->N_b)) {
            if (current_G_idx == 0) {
                for (int ii = 0; ii < separate_v_deg; ii++) {
                    //for (ii = 0; ii < m_PCM->ColW[jj] / 2; ii++) {
                        V2C_Store(jj, ii, mn, TRUE, TRUE, TRUE);
                    }
                }
            else if (current_G_idx == 1) {
                //for (ii = m_PCM->ColW[jj] / 2; ii < m_PCM->ColW[jj]; ii++) {
                for (int ii = separate_v_deg; ii < m_PCM->ColW[jj]; ii++) {
                    V2C_Store(jj, ii, mn, TRUE, TRUE, TRUE);
                }
            }
    /* delay */
    //prev_variable_node2_print = prev_variable_node2;
    prev_variable_node2_print = jj;
    for (int ii = 0; ii < m_PCM->J; ii++) {
        for (int i = 0; i < m_PCM->z_sb; i++) {
            VNU_out3_temp[ii][i] = VNU_out3[ii][i];
        }
    }
    if (FALSE == skip) {
        PMU_Write_HCU(prev_variable_node2_print, G_idx);
    }
    }
}
//================================================
// VNU 결과를 REG, SRAM에 저장한다.
//================================================
void Decoder::V2C_Store(int jj, int ii, int iter, int store_checksum_REG, int store_min_REG, int store_edge_SRAM)
{
    int j;
    int row_idx, s, position_c;
    int idx_offset;
    int check_in, check_in_mag;
    int check_sum;
    int pre_v2c_sgn;
    int cur_chk_sum_weight;
    int min1_pos;
    int min1_value;
    int min2_value;
    int old_min1_value;
    int old_min2_value;
    int update_flag;
    int v2c_sgn;
    int v2c_mag;
    int check_in_before_BS;
    int check_in_before_BS_nq;
    int check_in_before_BS_mag;
    int v2c_sgn_before_BS;
    int v2c_mag_before_BS;
    int pre_v2c_sgn_before_BS;
    int bit_pos;
    int mux_idx;
    int v_deg;
    int jj_temp;
    int mux_idx_temp;
    // current int sub-block information
    row_idx = m_PCM->V_net_b[jj][ii]; // current row index at base-matrix
    s = m_PCM->PCM_b[row_idx][jj]; // shift value at current sub-matrix
    shift_mem(z_mem_shift, m_PCM->z_sb, s, 1); // % index permutation
    position_c = m_PCM->VtoC_ID[row_idx][jj]; // order in current check // jj번째 column block의 ii번째 nonzero block이 해당 check에서 몇번째로 몇번째 variable node인지를 의미하는 값.
    idx_offset = row_idx * m_PCM->z_sb;
    mux_idx = m_PCM->Mux_idx[ii][jj];
    v_deg = m_PCM->ColW[jj];
    for (j = 0; j < m_PCM->z_sb; j++) {
        bit_pos = idx_offset + j;
        /* Read VNU output (before BS) */
        check_in_before_BS = VNU_out3[mux_idx][j];
        check_in_before_BS_nq = VNU_out3_nq[mux_idx][j];
        check_in_before_BS_mag = abs(check_in_before_BS);
        /* domain 변경 */
        if (check_in_before_BS >= 0)    v2c_sgn_before_BS = V_PLUS;
        else                            v2c_sgn_before_BS = V_MINUS;
#if defined (__4_BIT_LLR__)
        if (check_in_before_BS_mag == EDGE_MAG_8)      v2c_mag_before_BS = V_MAG7;
        else if (check_in_before_BS_mag == EDGE_MAG_7) v2c_mag_before_BS = V_MAG6;
        else if (check_in_before_BS_mag == EDGE_MAG_6) v2c_mag_before_BS = V_MAG5;
        else if (check_in_before_BS_mag == EDGE_MAG_5) v2c_mag_before_BS = V_MAG4;
        else if (check_in_before_BS_mag == EDGE_MAG_4) v2c_mag_before_BS = V_MAG3;
        else if (check_in_before_BS_mag == EDGE_MAG_3) v2c_mag_before_BS = V_MAG2;
        else if (check_in_before_BS_mag == EDGE_MAG_2) v2c_mag_before_BS = V_MAG1;
        else                                           v2c_mag_before_BS = V_MAG0;
#else
        if (check_in_before_BS_mag == EDGE_MAG_7)      v2c_mag_before_BS = V_VERY_STRONG;
        else if (check_in_before_BS_mag == EDGE_MAG_5) v2c_mag_before_BS = V_NORMAL_STRONG;
        else if (check_in_before_BS_mag == EDGE_MAG_3) v2c_mag_before_BS = V_NORMAL_WEAK;
        else                                           v2c_mag_before_BS = V_VERY_WEAK;
#endif
        /* Read VNU output (after BS ==> Extreme ECC 2.2 방식) */
        check_in = VNU_out3[mux_idx][z_mem_shift[j]];
        check_in_mag = abs(check_in);
        /* domain 변경 */
        if (check_in >= 0)    v2c_sgn = V_PLUS;
        else                  v2c_sgn = V_MINUS;
#if defined (__4_BIT_LLR__)
        if (check_in_mag == EDGE_MAG_8)      v2c_mag = V_MAG7;
        else if (check_in_mag == EDGE_MAG_7) v2c_mag = V_MAG6;
        else if (check_in_mag == EDGE_MAG_6) v2c_mag = V_MAG5;
        else if (check_in_mag == EDGE_MAG_5) v2c_mag = V_MAG4;
        else if (check_in_mag == EDGE_MAG_4) v2c_mag = V_MAG3;
        else if (check_in_mag == EDGE_MAG_3) v2c_mag = V_MAG2;
        else if (check_in_mag == EDGE_MAG_2) v2c_mag = V_MAG1;
        else                                 v2c_mag = V_MAG0;
#else
        if (check_in_mag == EDGE_MAG_7)      v2c_mag = V_VERY_STRONG;
        else if (check_in_mag == EDGE_MAG_5) v2c_mag = V_NORMAL_STRONG;
        else if (check_in_mag == EDGE_MAG_3) v2c_mag = V_NORMAL_WEAK;
        else                                 v2c_mag = V_VERY_WEAK;
#endif
        /* Read Check REG */
        pre_v2c_sgn = pre_exist_sgn_reg3[mux_idx][j];
        check_sum = Check_REG[bit_pos][IDX_CHECK_SUM];
        pre_v2c_sgn_before_BS = pre_exist_sgn_reg3_BS[mux_idx][j];
        CNU_Remove_Old_Sgn(iter, pre_v2c_sgn, &check_sum, jj);
        CNU_Update_New_Sgn(v2c_sgn, &check_sum);
        /* Write Check REG  */
        if (TRUE == store_checksum_REG) {
            Check_REG[bit_pos][IDX_CHECK_SUM] = check_sum;
        }
        /* Write Check SRAM (sign) */
        if (TRUE == store_edge_SRAM) {
            if (TRUE == Is_Iter_Type_Init(iter)) {
                Check_SRAM_sgn[bit_pos][position_c] = 0;
            }
            else {
                Check_SRAM_sgn[bit_pos][position_c] = v2c_sgn;
            }
        }
        /* Read MIN REG */
        min1_pos = REG_min1_pos[bit_pos];
        min1_value = REG_min1_value[bit_pos];
        min2_value = REG_min2_value[bit_pos];
        old_min1_value = min1_value;
        old_min2_value = min2_value;
        if ((TRUE == flag_BF_on)
#ifdef __AUTO_LLR_OPT__
            && (iter <= 4)
#else
            && (iter <= ITER_MAX_HBF)
#endif
            && (v_deg > DV_5)) { //1bit mode
            update_flag = FALSE;
        }
        else { //3bit mode
            /* Update min_pos, min_value, check_sum */
            CNU_Update_New_Mag(v2c_mag, &min1_value, &min2_value, &min1_pos, position_c, position_c, &update_flag, row_idx);
        
        /* Write REG (mag) */
        if (TRUE == store_min_REG) {
            REG_min1_pos[bit_pos] = min1_pos;
            REG_min1_value[bit_pos] = min1_value;
            REG_min2_value[bit_pos] = min2_value;
        }
    }
#if defined (__ECC_TV__)
        if (FLAG_HIGH == update_flag) {
            tv_upt_min[bit_pos] = FLAG_HIGH;
            tv_min_weak[bit_pos] = min1_value;
            tv_min_weak2[bit_pos] = min2_value;
        }
        // HCU용 TV 출력 위해서 추가
        if (jj < HCU_start) {
            jj_temp = jj; mux_idx_temp = mux_idx;
        }
        else if (jj == HCU_start && mux_idx < 8) {
            if (iter % 2 == 0) { jj_temp = HCU_start; mux_idx_temp = mux_idx; }
            else { jj_temp = HCU_start + 1; mux_idx_temp = mux_idx; }
        }
        else if (jj == HCU_start && mux_idx >= 8) {
            if (iter % 2 == 0) { jj_temp = HCU_start + 1; mux_idx_temp = mux_idx - 8; }
            else { jj_temp = HCU_start; mux_idx_temp = mux_idx - 8; }
        }
        else if (jj == HCU_end && mux_idx < 8) {
            if (iter % 2 == 0) { jj_temp = HCU_end + 1; mux_idx_temp = mux_idx; }
            else { jj_temp = HCU_end + 2; mux_idx_temp = mux_idx; }
        }
        else if (jj == HCU_end && mux_idx >= 8) {
            if (iter % 2 == 0) { jj_temp = HCU_end + 2; mux_idx_temp = mux_idx - 8; }
            else { jj_temp = HCU_end + 1; mux_idx_temp = mux_idx - 8; }
        }
        else {
            jj_temp = jj + m_PCM->punct_col_num; mux_idx_temp = mux_idx;
        }
        //if (jj == 0 && mux_idx < 8) {
        //  if (iter % 2 == 0) { jj_temp = 0; mux_idx_temp = mux_idx; }
        //  else { jj_temp = 1; mux_idx_temp = mux_idx; }
        //}
        //else if (jj == 0 && mux_idx >= 8) {
        //  if (iter % 2 == 0) { jj_temp = 1; mux_idx_temp = mux_idx - 8; }
        //  else { jj_temp = 0; mux_idx_temp = mux_idx - 8; }
        //}
        //else if (jj == 1 && mux_idx < 8) {
        //  if (iter % 2 == 0) { jj_temp = 2; mux_idx_temp = mux_idx; }
        //  else { jj_temp = 3; mux_idx_temp = mux_idx; }
        //}
        //else if (jj == 1 && mux_idx >= 8) {
        //  if (iter % 2 == 0) { jj_temp = 3; mux_idx_temp = mux_idx - 8; }
        //  else { jj_temp = 2; mux_idx_temp = mux_idx - 8; }
        //}
        //else { jj_temp = jj + 2; mux_idx_temp = mux_idx; }
        /* new v2c sgn (before BS) */
        if (TRUE == Is_Iter_Type_Init(iter)){
#if defined(__4_BIT_LLR__)
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + j] = V_PLUS; // sign plus
#else
            tv_new_sgn_mag[mux_idx][(3 * m_PCM->z_sb * jj) + j] = V_PLUS; // sign plus
#if defined(__HALF_COL_UPDATE__)
            tv_new_sgn_mag_HCU[mux_idx_temp][(3 * m_PCM->z_sb * jj_temp) + j] = V_PLUS; // sign plus
            tv_new_sgn_mag_HCU_in[mux_idx_temp][m_PCM->z_sb * jj_temp + j] = check_in_before_BS; // TV debug8: tv_new_sgn_mag_HCU_input
            tv_new_sgn_mag_HCU_in_nq[mux_idx_temp][m_PCM->z_sb * jj_temp + j] = check_in_before_BS_nq; // TV debug8: tv_new_sgn_mag_HCU_input
#endif
#endif
        }
        else {
#if defined(__4_BIT_LLR__)
            if (v2c_sgn_before_BS % 2 == 1) { tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + j] = V_MINUS; } //sign minus
            else                             { tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + j] = V_PLUS; }  // sign plus
#else
            if (v2c_sgn_before_BS % 2 == 1) {
                tv_new_sgn_mag[mux_idx][(3 * m_PCM->z_sb * jj) + j] = V_MINUS; //sign minus
#if defined(__HALF_COL_UPDATE__)
                tv_new_sgn_mag_HCU[mux_idx_temp][(3 * m_PCM->z_sb * jj_temp) + j] = V_MINUS; // sign minus
                tv_new_sgn_mag_HCU_in[mux_idx_temp][m_PCM->z_sb * jj_temp + j] = check_in_before_BS; // TV debug8: tv_new_sgn_mag_HCU_input
                tv_new_sgn_mag_HCU_in_nq[mux_idx_temp][m_PCM->z_sb * jj_temp + j] = check_in_before_BS_nq; // TV debug8: tv_new_sgn_mag_HCU_input
#endif
            }
            else {
                tv_new_sgn_mag[mux_idx][(3 * m_PCM->z_sb * jj) + j] = V_PLUS; // sign plus
#if defined(__HALF_COL_UPDATE__)
                tv_new_sgn_mag_HCU[mux_idx_temp][(3 * m_PCM->z_sb * jj_temp) + j] = V_PLUS; // sign plus
                tv_new_sgn_mag_HCU_in[mux_idx_temp][m_PCM->z_sb * jj_temp + j] = check_in_before_BS; // TV debug8: tv_new_sgn_mag_HCU_input
                tv_new_sgn_mag_HCU_in_nq[mux_idx_temp][m_PCM->z_sb * jj_temp + j] = check_in_before_BS_nq; // TV debug8: tv_new_sgn_mag_HCU_input
#endif
            }
#endif
        }
#if defined(__4_BIT_LLR__)
        /* new v2c mag (before BS), 4-bit precision */
        if (EDGE_MAG_8 == check_in_before_BS_mag) {
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 1; // mag MSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 1; // mag CSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 1; // mag LSB
        }
        else if (EDGE_MAG_7 == check_in_before_BS_mag) {
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 1; // mag MSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 1; // mag CSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 0; // mag LSB
        }
        else if (EDGE_MAG_6 == check_in_before_BS_mag) {
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 1; // mag MSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 0; // mag CSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 1; // mag LSB
        }
        else if (EDGE_MAG_5 == check_in_before_BS_mag) {
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 1; // mag MSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 0; // mag CSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 0; // mag LSB
        }
        else if (EDGE_MAG_4 == check_in_before_BS_mag) {
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 0; // mag MSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 1; // mag CSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 1; // mag LSB
        }
        else if (EDGE_MAG_3 == check_in_before_BS_mag) {
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 0; // mag MSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 1; // mag CSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 0; // mag LSB
        }
        else if (EDGE_MAG_2 == check_in_before_BS_mag) {
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 0; // mag MSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 0; // mag CSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 1; // mag LSB
        }
        else {
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3)] = 0; // mag MSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 1] = 0; // mag CSB
            tv_new_sgn_mag[mux_idx][(4 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 3) + 2] = 0; // mag LSB
        }
#else
        /* new v2c mag (before BS), 3-bit precision */
        /* new v2c mag (before BS) */
        if (EDGE_MAG_7 == check_in_before_BS_mag) {
            tv_new_sgn_mag[mux_idx][(3 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2)] = 1; // mag MSB
            tv_new_sgn_mag[mux_idx][(3 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2) + 1] = 1; // mag LSB
#if defined(__HALF_COL_UPDATE__)
            tv_new_sgn_mag_HCU[mux_idx_temp][(3 * m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2)] = 1; // mag MSB
            tv_new_sgn_mag_HCU[mux_idx_temp][(3 * m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2) + 1] = 1; // mag LSB
#endif
        }
        else if (EDGE_MAG_5 == check_in_before_BS_mag) {
            tv_new_sgn_mag[mux_idx][(3 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2)] = 1; // mag MSB
            tv_new_sgn_mag[mux_idx][(3 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2) + 1] = 0; // mag LSB
#if defined(__HALF_COL_UPDATE__)
            tv_new_sgn_mag_HCU[mux_idx_temp][(3 * m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2)] = 1;// mag MSB
            tv_new_sgn_mag_HCU[mux_idx_temp][(3 * m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2) + 1] = 0;// mag LSB
#endif
        }
        else if (EDGE_MAG_3 == check_in_before_BS_mag) {
            tv_new_sgn_mag[mux_idx][(3 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2)] = 0;// mag MSB
            tv_new_sgn_mag[mux_idx][(3 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2) + 1] = 1;// mag LSB
#if defined(__HALF_COL_UPDATE__)
            tv_new_sgn_mag_HCU[mux_idx_temp][(3 * m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2)] = 0;// mag MSB
            tv_new_sgn_mag_HCU[mux_idx_temp][(3 * m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2) + 1] = 1;// mag LSB
#endif
        }
        else {
            tv_new_sgn_mag[mux_idx][(3 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2)] = 0;// mag MSB
            tv_new_sgn_mag[mux_idx][(3 * m_PCM->z_sb * jj) + m_PCM->z_sb + (j * 2) + 1] = 0;// mag LSB
#if defined(__HALF_COL_UPDATE__)
            tv_new_sgn_mag_HCU[mux_idx_temp][(3 * m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2)] = 0;// mag MSB
            tv_new_sgn_mag_HCU[mux_idx_temp][(3 * m_PCM->z_sb * jj_temp) + m_PCM->z_sb + (j * 2) + 1] = 0;// mag LSB
#endif
        }
#endif
        /* old v2c sgn */
        if (TRUE == Is_Iter_Type_Init(iter)) {
            tv_old_sgn[mux_idx][m_PCM->z_sb * jj + j] = 0;
#if defined(__HALF_COL_UPDATE__)
            tv_old_sgn_HCU[mux_idx_temp][m_PCM->z_sb * jj_temp + j] = 0;
#endif
        }
        else {
            tv_old_sgn[mux_idx][m_PCM->z_sb * jj + j] = pre_v2c_sgn_before_BS;
#if defined(__HALF_COL_UPDATE__)
            tv_old_sgn_HCU[mux_idx_temp][m_PCM->z_sb * jj_temp + j] = pre_v2c_sgn_before_BS;
#endif
        }
#endif
    }// end for loop (j)
    /* Update Syndrome */
/* Update Syndrome */
    if (TRUE == Is_Iter_Type_Init(iter)) {
        if (jj == m_PCM->N_b - 1) {
            if (ii == m_PCM->ColW[jj] - 1) {
                /* copy from checksum reg to syndrome reg */
                for (j = 0; j < m_PCM->M; j++) {
                    Syndrome[j] = Check_REG[j][IDX_CHECK_SUM];
                    // Puncturing Recovery 시작 전에 Syndrome 중간값 저장 -> TV 검증용
                    if (iter == 0) {
                        Syndrome_intermediate[j] = Syndrome[j];
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
                        Syndrome_intermediate_internal[jj][j] = Syndrome[j];
                        //Syndrome_intermediate_internal[jj - m_PCM->punct_col_num][j] = Syndrome[j];
#endif
                    }
                    Check_REG[j][IDX_CHECK_SUM] = 0;    // reset
                }
                //----
                // Puncturing Recovery
                if(iter == 0){
                // COL_BLK 127, 128를 에 version
#if defined(__RUN_PUNCT_RECOVERY__)
#ifdef __GENIE_PUNCT_RECOVERY__
                for (j = m_ecc_info->bit_pos.info_punc_start; j < m_ecc_info->bit_pos.info_punc_end; j++) {
                    Variable_mem[j] = m_genie_inv_cw[j];
                }
#else
#if defined(__HACRC_IKD_5B__)
#else
                for (int k = 0; k < m_PCM->punct_col_num; k++) {
                    for (int j = 0; j < m_PCM->z_sb; j++) {
                        m_PCM->punct_vote[k][j] = 0;
                        m_PCM->punct_vote_disjoint[k][j] = 0;
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
                        Punc_vote_Mag[k][j] = 0;
                        Punc_vote_decision[k][j] = 0;
                        for (int l = 0; l < m_PCM->M_b; l++) {
                            Punc_vote_Mag_Row[k][l][j] = 0;
                            Punc_vote_Mag_Row_before_BS[k][l][j] = 0;
                        }
#endif
                    }
                }
                for (int i = 0; i < m_PCM->M_b; i++) {
                    if(m_PCM->PCM_b[i][127] != -1 && m_PCM->PCM_b[i][128] == -1){
                    for (int z = 0; z < m_PCM->z_sb; z++) {
                        int idx_cn = m_PCM->z_sb * i + z;
                        int synd_val = Syndrome[idx_cn];
                        if (synd_val == 0) {
                            m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb]++;
                            m_PCM->punct_vote_disjoint[0][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb]++;
                            //m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                            //m_PCM->punct_vote_disjoint[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                        }
                        else {
                            m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb]--;
                            m_PCM->punct_vote_disjoint[0][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb]--;
                            //m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                            //m_PCM->punct_vote_disjoint[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                        
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
                        Punc_vote_Mag[0][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb] += 1;
                        Punc_vote_Mag_Row[0][i][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb] = 1;
                        Punc_vote_Mag_Row_before_BS[0][i][z] = 1;
                        //Punc_vote_Mag[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] += 1;
                        //Punc_vote_Mag_Row[0][i][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] = 1;
                        //Punc_vote_Mag_Row_before_BS[0][i][z] = 1;
#endif
                    }
                }
            }
            if (m_PCM->punct_col_num >= 2) {
                for (int z = 0; z < m_PCM->z_sb; z++) {
                    int idx_cn = m_PCM->z_sb * i + z;
                    int synd_val = Syndrome[idx_cn];
                    if (synd_val == 0) {
                        m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb]++;
                        m_PCM->punct_vote_disjoint[1][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb]++;
                        //m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                        //m_PCM->punct_vote_disjoint[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                    }
                    else {
                        m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb]--;
                        m_PCM->punct_vote_disjoint[1][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb]--;
                        //m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                        //m_PCM->punct_vote_disjoint[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
                        Punc_vote_Mag[1][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb] += 1;
                        Punc_vote_Mag_Row[1][i][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb] = 1;
                        Punc_vote_Mag_Row_before_BS[1][i][z] = 1;
                        //Punc_vote_Mag[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] += 1;
                        //Punc_vote_Mag_Row[1][i][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] = 1;
                        //Punc_vote_Mag_Row_before_BS[1][i][z] = 1;
#endif
                    }
                }
            }
        }
                /*
                for (int z = 0; z < m_PCM->z_sb; z++) {
                    m_PCM->punct_vote[0][z] = Syndrome[m_ecc_info->bit_pos.info_sn_start + z];
                    m_PCM->punct_vote_disjoint[0][z - m_ecc_info->bit_pos.info_sn_start] = 10;
                }
                */
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
                for (int i = 0; i < m_PCM->M_b; i++) {
                    if (m_PCM->PCM_b[i][0] != -1 && m_PCM->PCM_b[i][1] != -1) {
                    }
                }
#endif
                for (int i = 0; i < m_PCM->M_b; i++) {
                    if (m_PCM->PCM_b[i][127] != -1 && m_PCM->PCM_b[i][128] != -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            int synd_val = Syndrome[idx_cn];
                            if (synd_val == 0) {
                                if (m_PCM->punct_vote_disjoint[0][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 4] % m_PCM->z_sb] > 0) {
                                    m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb]++;
                                }
                            else {
                                m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb]--;
                            }
                            //if (m_PCM->punct_vote_disjoint[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] > 0) {
                            //  m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]++;
                            //}
                            //else {
                            //}
                            }
                            else {
                                if (m_PCM->punct_vote_disjoint[0][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 4] % m_PCM->z_sb] > 0) {
                                    m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb]--;
                                }
                                else {
                                    m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb]++;
                                }
                            //if (m_PCM->punct_vote_disjoint[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] > 0) {
                            //  m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]--;
                            //}
                            //else {
                            //  m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]++;
                            //}
                            }
                        }
                    }
                }
                for (int z = 0; z < m_PCM->z_sb; z++) m_PCM->punct_vote_disjoint[1][z] = m_PCM->punct_vote[1][z];
                for (int z = m_PCM->z_sb - m_ecc_info->shortened_bit_info - m_ecc_info->shortened_bit_info_offset_end; z < m_PCM->z_sb - m_ecc_info->shortened_bit_info_offset_end; z++) {
                    m_PCM->punct_vote[1][z] = 10;
                    m_PCM->punct_vote_disjoint[1][z] = 10;
                }
                for (int i = 0; i < m_PCM->M_b; i++) {
                    if (m_PCM->PCM_b[i][127] != -1 && m_PCM->PCM_b[i][128] != -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            int synd_val = Syndrome[idx_cn];
                            if (synd_val == 0) {
                                if (m_PCM->punct_vote_disjoint[1][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb] > 0) {
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 4] % m_PCM->z_sb]++;
                                }
                            else {
                                m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 4] % m_PCM->z_sb]--;
                            }
                            //if (m_PCM->punct_vote_disjoint[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb] > 0) {
                            //  m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                            //}
                            //else {
                            //  m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                            //}
                            }
                            else {
                                if (m_PCM->punct_vote_disjoint[1][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 3] % m_PCM->z_sb] > 0) {
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 4] % m_PCM->z_sb]--;
                                }
                                else {
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][m_PCM->RowW[i] - 4] % m_PCM->z_sb]++;
                                }
                            //if (m_PCM->punct_vote_disjoint[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb] > 0) {
                            //  m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                            //}
                            //else {
                            //}
                            }
                        }
                    }
                }
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
                for (int i = 0; i < m_PCM->punct_col_num; i++) {
                    for (int z = 0; z < m_PCM->z_sb; z++) {
                        if (Punc_vote_Mag[i][z] == 16) Punc_vote_Mag[i][z] = 15;
                        if (Punc_vote_Mag[i][z] > 8) { Punc_vote_decision[i][z] = 1; }
                        else { Punc_vote_decision[i][z] = 0; }
                    }
                }
                // shortening 부분 zero-padding 처리 (vote 결과 상관없이)
                for (int z = m_ecc_info->bit_pos.info_sh_start; z < m_ecc_info->bit_pos.info_sh_end; z++) {
                    Punc_vote_decision[0][z] = 0;
                }
#endif
                /*
                for (int z = m_ecc_info->bit_pos.info_sh_start; z < m_ecc_info->bit_pos.info_sh_end; z++) {
                    m_PCM->punct_vote[0][z - m_ecc_info->bit_pos.info_sh_start] = 15;
                }*/
                for (int z = m_PCM->z_sb - m_ecc_info->shortened_bit_info - m_ecc_info->shortened_bit_info_offset_end; z < m_PCM->z_sb - m_ecc_info->shortened_bit_info_offset_end; z++) {
                    m_PCM->punct_vote[1][z] = 15;
                }
                PR_ERR_CNT = 0;
                PR_ERR_MAG_CNT = 0;
                PR_MAG_CNT = 0;
                for (int z = 0; z < m_PCM->z_sb; z++) {
                    if (m_PCM->punct_vote[0][z] >= 0) {
                        Variable_mem[m_PCM->z_sb * (HCU_start) + z] = 0;
                    }
                    else {
                        Variable_mem[m_PCM->z_sb * (HCU_start) + z] = 1;
                    }
                    if (m_PCM->punct_vote[1][z] >= 0) {
                        Variable_mem[m_PCM->z_sb * (HCU_end) + z] = 0;
                    }
                    else {
                        Variable_mem[m_PCM->z_sb * (HCU_end) + z] = 1;
                    }
                }
#endif
#endif // __RUN_PUNCT_RECOVERY__
/////////////////////////////////////////////////////////////
// Col_Blk 0, 1일 때 version
/*
#if defined(__RUN_PUNCT_RECOVERY__)
#ifdef __GENIE_PUNCT_RECOVERY__
                for (j = m_ecc_info->bit_pos.info_punc_start; j < m_ecc_info->bit_pos.info_punc_end; j++) {
                    Variable_mem[j] = m_genie_inv_cw[j];
                }
#else
#if defined(__HACRC_IKD_5B__)
#else
                for (int k = 0; k < m_PCM->punct_col_num; k++) {
                    for (int j = 0; j < m_PCM->z_sb; j++) {
                        m_PCM->punct_vote[k][j] = 0;
                        m_PCM->punct_vote_disjoint[k][j] = 0;
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
                        Punc_vote_Mag[k][j] = 0;
                        Punc_vote_decision[k][j] = 0;
                        for (int l = 0;l < m_PCM->M_b;l++) {
                            Punc_vote_Mag_Row[k][l][j] = 0;
                            Punc_vote_Mag_Row_before_BS[k][l][j] = 0;
                        }
#endif
                    }
                }
                for (int i = 0; i < m_PCM->M_b; i++) {
                    if (m_PCM->PCM_b[i][0] != -1 && m_PCM->PCM_b[i][1] == -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            int synd_val = Syndrome[idx_cn];
                            if (synd_val == 0) {
                                m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                                m_PCM->punct_vote_disjoint[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                            }
                            else {
                                m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                                m_PCM->punct_vote_disjoint[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
                                Punc_vote_Mag[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] += 1;
                                Punc_vote_Mag_Row[0][i][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] = 1;
                                Punc_vote_Mag_Row_before_BS[0][i][z] = 1;
#endif
                            }
                        }
                    }
                    else if (m_PCM->PCM_b[i][0] == -1 && m_PCM->PCM_b[i][1] != -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            int synd_val = Syndrome[idx_cn];
                            if (synd_val == 0) {
                                m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                                m_PCM->punct_vote_disjoint[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                            }
                            else {
                                m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                                m_PCM->punct_vote_disjoint[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
                                Punc_vote_Mag[1][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] += 1;
                                Punc_vote_Mag_Row[1][i][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] = 1;
                                Punc_vote_Mag_Row_before_BS[1][i][z] = 1;
#endif
                            }
                        }
                    }
                }
                for (int z = m_ecc_info->bit_pos.info_sh_start; z < m_ecc_info->bit_pos.info_sh_end; z++) {
                    m_PCM->punct_vote[0][z] = 10;
                    m_PCM->punct_vote_disjoint[0][z] = 10;
                }
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
                for (int i = 0; i < m_PCM->M_b; i++) {
                    if (m_PCM->PCM_b[i][0] != -1 && m_PCM->PCM_b[i][1] != -1) {
                    }
                }
#endif
                for (int i = 0; i < m_PCM->M_b; i++) {
                    if (m_PCM->PCM_b[i][0] != -1 && m_PCM->PCM_b[i][1] != -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int synd_val = Syndrome[idx_cn];
                            if (synd_val == 0) {
                                if (m_PCM->punct_vote_disjoint[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] > 0) {
                                    m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]++;
                                }
                            else {
                                m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]--;
                                }
                            }
                            else {
                                if (m_PCM->punct_vote_disjoint[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb] > 0) {
                                    m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]--;
                                }
                                else {
                                    m_PCM->punct_vote[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb]++;
                                }
                            }
                        }
                    }
                }
                for (int z = 0; z < m_PCM->z_sb; z++) m_PCM->punct_vote_disjoint[1][z] = m_PCM->punct_vote[1][z];
                for (int i = 0; i < m_PCM->M_b; i++) {
                    if (m_PCM->PCM_b[i][0] != -1 && m_PCM->PCM_b[i][1] != -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            int synd_val = Syndrome[idx_cn];
                            if (synd_val == 0) {
                                if (m_PCM->punct_vote_disjoint[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb] > 0) {
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                                }
                                else {
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                                }
                            }
                            else {
                                if (m_PCM->punct_vote_disjoint[1][m_PCM->C_net[idx_cn][1] % m_PCM->z_sb] > 0) {
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]--;
                                }
                                else {
                                    m_PCM->punct_vote[0][m_PCM->C_net[idx_cn][0] % m_PCM->z_sb]++;
                                }
                            }
                        }
                    }
                }
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
                for (int i = 0;i < m_PCM->punct_col_num;i++) {
                    for (int z = 0;z < m_PCM->z_sb;z++) {
                        if (Punc_vote_Mag[i][z] == 16) Punc_vote_Mag[i][z] = 15;
                        if (Punc_vote_Mag[i][z] > 8) { Punc_vote_decision[i][z] = 1; }
                        else { Punc_vote_decision[i][z] = 0; }
                    }
                }
                // shortening 부분 zero-padding 처리 (vote 결과 상관없이)
                for (int z = m_ecc_info->bit_pos.info_sn_start;z < m_ecc_info->bit_pos.info_sn_end;z++) {
                    Punc_vote_decision[0][z] = 0;
                }
#endif
                for (int z = m_ecc_info->bit_pos.info_sh_start; z < m_ecc_info->bit_pos.info_sh_end; z++) {
                    m_PCM->punct_vote[0][z] = 15;
                }
                PR_ERR_CNT = 0;
                PR_ERR_MAG_CNT = 0;
                PR_MAG_CNT = 0;
                for (int z = 0; z < m_PCM->z_sb; z++) {
                    if (m_PCM->punct_vote[0][z] >= 0) {
                        Variable_mem[z] = 0;
                    }
                    else {
                        Variable_mem[z] = 1;
                    }
                    if (m_PCM->punct_vote[1][z] >= 0) {
                        Variable_mem[m_PCM->z_sb + z] = 0;
                    }
                    else {
                        Variable_mem[m_PCM->z_sb + z] = 1;
                    }
                }
            }
#endif
#endif // __RUN_PUNCT_RECOVERY__
/////////////////////////////////////////////////////////////
*/
                // Syndrome Vector Update using Recovered Punctured Bits
#if defined(__HACRC_IKD_5B__)
#else
                for (int i = 0; i < m_PCM->M_b; i++) {
                    if (m_PCM->PCM_b[i][127] != -1 && m_PCM->PCM_b[i][128] == -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            Syndrome[idx_cn] = (Syndrome[idx_cn] + Variable_mem[m_PCM->z_sb * (HCU_start) + ((z + m_PCM->PCM_b[i][127]) % m_PCM->z_sb)]) % 2;
                        }
                    }
                    else if (m_PCM->PCM_b[i][127] == -1 && m_PCM->PCM_b[i][128] != -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            Syndrome[idx_cn] = (Syndrome[idx_cn] + Variable_mem[m_PCM->z_sb * (HCU_end) + ((z + m_PCM->PCM_b[i][128]) % m_PCM->z_sb)]) % 2;
                        }
                    }
                    else {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            Syndrome[idx_cn] = (Syndrome[idx_cn] + Variable_mem[m_PCM->z_sb * (HCU_start) + ((z + m_PCM->PCM_b[i][127]) % m_PCM->z_sb)] + Variable_mem[m_PCM->z_sb * (HCU_end) + ((z + m_PCM->PCM_b[i][128]) % m_PCM->z_sb)]) % 2;
                        }
                    }
                }
                /*
                for (int i = 0; i < m_PCM->M_b; i++) {
                    if (m_PCM->PCM_b[i][0] != -1 && m_PCM->PCM_b[i][1] == -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            Syndrome[idx_cn] = (Syndrome[idx_cn] + Variable_mem[(z + m_PCM->PCM_b[i][0]) % m_PCM->z_sb]) % 2;
                        }
                    }
                    else if (m_PCM->PCM_b[i][0] == -1 && m_PCM->PCM_b[i][1] != -1) {
                        for (int z = 0; z < m_PCM->z_sb; z++) {
                            int idx_cn = m_PCM->z_sb * i + z;
                            Syndrome[idx_cn] = (Syndrome[idx_cn] + Variable_mem[(z + m_PCM->PCM_b[i][0]) % m_PCM->z_sb] + Variable_mem
                                [m_PCM->z_sb + ((z + m_PCM->PCM_b[i][1]) % m_PCM->z_sb)]) % 2;
                        }
                    }
                }*/
#endif
#endif
            } // if (iter==0) end
            //----
        }
    }
    // Syndrome intermediate interval vector 검증용
    else {
        if (ii == m_PCM->ColW[jj] - 1) {
            /* copy from checksum reg to syndrome reg */
            for (j = 0; j < m_PCM->M; j++) {
                if (iter == 0) {
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
                    Syndrome_intermediate_internal[jj][j] = Check_REG[j][IDX_CHECK_SUM];
                    //if (jj >= m_PCM->punct_col_num) {
                    //  Syndrome_intermediate_internal[jj - m_PCM->punct_col_num][j] = Check_REG[j][IDX_CHECK_SUM];
                    //}
#endif
                }
            }
        }
    }
}
/* Preupdate 후 syndrome weight calculation */
    if (iter == 0) {
        if (jj == m_PCM->N_b - 1) {
            if (ii == m_PCM->ColW[jj] - 1) {
                syn_weight = Compute_SW(TRUE);
                psyn_weight = Compute_PSW(TRUE);
#if defined(__ECC_TV__)
                for (int i = m_PCM->N - m_PCM->M - m_ecc_info->punctured_bit_info - m_ecc_info->shortened_bit_info; i < m_PCM->N - m_PCM->M; i++) {
                    Punc_one_cnt[i] = Variable_mem[i];
                }
                    // Col Blk 0, 1 Puncturing Case
                    // Col BLK 127, 128 Puncturing Case
                    // for (int i = 0; i < m_PCM->z_sb*2; i++) {
                    //  Punc_one_cnt[i] = Variable_mem[i];
                    //}
                    m_tv_dec_inter.Print_TV_SW_CSW(syn_weight);
                    m_tv_dec_inter.Print_TV_one_cnt_BLK(Punc_one_cnt);
                    // m_tv_dec_inter.Print_TV_VNU_out_temp(tv_new_sgn_mag_HCU);
#endif
            }
        }
    }
    /* Check-Sum Weight Calculation */
    if (jj == m_PCM->N_b - 1) {
        if (ii == m_PCM->ColW[jj] - 1) {
            cur_chk_sum_weight = Compute_CSW();
            Set_CSW(cur_chk_sum_weight);
#if defined(__ECC_TV__)
            m_tv_dec_inter.Print_TV_SW_CSW(mn, cur_chk_sum_weight);
#endif
            prev_min1_v_sum = Compute_Min1_Sum();
        }
    }
}
//================================================
// old V2C sign 값 제거
//================================================
void Decoder::CNU_Remove_Old_Sgn(int iter, int pre_v2c_sgn, int* check_sum, int col_idx)
{
	if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
		//TEMP_HY 기존 C-code에서 왜 Iter == 1에서 read x 는 operation이 없었는지 확인필요
#if defined (__RUN_PREPROCESSING__)
		if ((TRUE == flag_BF_on) &&
			(iter == 1) &&
			(col_idx == m_PCM->N_b - m_PCM->M_b - 3 || col_idx == m_PCM->N_b - m_PCM->M_b - 2)) {
			Intentional_Blank();	// read o, BF_mode에서 Iter 1 직전에 Pre-processing을 Col_0 에서 수행 -> 해당 column은 read 수행
		}
		else if ((FALSE == flag_BF_on) &&
			(iter == ITER_MAX_HBF + 1) &&
			(col_idx == m_PCM->N_b - m_PCM->M_b - 3 || col_idx == m_PCM->N_b - m_PCM->M_b - 2)) {
			Intentional_Blank();	// read o, BF_mode_off에서 Iter ITER_MAX_HBF + 1 직전에 Pre-processing을 Col_0 에서 수행 -> 해당 column은 read 수행
		}
		else if (TRUE == Is_Iter_Type_Edge_Clear(iter)) {
			pre_v2c_sgn = 0;// read x
		}
		else {
			Intentional_Blank();	// read o
		}
#else
		if (TRUE == Is_Iter_Type_Edge_Clear(iter)) {
			pre_v2c_sgn = 0;
		}
#endif
	}
	else {
		if (TRUE == Is_Iter_Type_Edge_Clear(iter)) {
			pre_v2c_sgn = 0;
		}
	}
	*check_sum = (*check_sum + pre_v2c_sgn) % 2;
}
//================================================
// min1, min2, min1_pos를 사용하는 QBS 방식에서
// new V2C sign 반영
//================================================
void Decoder::CNU_Update_New_Mag(int v2c_mag, int* min1_value, int* min2_value, int* min1_pos, int cur_pos, int cur_pos_p2, int* update_flag, int row_idx)
{
	*update_flag = FLAG_LOW;
	/* min update */
	if (*min1_pos == cur_pos_p2) {
		*min1_value = *min2_value;
#if defined (__4_BIT_LLR__)
		*min2_value = V_MAG7;
#else
		*min2_value = V_VERY_STRONG;
#endif
		*update_flag = FLAG_HIGH;
	}
	if (v2c_mag <= *min1_value) {
		*min1_value = v2c_mag;
		*min1_pos = cur_pos_p2;
#if defined (__4_BIT_LLR__)
		*min2_value = V_MAG7;
#else
		*min2_value = V_VERY_STRONG;
#endif
		*update_flag = FLAG_HIGH;
	}
	else if (v2c_mag <= *min2_value) {
		*min2_value = v2c_mag;
		*update_flag = FLAG_HIGH;
	}
	else {
		Intentional_Blank();
	}
}
void Decoder::CNU_Update_New_Sgn(int v2c_sgn, int* check_sum)
{	/* check sum update */
	*check_sum = (*check_sum + v2c_sgn) % 2;
}
//================================================
// Update VNU out without VNU_in
// 1) VNU_out part
// 2) decision part
//================================================
void Decoder::VN_Cal_Pre(int jj)
{
	int ii;
	int i;
	int idx_offset = jj * m_PCM->z_sb;
	int bit_pos;
	int mux_idx;
	if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
		/* update VNU_out*/
		for (ii = 0; ii < m_PCM->ColW[jj]; ii++) {
			mux_idx = m_PCM->Mux_idx[ii][jj];
			for (i = 0; i < m_PCM->z_sb; i++) {
				bit_pos = idx_offset + i;
				if ((bit_pos >= m_ecc_info->bit_pos.info_sh_start) && (bit_pos < m_ecc_info->bit_pos.info_sh_end)) {
					/* shortening */
#if defined (__4_BIT_LLR__)
					VNU_out[mux_idx][i] = EDGE_MAG_8;
#else
					VNU_out[mux_idx][i] = EDGE_MAG_7;
#endif
				}
				else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start1) && (bit_pos < m_ecc_info->bit_pos.info_punc_end1)) {
					/* puncturing (info part) */
#if defined(__RUN_PUNCT_RECOVERY__)
					VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_1);
					//VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_4);
#else
            VNU_out[mux_idx][i] = EDGE_MAG_1;
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start2) && (bit_pos < m_ecc_info->bit_pos.info_punc_end2)) {
                /* puncturing (info part) */
#if defined(__RUN_PUNCT_RECOVERY__)
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_1);
                //VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_4);
#else
                VNU_out[mux_idx][i] = EDGE_MAG_1;
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.info_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.info_no_punc_end)) {
                /* HD input (+ or -) */
#if defined (__4_BIT_LLR__)
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_4);
#else
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_3);
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.parity_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_no_punc_end)) {
                /* HD input (+ or -) */
#if defined (__4_BIT_LLR__)
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_4);
#else
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_3);
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.parity_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_punc_end)) {
                /* puncturing (parity part) */
#if defined(__RUN_PUNCT_RECOVERY__)
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_1);
#else
                VNU_out[mux_idx][i] = EDGE_MAG_1;
#endif
            }
#if defined (__LOG_VNU_IN_OUT__)
            m_log_VNU_out[mux_idx][bit_pos] = VNU_out[mux_idx][i];
#endif
            VNU_out_nq[mux_idx][i] = VNU_out[mux_idx][i];
        }
    }
}
else if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
    /* update VNU_out*/
    for (ii = 0; ii < m_PCM->ColW[jj]; ii++) {
        mux_idx = m_PCM->Mux_idx[ii][jj];
        for (i = 0; i < m_PCM->z_sb; i++) {
            bit_pos = idx_offset + i;
            if ((bit_pos >= m_ecc_info->bit_pos.info_sh_start) && (bit_pos < m_ecc_info->bit_pos.info_sh_end)) {
                /* shortening */
#if defined (__4_BIT_LLR__)
                VNU_out[mux_idx][i] = EDGE_MAG_8;
#else
                VNU_out[mux_idx][i] = EDGE_MAG_7;
#endif
                Soft_LLR[bit_pos] = CH_LLR_MAX;
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start1) && (bit_pos < m_ecc_info->bit_pos.info_punc_end1)) {
                /* puncturing (info part) */
#if defined(__RUN_PUNCT_RECOVERY__)
                //VNU_out[mux_idx][i] = EDGE_MAG_1;
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_1);
                Soft_LLR[bit_pos] = CH_LLR_MIN;
#else
                VNU_out[mux_idx][i] = EDGE_MAG_1;
                Soft_LLR[bit_pos] = CH_LLR_MIN;
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start2) && (bit_pos < m_ecc_info->bit_pos.info_punc_end2)) {
                /* puncturing (info part) */
#if defined(__RUN_PUNCT_RECOVERY__)
                //VNU_out[mux_idx][i] = EDGE_MAG_1;
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_1);
                Soft_LLR[bit_pos] = CH_LLR_MIN;
#else
                VNU_out[mux_idx][i] = EDGE_MAG_1;
                Soft_LLR[bit_pos] = CH_LLR_MIN;
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.info_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.info_no_punc_end)) {
                /* SD input */
                VNU_out[mux_idx][i] = Soft_LLR[bit_pos];
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.parity_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_no_punc_end)) {
                VNU_out[mux_idx][i] = Soft_LLR[bit_pos];
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.parity_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_punc_end)) {
                /* puncturing (parity part) */
                //VNU_out[mux_idx][i] = EDGE_MAG_1;
                //Soft_LLR[bit_pos] = CH_LLR_MIN;
#if defined(__RUN_PUNCT_RECOVERY__)
                //VNU_out[mux_idx][i] = EDGE_MAG_1;
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_1);
                Soft_LLR[bit_pos] = CH_LLR_MIN;
#else
                VNU_out[mux_idx][i] = EDGE_MAG_1;
                Soft_LLR[bit_pos] = CH_LLR_MIN;
#endif
            }
            VNU_out_nq[mux_idx][i] = VNU_out[mux_idx][i];
            /* clipping */
#if defined (__4_BIT_LLR__)
            if (VNU_out[mux_idx][i] > EDGE_MAG_8)       VNU_out[mux_idx][i] = EDGE_MAG_8;
            else if (VNU_out[mux_idx][i] < -EDGE_MAG_8) VNU_out[mux_idx][i] = -EDGE_MAG_8;
#else
            if (VNU_out[mux_idx][i] > EDGE_MAG_7)       VNU_out[mux_idx][i] = EDGE_MAG_7;
            else if (VNU_out[mux_idx][i] < -EDGE_MAG_7) VNU_out[mux_idx][i] = -EDGE_MAG_7;
#endif
#if defined (__LOG_VNU_IN_OUT__)
            m_log_VNU_out[mux_idx][bit_pos] = VNU_out[mux_idx][i];
#endif
            }
        }
    }
#if defined (__ECC_TV__)
if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
    if ((jj >= m_PCM->N_b - m_PCM->M_b) && (jj < m_PCM->N_b)) {
        for (i = 0; i < m_PCM->z_sb; i++) {
            bit_pos = idx_offset + i;
            tv_llr_out[bit_pos] = 5;
        }
    }
    else {
        for (i = 0; i < m_PCM->z_sb; i++) {
            bit_pos = idx_offset + i;
            if (Variable_mem[bit_pos] == 0)
                tv_llr_out[bit_pos] = 5;
            else
                tv_llr_out[bit_pos] = -5;
        }
    }
}
else if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
    for (ii = 0; ii < m_PCM->ColW[jj]; ii++) {
        for (i = 0; i < m_PCM->z_sb; i++) {
            /* C2V output으로 C2V module에서 출력해야 하나 연산을 skip한 관계로 이 함수에서 값을 clear 함 */
            //tv_vtc_inp[ii][4 * (m_PCM->z_sb * jj) + i] = 0;    // sign
            //tv_vtc_inp[ii][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (i * 3) + 2] = 1; // mag LSB
            tv_vtc_inp[ii][(3 * m_PCM->z_sb * jj) + i] = 0; // sign
            tv_vtc_inp[ii][(3 * m_PCM->z_sb * jj) + m_PCM->z_sb + (i * 2)] = 0; // mag MSB
            tv_vtc_inp[ii][(3 * m_PCM->z_sb * jj) + m_PCM->z_sb + (i * 2) + 1] = 0; // mag LSB
        }
    }
    for (i = 0; i < m_PCM->z_sb; i++) {
        bit_pos = idx_offset + i;
        tv_llr_out[bit_pos] = Soft_LLR[bit_pos];
        //printf("[%d]: tv_llr_out=%d\n", bit_pos, tv_llr_out[bit_pos]);
    }
}
#endif
    /* make hard decision */
    for (i = 0; i < m_PCM->z_sb; i++) {
        bit_pos = idx_offset + i;
        if (Variable_mem[bit_pos] == 0) cwc[bit_pos] = 0;
        else                            cwc[bit_pos] = 1;
        /* 예외처리 2021.08.05 WIKI 참고*/
        if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start1) && (bit_pos < m_ecc_info->bit_pos.info_punc_end1)) {
            //cwc[bit_pos] = 1;
            if (Variable_mem[bit_pos] == 0) cwc[bit_pos] = 0;
            else                            cwc[bit_pos] = 1;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start2) && (bit_pos < m_ecc_info->bit_pos.info_punc_end2)) {
            //cwc[bit_pos] = 1;
            if (Variable_mem[bit_pos] == 0) cwc[bit_pos] = 0;
            else                            cwc[bit_pos] = 1;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.parity_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_punc_end)) {
            //cwc[bit_pos] = 1;
            if (Variable_mem[bit_pos] == 0) cwc[bit_pos] = 0;
            else                            cwc[bit_pos] = 1;
        }
    }
}
//================================================
// Update VNU out without VNU_in
// 1) VNU_out part
// 2) decision part
//================================================
void Decoder::VN_Cal_Pre_HCU(int jj, int G_idx)
{
    int ii;
    int i;
    int idx_offset = jj * m_PCM->z_sb;
    int bit_pos;
    int mux_idx;
    int current_G_idx;
    int start_idx = 0;
    int end_idx = 0;
    int separate_v_deg;
    if (jj == HCU_start) {
        separate_v_deg = SEPARATE_V_DEG_1;
    }
    else if (jj == HCU_end) {
        separate_v_deg = SEPARATE_V_DEG_2;
    }
    current_G_idx = (G_idx + mn) % 2;
    if (current_G_idx == 0) {
        //start_idx = 0; end_idx = m_PCM->ColW[jj] / 2;
        start_idx = 0; end_idx = separate_v_deg;
    }
    else if (current_G_idx == 1) {
        //start_idx = m_PCM->ColW[jj] / 2; end_idx = m_PCM->ColW[jj];
        start_idx = separate_v_deg; end_idx = m_PCM->ColW[jj];
    }
    if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
        /* update VNU_out*/
        for (ii = start_idx; ii < end_idx; ii++) {
            mux_idx = m_PCM->Mux_idx[ii][jj];
            for (i = 0; i < m_PCM->z_sb; i++) {
                bit_pos = idx_offset + i;
                if ((bit_pos >= m_ecc_info->bit_pos.info_sh_start) && (bit_pos < m_ecc_info->bit_pos.info_sh_end)) {
                /* shortening */
#if defined(__4_BIT_LLR__)
                VNU_out[mux_idx][i] = EDGE_MAG_8;
#else
                VNU_out[mux_idx][i] = EDGE_MAG_7;
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start1) && (bit_pos < m_ecc_info->bit_pos.info_punc_end1)) {
                /* puncturing (info part) */
#if defined(__RUN_PUNCT_RECOVERY__)
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_1);
                //VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_4);
#else
                VNU_out[mux_idx][i] = EDGE_MAG_1;
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start2) && (bit_pos < m_ecc_info->bit_pos.info_punc_end2)) {
                /* puncturing (info part) */
#if defined(__RUN_PUNCT_RECOVERY__)
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_1);
                //VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_4);
#else
                VNU_out[mux_idx][i] = EDGE_MAG_1;
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.info_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.info_no_punc_end)) {
                /* HD input (+ or -) */
#if defined (__4_BIT_LLR__)
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_4);
#else
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_3);
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.parity_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_no_punc_end)) {
                /* HD input (+ or -) */
#if defined (__4_BIT_LLR__)
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_4);
#else
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_3);
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.parity_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_punc_end)) {
                /* puncturing (parity part) */
                VNU_out[mux_idx][i] = EDGE_MAG_1;
            }
#if defined (__LOG_VNU_IN_OUT__)
            m_log_VNU_out[mux_idx][bit_pos] = VNU_out[mux_idx][i];
#endif
            VNU_out_nq[mux_idx][i] = VNU_out[mux_idx][i];
        }
    }
}
else if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
    /* update VNU_out*/
    for (ii = start_idx; ii < end_idx; ii++) {
        mux_idx = m_PCM->Mux_idx[ii][jj];
        for (i = 0; i < m_PCM->z_sb; i++) {
            bit_pos = idx_offset + i;
if ((bit_pos>=m_ecc_info->bit_pos.info_sh_start) && (bit_pos < m_ecc_info -> bit_pos.info_sh_end)){
#if defined (__4_BIT_LLR__)
                VNU_out[mux_idx][i] = EDGE_MAG_8;
#else
                VNU_out[mux_idx][i] = EDGE_MAG_7;
#endif
                Soft_LLR[bit_pos] = CH_LLR_MAX;
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start1) && (bit_pos < m_ecc_info->bit_pos.info_punc_end1)) {
                /* puncturing (info part) */
#if defined(__RUN_PUNCT_RECOVERY__)
                //VNU_out[mux_idx][i] = EDGE_MAG_1;
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_1);
                Soft_LLR[bit_pos] = CH_LLR_MIN;
#else
                VNU_out[mux_idx][i] = EDGE_MAG_1;
                Soft_LLR[bit_pos] = CH_LLR_MIN;
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start2) && (bit_pos < m_ecc_info->bit_pos.info_punc_end2)) {
                /* puncturing (info part) */
#if defined(__RUN_PUNCT_RECOVERY__)
                //VNU_out[mux_idx][i] = EDGE_MAG_1;
                VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_1);
                Soft_LLR[bit_pos] = CH_LLR_MIN;
                #else
                VNU_out[mux_idx][i] = EDGE_MAG_1;
                Soft_LLR[bit_pos] = CH_LLR_MIN;
#endif
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.info_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.info_no_punc_end)) {
                /* SD input */
                VNU_out[mux_idx][i] = Soft_LLR[bit_pos];
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.parity_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_no_punc_end)) {
                /* SD input */
                VNU_out[mux_idx][i] = Soft_LLR[bit_pos];
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.parity_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_punc_end)) {
                /* puncturing (parity part) */
                VNU_out[mux_idx][i] = EDGE_MAG_1;
                Soft_LLR[bit_pos] = CH_LLR_MIN;
            }
            VNU_out_nq[mux_idx][i] = VNU_out[mux_idx][i];
            /* clipping */
#if defined (__4_BIT_LLR__)
            if (VNU_out[mux_idx][i] > EDGE_MAG_8)       VNU_out[mux_idx][i] = EDGE_MAG_8;
            else if (VNU_out[mux_idx][i] < -EDGE_MAG_8) VNU_out[mux_idx][i] = -EDGE_MAG_8;
#else
            if (VNU_out[mux_idx][i] > EDGE_MAG_7)       VNU_out[mux_idx][i] = EDGE_MAG_7;
            else if (VNU_out[mux_idx][i] < -EDGE_MAG_7) VNU_out[mux_idx][i] = -EDGE_MAG_7;
#endif
#if defined (__LOG_VNU_IN_OUT__)
            m_log_VNU_out[mux_idx][bit_pos] = VNU_out[mux_idx][i];
#endif
        }
    }
}
#if defined (__ECC_TV__)
if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
    if ((jj >= m_PCM->N_b - m_PCM->M_b) && (jj < m_PCM->N_b)) {
        for (i = 0; i < m_PCM->z_sb; i++) {
            bit_pos = idx_offset + i;
            tv_llr_out[bit_pos] = 5;
        }
    }
    else {
        for (i = 0; i < m_PCM->z_sb; i++) {
            bit_pos = idx_offset + i;
            if (Variable_mem[bit_pos] == 0)
                tv_llr_out[bit_pos] = 5;
            else
                tv_llr_out[bit_pos] = -5;
        }
    }
}
else if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
    for (ii = 0; ii < m_PCM->ColW[jj]; ii++) {
        for (i = 0; i < m_PCM->z_sb; i++) {
            /* C2V output으로 C2V module에서 출력해야 하나 연산을 skip한 관계로 이 함수에서 값을 clear 함 */
            //tv_vtc_inp[ii][4 * (m_PCM->z_sb * jj) + i] = 0;    // sign
            //tv_vtc_inp[ii][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (i * 3)] = 1; // mag MSB
            //tv_vtc_inp[ii][4 * (m_PCM->z_sb * jj) + m_PCM->z_sb + (i * 3) + 1] = 1; // mag CSB
            tv_vtc_inp[ii][(3 * m_PCM->z_sb * jj) + 1] = 0; // sign
            tv_vtc_inp[ii][(3 * m_PCM->z_sb * jj) + m_PCM->z_sb + (i * 2)] = 0; // mag MSB
            tv_vtc_inp[ii][(3 * m_PCM->z_sb * jj) + m_PCM->z_sb + (i * 2) + 1] = 0; // mag LSB
        }
    }
    for (i = 0; i < m_PCM->z_sb; i++) {
        bit_pos = idx_offset + i;
        tv_llr_out[bit_pos] = Soft_LLR[bit_pos];
    }
}
#endif
    /* make hard decision */
    if (G_idx == 1) {
        for (i = 0; i < m_PCM->z_sb; i++) {
            bit_pos = idx_offset + i;
            if (Variable_mem[bit_pos] == 0) cwc[bit_pos] = 0;
            else                            cwc[bit_pos] = 1;
            /* 예외처리 2021.08.05 WIKI 참고*/
            if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start1) && (bit_pos < m_ecc_info->bit_pos.info_punc_end1)) {
                //cwc[bit_pos] = 1;
                if (Variable_mem[bit_pos] == 0) cwc[bit_pos] = 0;
                else                            cwc[bit_pos] = 1;
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start2) && (bit_pos < m_ecc_info->bit_pos.info_punc_end2)) {
                //cwc[bit_pos] = 1;
                if (Variable_mem[bit_pos] == 0) cwc[bit_pos] = 0;
                else                            cwc[bit_pos] = 1;
            }
            else if ((bit_pos >= m_ecc_info->bit_pos.parity_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_punc_end)) {
                cwc[bit_pos] = 1;
            }
        }
    }
}
//================================================
// Calculate V2C (VNU_out) for HD
// v_deg : degree of VN
// idx_offset : start index of column block
//================================================
void Decoder::VN_Cal_HD(int v_deg, int idx_offset, int iter)
{
    int ii, j;
    int sum_t, temp, temp_nq;
    int temp_m;
    int channel_llr = 0;
    int col_idx = idx_offset / m_PCM->z_sb;
    int ch1, ch2, ch3, ch4;
    int th1, th2, th3, th4, th5, th6, th7;
    int bTable;
    int bit_pos;
    int mux_idx;
#if defined(__AUTO_LLR_OPT__)
    Get_VNU_LLR_SET_FILE(v_deg, col_idx, cur_set_idx, &ch1, &ch2, &ch3, &ch4, &th1, &th2, &th3, &th4, &th5, &th6, &th7);
#else
    Get_VNU_Ch_LLR_Adaptive(v_deg, col_idx, cur_set_idx, &ch1, &ch2, &ch3, &ch4);
    Get_VNU_Th_Adaptive(v_deg, col_idx, cur_set_idx, &th1, &th2, &th3, &th4, &th5, &th6, &th7);
#endif
    for (j = 0; j < m_PCM->z_sb; j++) {
        bit_pos = idx_offset + j;
        sum_t = 0;
        bTable = FALSE;
        if ((bit_pos >= m_ecc_info->bit_pos.info_sh_start) && (bit_pos < m_ecc_info->bit_pos.info_sh_end)) {
            /* shortening */
            channel_llr = CH_LLR_MAX;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start1) && (bit_pos < m_ecc_info->bit_pos.info_punc_end1)) {
            /* puncturing (info part) */
            channel_llr = CH_LLR_MIN;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start2) && (bit_pos < m_ecc_info->bit_pos.info_punc_end2)) {
            /* puncturing (info part) */
            channel_llr = CH_LLR_MIN;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.info_no_punc_end)) {
            bTable = TRUE;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.parity_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_no_punc_end)) {
            bTable = TRUE;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.parity_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_punc_end)) {
            /* puncturing (parity part) */
            channel_llr = CH_LLR_MIN;
        }
        if (TRUE == bTable) {
            if ((MODE_STOPPING_CRITERIA_ITER == m_param_dec->stopping_criteria) || ((MODE_STOPPING_CRITERIA_CYCLE == m_param_dec->stopping_criteria) && (Force_stopping < POWER_STOPPING_DELAY))) {
                channel_llr = ch1;
            }
            else {
                /* Power stopping algorithm (Part 2) */
                channel_llr = CH_LLR_MAX;
            }
        }
        sum_t = channel_llr;
#if defined (__ECC_TV__)
        if (Variable_mem[bit_pos] == 0) tv_llr_out[bit_pos] = sum_t;
        else                            tv_llr_out[bit_pos] = -sum_t;
        /*
        if (bit_pos >= m_PCM->N - m_PCM->M && bit_pos < m_PCM->N) {
            tv_llr_out[bit_pos] = sum_t;
        }
        else {
            if (Variable_mem[bit_pos] == 0) tv_llr_out[bit_pos] = sum_t;
            else                            tv_llr_out[bit_pos] = -sum_t;
        }*/
#endif
        for (ii = 0; ii < v_deg; ii++) {
            mux_idx = m_PCM->Mux_idx[ii][col_idx];
            sum_t = sum_t + VNU_in[mux_idx][j];
        }
        /* syndrome-aided decoding */
        if (sum_t > 0)  cwc[bit_pos] = Variable_mem[bit_pos];
        else            cwc[bit_pos] = (Variable_mem[bit_pos] + 1) % 2;
#if defined (__LOG_VNU_IN_OUT__)
        m_log_ch_llr[bit_pos] = channel_llr;
        m_log_sum_t[bit_pos] = sum_t;
#endif
        for (ii = 0; ii < v_deg; ii++) {
            mux_idx = m_PCM->Mux_idx[ii][col_idx];
            temp = sum_t - VNU_in[mux_idx][j];
            temp_m = abs(temp);
            temp_nq = temp;
#ifdef __AUTO_LLR_OPT__
            if ((TRUE == flag_BF_on) && (iter <= 4) && (v_deg > DV_5)) { //1bit precision
#else
            if ((TRUE == flag_BF_on) && (iter <= ITER_MAX_HBF) && (v_deg > DV_5)) { //1bit precision
#endif
                /* Zero V-out */
                if (temp_m == 0) {
#if defined (__4_BIT_LLR__)
                    if (VNU_in[mux_idx][j] > 0) temp = EDGE_MAG_8;
                    else                        temp = -EDGE_MAG_8;
#else
                    if (VNU_in[mux_idx][j] > 0) temp = EDGE_MAG_7;
                    else                        temp = -EDGE_MAG_7;
#endif
                }
                else {
#if defined (__4_BIT_LLR__)
                    temp_m = EDGE_MAG_8;
#else
                    temp_m = EDGE_MAG_7;
#endif
                    if (temp > 0)       temp = temp_m;
                    else                temp = -temp_m;
                }
            }
            else {  // 4bit precision
                /* Zero V-out */
                if (temp_m == 0) {
#if defined (__4_BIT_LLR__)
                    if      (temp_m >= th1)      temp_m = EDGE_MAG_8;
                    else if (temp_m >= th2)      temp_m = EDGE_MAG_7;
                    else if (temp_m >= th3)      temp_m = EDGE_MAG_6;
                    else if (temp_m >= th4)      temp_m = EDGE_MAG_5;
                    else if (temp_m >= th5)      temp_m = EDGE_MAG_4;
                    else if (temp_m >= th6)      temp_m = EDGE_MAG_3;
                    else if (temp_m >= th7)      temp_m = EDGE_MAG_2;
                    else                         temp_m = EDGE_MAG_1;
#else
                    if      (temp_m >= th1)      temp_m = EDGE_MAG_7;
                    else if (temp_m >= th2)      temp_m = EDGE_MAG_5;
                    else if (temp_m >= th3)      temp_m = EDGE_MAG_3;
                    else      temp_m = EDGE_MAG_1;
#endif
                    if (VNU_in[mux_idx][j] > 0) temp = temp_m;
                    else                        temp = -temp_m;
                }
                else {
#if defined (__4_BIT_LLR__)
                    if      (temp_m >= th1)      temp_m = EDGE_MAG_8;
                    else if (temp_m >= th2)      temp_m = EDGE_MAG_7;
                    else if (temp_m >= th3)      temp_m = EDGE_MAG_6;
                    else if (temp_m >= th4)      temp_m = EDGE_MAG_5;
                    else if (temp_m >= th5)      temp_m = EDGE_MAG_4;
                    else if (temp_m >= th6)      temp_m = EDGE_MAG_3;
                    else if (temp_m >= th7)      temp_m = EDGE_MAG_2;
                    else                         temp_m = EDGE_MAG_1;
#else
                    if      (temp_m >= th1)      temp_m = EDGE_MAG_7;
                    else if (temp_m >= th2)      temp_m = EDGE_MAG_5;
                    else if (temp_m >= th3)      temp_m = EDGE_MAG_3;
                    else                         temp_m = EDGE_MAG_1;
#endif
                    if (temp > 0)       temp = temp_m;
                    else                temp = -temp_m;
                }
            }
            VNU_out[mux_idx][j] = temp;
            VNU_out_nq[mux_idx][j] = temp_nq;
#if defined (__LOG_VNU_IN_OUT__)
            m_log_VNU_in[mux_idx][bit_pos] = VNU_in[mux_idx][j];
            m_log_VNU_out[mux_idx][bit_pos] = VNU_out[mux_idx][j];
#endif
        }// end for loop (i)
    }// end for loop (j)
    }
//================================================
// Half Column Update용
// Calculate V2C (VNU_out) for HD
// v_deg : degree of VN
// idx_offset : start index of column block
//================================================
void Decoder::VN_Cal_HD_HCU(int v_deg, int idx_offset, int G_idx, int iter)
{
    int ii, j;
    int sum_t, temp, temp_nq;
    int sum_t_old_temp;
    int temp_m;
    int channel_llr = 0;
    int col_idx = idx_offset / m_PCM->z_sb;
    int ch1, ch2, ch3, ch4;
    int th1, th2, th3, th4, th5, th6, th7;
    int bTable;
    int bit_pos;
    int mux_idx;
    int separate_v_deg;
    if (col_idx == HCU_start) {
        separate_v_deg = SEPARATE_V_DEG_1;
    }
    else if (col_idx == HCU_end) {
        separate_v_deg = SEPARATE_V_DEG_2;
    }
    int current_G_idx;
    current_G_idx = (G_idx + iter) % 2;
    int start_deg = 0;
    int end_deg = 0;
#if defined(__AUTO_LLR_OPT__)
    Get_VNU_LLR_SET_FILE(v_deg, col_idx, cur_set_idx, &ch1, &ch2, &ch3, &ch4, &th1, &th2, &th3, &th4, &th5, &th6, &th7);
#else
    Get_VNU_Ch_LLR_Adaptive(v_deg, col_idx, cur_set_idx, &ch1, &ch2, &ch3, &ch4);
    Get_VNU_Th_Adaptive(v_deg, col_idx, cur_set_idx, &th1, &th2, &th3, &th4, &th5, &th6, &th7);
#endif
    for (j = 0; j < m_PCM->z_sb; j++) {
        bit_pos = idx_offset + j;
        sum_t = 0;
        bTable = FALSE;
        if ((bit_pos >= m_ecc_info->bit_pos.info_sh_start) && (bit_pos < m_ecc_info->bit_pos.info_sh_end)) {
            /* shortening */
            channel_llr = CH_LLR_MAX;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start1) && (bit_pos < m_ecc_info->bit_pos.info_punc_end1)) {
            /* puncturing (info part) */
            channel_llr = CH_LLR_MIN;
            /*
            if (bit_pos < m_PCM->z_sb) {
                if (abs(m_PCM->punct_vote[0][j]) >= PR_MAJORITY_MAG) channel_llr = 10;
            }
            else {
                if (abs(m_PCM->punct_vote[1][j]) >= PR_MAJORITY_MAG) channel_llr = 10;
            }*/
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start2) && (bit_pos < m_ecc_info->bit_pos.info_punc_end2)) {
            /* puncturing (info part) */
            channel_llr = CH_LLR_MIN;
            /*
            if (bit_pos < m_PCM->z_sb) {
                if (abs(m_PCM->punct_vote[0][j]) >= PR_MAJORITY_MAG) channel_llr = 10;
            }
            else {
                if (abs(m_PCM->punct_vote[1][j]) >= PR_MAJORITY_MAG) channel_llr = 10;
            }*/
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.info_no_punc_end)) {
            bTable = TRUE;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.parity_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_no_punc_end)) {
            bTable = TRUE;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.parity_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_punc_end)) {
            /* puncturing (parity part) */
            channel_llr = CH_LLR_MIN;
        }
        if (TRUE == bTable) {
            if ((MODE_STOPPING_CRITERIA_ITER == m_param_dec->stopping_criteria) || ((MODE_STOPPING_CRITERIA_CYCLE == m_param_dec->stopping_criteria) && (Force_stopping < POWER_STOPPING_DELAY))) {
                channel_llr = ch1;
            }
            else {
                /* Power stopping algorithm (Part 2) */
                channel_llr = CH_LLR_MAX;
            }
        }
        sum_t = channel_llr;
#if defined (__ECC_TV__)
        if (Variable_mem[bit_pos] == 0) tv_llr_out[bit_pos] = sum_t;
        else                            tv_llr_out[bit_pos] = -sum_t;
        /*
        if (bit_pos >= m_PCM->N - m_PCM->M && bit_pos < m_PCM->N) {
            tv_llr_out[bit_pos] = sum_t;
        }
        else {
            if (Variable_mem[bit_pos] == 0) tv_llr_out[bit_pos] = sum_t;
            else                         tv_llr_out[bit_pos] = -sum_t;
        */
#endif
        if (current_G_idx == 0) {
            sum_t_old_temp = 0;
            //for (ii = 0; ii < v_deg / 2; ii++) {
            for (ii = 0; ii < separate_v_deg; ii++) {
                mux_idx = m_PCM->Mux_idx[ii][col_idx];
                sum_t_old_temp = sum_t_old_temp + VNU_in[mux_idx][j];
            }
            Sum_t_OLD_G0[col_idx - (HCU_start)][j] = sum_t_old_temp;
            sum_t = sum_t + Sum_t_OLD_G0[col_idx - (HCU_start)][j];
            sum_t = sum_t + Sum_t_OLD_G1[col_idx - (HCU_start)][j];
        }
        else if (current_G_idx == 1) {
            sum_t_old_temp = 0;
            //for (ii = v_deg / 2; ii < v_deg; ii++) {
            for (ii = separate_v_deg; ii < v_deg; ii++) {
                mux_idx = m_PCM->Mux_idx[ii][col_idx];
                sum_t_old_temp = sum_t_old_temp + VNU_in[mux_idx][j];
            }
            Sum_t_OLD_G1[col_idx - (HCU_start)][j] = sum_t_old_temp;
            sum_t = sum_t + Sum_t_OLD_G1[col_idx - (HCU_start)][j];
            sum_t = sum_t + Sum_t_OLD_G0[col_idx - (HCU_start)][j];
        }
        //printf("[ITER: %d col_blk: %d  G_idx: %d][%d] channel_LLR=%d, Sum_t_OLD_G0=%d,Sum_t_OLD_G1=%d\n", iter, col_idx, current_G_idx, j, channel_llr, Sum_t_OLD_G0[col_idx][j], Sum_t_OLD_G1[col_idx][j]);
        if (G_idx == 1) {
            /* syndrome-aided decoding */
            if (sum_t > 0)  cwc[bit_pos] = Variable_mem[bit_pos];
            else            cwc[bit_pos] = (Variable_mem[bit_pos] + 1) % 2;
        }
#if defined (__LOG_VNU_IN_OUT__)
        m_log_ch_llr[bit_pos] = channel_llr;
        m_log_sum_t[bit_pos] = sum_t;
#endif
        //printf("[bit_pos=%d, iter=%d] sum_t_G0=%d, sum_t_G1=%d\n", bit_pos, iter,sum_t_G0, sum_t_G1);
        if (current_G_idx == 0) {
            //start_deg = 0; end_deg = v_deg / 2;
            start_deg = 0; end_deg = separate_v_deg;
        }
        else if (current_G_idx == 1) {
            //start_deg = v_deg / 2; end_deg = v_deg;
            start_deg = separate_v_deg; end_deg = v_deg;
        }
        for (ii = start_deg; ii < end_deg; ii++) {
            mux_idx = m_PCM->Mux_idx[ii][col_idx];
            temp = sum_t - VNU_in[mux_idx][j];
            temp_m = abs(temp);
            temp_nq = temp;
#ifdef __AUTO_LLR_OPT__
            if ((TRUE == flag_BF_on) && (iter <= 4) && (v_deg > DV_5)) { //1bit precision
#else
            if ((TRUE == flag_BF_on) && (iter <= ITER_MAX_HBF) && (v_deg > DV_5)) { //1bit precision
#endif
                /* Zero V-out */
                if (temp_m == 0) {
#if defined (__4_BIT_LLR__)
                    if (VNU_in[mux_idx][j] > 0) temp = EDGE_MAG_8;
                    else                        temp = -EDGE_MAG_8;
#else
                    if (VNU_in[mux_idx][j] > 0) temp = EDGE_MAG_7;
                    else                        temp = -EDGE_MAG_7;
#endif
                }
                else {
#if defined (__4_BIT_LLR__)
                    temp_m = EDGE_MAG_8;
#else
                    temp_m = EDGE_MAG_7;
#endif
                    if (temp > 0)       temp = temp_m;
                    else                temp = -temp_m;
                }
            }
            else {  // 4bit precision
                /* Zero V-out */
                if (temp_m == 0) {
#if defined (__4_BIT_LLR__)
                    if      (temp_m >= th1)      temp_m = EDGE_MAG_8;
                    else if (temp_m >= th2)      temp_m = EDGE_MAG_7;
                    else if (temp_m >= th3)      temp_m = EDGE_MAG_6;
                    else if (temp_m >= th4)      temp_m = EDGE_MAG_5;
                    else if (temp_m >= th5)      temp_m = EDGE_MAG_4;
                    else if (temp_m >= th6)      temp_m = EDGE_MAG_3;
                    else if (temp_m >= th7)      temp_m = EDGE_MAG_2;
                    else                         temp_m = EDGE_MAG_1;
#else
                    if      (temp_m >= th1)      temp_m = EDGE_MAG_7;
                    else if (temp_m >= th2)      temp_m = EDGE_MAG_5;
                    else if (temp_m >= th3)      temp_m = EDGE_MAG_3;
                    else                         temp_m = EDGE_MAG_1;
#endif
                    if (VNU_in[mux_idx][j] > 0) temp = temp_m;
                    else                        temp = -temp_m;
                }
                else {
#if defined (__4_BIT_LLR__)
                    if      (temp_m >= th1)      temp_m = EDGE_MAG_8;
                    else if (temp_m >= th2)      temp_m = EDGE_MAG_7;
                    else if (temp_m >= th3)      temp_m = EDGE_MAG_6;
                    else if (temp_m >= th4)      temp_m = EDGE_MAG_5;
                    else if (temp_m >= th5)      temp_m = EDGE_MAG_4;
                    else if (temp_m >= th6)      temp_m = EDGE_MAG_3;
                    else if (temp_m >= th7)      temp_m = EDGE_MAG_2;
                    else                         temp_m = EDGE_MAG_1;
#else
                    if      (temp_m >= th1)      temp_m = EDGE_MAG_7;
                    else if (temp_m >= th2)      temp_m = EDGE_MAG_5;
                    else if (temp_m >= th3)      temp_m = EDGE_MAG_3;
                    else                         temp_m = EDGE_MAG_1;
#endif
                    if(temp>0) temp = temp_m;
                    else temp = -temp_m;
                }
            }
            VNU_out[mux_idx][j] = temp;
            VNU_out_nq[mux_idx][j] = temp_nq;
#if defined (__LOG_VNU_IN_OUT__)
            m_log_VNU_in[mux_idx][bit_pos] = VNU_in[mux_idx][j];
            m_log_VNU_out[mux_idx][bit_pos] = VNU_out[mux_idx][j];
#endif
        }// end for loop (ii)
    }// end for loop (j)
    }
//================================================
// Calculate V2C (VNU_out) for 1.5SD
// v_deg : degree of VN
// idx_offset : start index of column block
//================================================
void Decoder::VN_Cal_CD(int v_deg, int idx_offset, int iter)
{
    int ii, j;
    int sum_t, temp;
    int temp_m;
    int channel_llr = 0;
    int col_idx = idx_offset / m_PCM->z_sb;
    int ch1, ch2, ch3, ch4;
    int th1, th2, th3, th4, th5, th6, th7;
    int bTable;
    int bit_pos;
    int mux_idx;
#if defined(__AUTO_LLR_OPT__)
    Get_VNU_LLR_SET_FILE(v_deg, col_idx, cur_set_idx, &ch1, &ch2, &ch3, &ch4, &th1, &th2, &th3, &th4, &th5, &th6, &th7);
#else
    Get_VNU_Ch_LLR_Adaptive(v_deg, col_idx, cur_set_idx, &ch1, &ch2, &ch3, &ch4);
    Get_VNU_Th_Adaptive(v_deg, col_idx, cur_set_idx, &th1, &th2, &th3, &th4, &th5, &th6, &th7);
#endif
    for (j = 0; j < m_PCM->z_sb; j++) {
        bit_pos = idx_offset + j;
        sum_t = 0;
        bTable = FALSE;
        if (CD[bit_pos] == 1) {
            /* erasure */
            channel_llr = CH_LLR_MIN;    // erasure
        }
        else {
        if ((bit_pos >= m_ecc_info->bit_pos.info_sh_start) && (bit_pos < m_ecc_info->bit_pos.info_sh_end)) {
            /* shortening */
            channel_llr = CH_LLR_MAX;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start1) && (bit_pos < m_ecc_info->bit_pos.info_punc_end1)) {
            /* puncturing (info part) */
            channel_llr = CH_LLR_MIN;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start2) && (bit_pos < m_ecc_info->bit_pos.info_punc_end2)) {
            /* puncturing (info part) */
            channel_llr = CH_LLR_MIN;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.info_no_punc_end)) {
            bTable = TRUE;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.parity_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_no_punc_end)) {
            bTable = TRUE;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.parity_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_punc_end)) {
            /* puncturing (parity part) */
            channel_llr = CH_LLR_MIN;
        }
        if (TRUE == bTable) {
            if ((MODE_STOPPING_CRITERIA_ITER == m_param_dec->stopping_criteria) || ((MODE_STOPPING_CRITERIA_CYCLE == m_param_dec->stopping_criteria) && (Force_stopping < POWER_STOPPING_DELAY))) {
                channel_llr = ch1;
            }
            else {
                /* Power stopping algorithm (Part 2) */
                channel_llr = CH_LLR_MAX;
            }
        }
        }
        sum_t = channel_llr;
#if defined (__ECC_TV__)
        if (Variable_mem[bit_pos] == 0) tv_llr_out[bit_pos] = sum_t;
        else                            tv_llr_out[bit_pos] = -sum_t;
        /*
        if (bit_pos >= m_PCM->N - m_PCM->M && bit_pos < m_PCM->N) {
            tv_llr_out[bit_pos] = sum_t;
        }
        else {
            if (Variable_mem[bit_pos] == 0) tv_llr_out[bit_pos] = sum_t;
            else                            tv_llr_out[bit_pos] = -sum_t;
        }*/
#endif
        for (ii = 0; ii < v_deg; ii++) {
            mux_idx = m_PCM->Mux_idx[ii][col_idx];
            sum_t = sum_t + VNU_in[mux_idx][j];
        }
        /* syndrome-aided decoding */
        if (sum_t > 0)  cwc[bit_pos] = Variable_mem[bit_pos];
        else            cwc[bit_pos] = (Variable_mem[bit_pos] + 1) % 2;
#if defined (__LOG_VNU_IN_OUT__)
        m_log_ch_llr[bit_pos] = channel_llr;
        m_log_sum_t[bit_pos] = sum_t;
#endif
        for (ii = 0; ii < v_deg; ii++) {
            mux_idx = m_PCM->Mux_idx[ii][col_idx];
	temp = sum_r - VNU_in[mux_idx][j];
	temp_m = abs(temp);
	/* Zero V-out */
	if (temp_m == 0) {
#if defined (__4_BIT_LLR__)
		if (temp_m >= th1)		temp_m = EDGE_MAG_8;
		else if (temp_m >= th2)		temp_m = EDGE_MAG_7;
		else if (temp_m >= th3)		temp_m = EDGE_MAG_6;
		else if (temp_m >= th4)		temp_m = EDGE_MAG_5;
		else if (temp_m >= th5)		temp_m = EDGE_MAG_4;
		else if (temp_m >= th6)		temp_m = EDGE_MAG_3;
		else if (temp_m >= th7)		temp_m = EDGE_MAG_2;
		else				temp_m = EDGE_MAG_1;
#else
		if (temp_m >= th1)		temp_m = EDGE_MAG_7;
		else if (temp_m >= th2)		temp_m = EDGE_MAG_5;
		else if (temp_m >= th3)		temp_m = EDGE_MAG_3;
		else				temp_m = EDGE_MAG_1;
#endif
		if (VNU_in[mux_idx][j] > 0) temp = temp_m;
		else				temp = -temp_m;
	}
	else {
#if defined (__4_BIT_LLR__)
		if (temp_m >= th1)		temp_m = EDGE_MAG_8;
		else if (temp_m >= th2)		temp_m = EDGE_MAG_7;
		else if (temp_m >= th3)		temp_m = EDGE_MAG_6;
		else if (temp_m >= th4)		temp_m = EDGE_MAG_5;
		else if (temp_m >= th5)		temp_m = EDGE_MAG_4;
		else if (temp_m >= th6)		temp_m = EDGE_MAG_3;
		else if (temp_m >= th7)		temp_m = EDGE_MAG_2;
		else				temp_m = EDGE_MAG_1;
#else
		if (temp_m >= th1)		temp_m = EDGE_MAG_7;
		else if (temp_m >= th2)		temp_m = EDGE_MAG_5;
		else if (temp_m >= th3)		temp_m = EDGE_MAG_3;
		else				temp_m = EDGE_MAG_1;
#endif
		if (temp > 0)			temp = temp_m;
		else				temp = -temp_m;
	}
	VNU_out[mux_idx][j] = temp;
#if defined (__LOG_VNU_IN_OUT__)
	m_log_VNU_in[mux_idx][bit_pos] = VNU_in[mux_idx][j];
	m_log_VNU_out[mux_idx][bit_pos] = VNU_out[mux_idx][j];
#endif
	}// end for loop (i)
	}// end for loop (j)
}
//================================================
// Calculate V2C (VNU_out) for 2SD and 3SD
// v_deg : degree of VN
// idx_offset : start index of column block
//================================================
void Decoder::VN_Cal_SD(int v_deg, int idx_offset, int iter)
{
    int ii, j, sum_t, temp, temp_nq;
    int temp_m;
    int channel_llr = 0;
    int col_idx = idx_offset / m_PCM->z_sb;
    int ch1, ch2, ch3, ch4;
    int th1, th2, th3, th4, th5, th6, th7;
    int mag;
    int bTable;
    int bit_pos;
    int mux_idx;
#if defined(__AUTO_LLR_OPT__)
    Get_VNU_LLR_SET_FILE(v_deg, col_idx, cur_set_idx, &ch1, &ch2, &ch3, &ch4, &th1, &th2, &th3, &th4, &th5, &th6, &th7);
#else
    Get_VNU_Ch_LLR_Adaptive(v_deg, col_idx, cur_set_idx, &ch1, &ch2, &ch3, &ch4);
    Get_VNU_Th_Adaptive(v_deg, col_idx, cur_set_idx, &th1, &th2, &th3, &th4, &th5, &th6, &th7);
#endif
    for (j = 0; j < m_PCM->z_sb; j++) {
        bit_pos = idx_offset + j;
        sum_t = 0;
        bTable = FALSE;
        if ((bit_pos >= m_ecc_info->bit_pos.info_sh_start) && (bit_pos < m_ecc_info->bit_pos.info_sh_end)) {
            /* shortening */
            channel_llr = CH_LLR_MAX;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start1) && (bit_pos < m_ecc_info->bit_pos.info_punc_end1)) {
            /* puncturing (info part) */
            channel_llr = CH_LLR_MIN;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start2) && (bit_pos < m_ecc_info->bit_pos.info_punc_end2)) {
            /* puncturing (info part) */
            channel_llr = CH_LLR_MIN;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.info_no_punc_end)) {
            bTable = TRUE;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.parity_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_no_punc_end)) {
            bTable = TRUE;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.parity_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_punc_end)) {
            /* puncturing (parity part) */
            channel_llr = CH_LLR_MIN;
        }
        if (TRUE == bTable) {
            if ((MODE_STOPPING_CRITERIA_ITER == m_param_dec->stopping_criteria) || ((MODE_STOPPING_CRITERIA_CYCLE == m_param_dec->stopping_criteria) && (Force_stopping < POWER_STOPPING_DELAY))) {
                mag = abs(Soft_LLR_PRIME[bit_pos]);
                if (MODE_DEC_2SD == m_param_dec->init_n) {
                    //if (mag >= EDGE_MAG_3) { channel_llr = ch1; }
                    if (mag > EDGE_MAG_3) { channel_llr = ch1; }
                    else { channel_llr = ch2; }
                }
                else if (MODE_DEC_3SD == m_param_dec->init_n) {
#if defined (__4_BIT_LLR__)
                    if (mag >= EDGE_MAG_7) { channel_llr = ch1; }
                    else if (mag == EDGE_MAG_5) { channel_llr = ch2; }
                    else if (mag == EDGE_MAG_3) { channel_llr = ch3; }
                    else { channel_llr = ch4; }
#else
                    if (mag == EDGE_MAG_7) { channel_llr = ch1; }
                    else if (mag == EDGE_MAG_5) { channel_llr = ch2; }
                    else if (mag == EDGE_MAG_3) { channel_llr = ch3; }
                    else { channel_llr = ch4; }
#endif
                }
            }
            else {
                /* Power stopping algorithm (Part 2) */
                channel_llr = CH_LLR_MAX;
            }
        }
        /* syndrome aided decoding */
        //sum_t = abs(channel_llr);
        sum_t = channel_llr;
#if defined (__ECC_TV__)
        if (Variable_mem[bit_pos] == 0) tv_llr_out[bit_pos] = sum_t;
        else                            tv_llr_out[bit_pos] = -sum_t;
        //printf("%d [bit_pos: %d] %d\n", mn, bit_pos, tv_llr_out[bit_pos]);
#endif
        for (ii = 0; ii < v_deg; ii++) {
            mux_idx = m_PCM->Mux_idx[ii][col_idx];
            sum_t = sum_t + VNU_in[mux_idx][j];
        }
        /* syndrome aided decoding */
        if (sum_t > 0)  cwc[bit_pos] = Variable_mem[bit_pos];
        else            cwc[bit_pos] = (Variable_mem[bit_pos] + 1) % 2;
        /*
        if (iter > 20) {
            if (bit_pos < m_ecc_info->bit_pos.info_punc_end) {
                if (Variable_mem[bit_pos] != cwc[bit_pos]) PR_bit_flip_cnt[bit_pos] += 1;
            }
        }
        }*/
#if defined (__LOG_VNU_IN_OUT__)
        m_log_ch_llr[bit_pos] = abs(channel_llr);
        m_log_sum_t[bit_pos] = sum_t;
#endif
        for (ii = 0; ii < v_deg; ii++) {
            mux_idx = m_PCM->Mux_idx[ii][col_idx];
            temp = sum_t - VNU_in[mux_idx][j];
            temp_m = abs(temp);
            temp_nq = temp;
            /* Zero V-out */
            if (temp_m == 0) {
#if defined (__4_BIT_LLR__)
                if (temp_m >= th1)          temp_m = EDGE_MAG_8;
                else if (temp_m >= th2)      temp_m = EDGE_MAG_7;
                else if (temp_m >= th3)      temp_m = EDGE_MAG_6;
                else if (temp_m >= th4)      temp_m = EDGE_MAG_5;
                else if (temp_m >= th5)      temp_m = EDGE_MAG_4;
                else if (temp_m >= th6)      temp_m = EDGE_MAG_3;
                else if (temp_m >= th7)      temp_m = EDGE_MAG_2;
                else                         temp_m = EDGE_MAG_1;
#else
                if (temp_m >= th1)            temp_m = EDGE_MAG_7;
                else if (temp_m >= th2)       temp_m = EDGE_MAG_5;
                else if (temp_m >= th3)       temp_m = EDGE_MAG_3;
                else                          temp_m = EDGE_MAG_1;
#endif
                if (VNU_in[mux_idx][j] > 0) temp = temp_m;
                else                         temp = -temp_m;
            }
            else {
#if defined (__4_BIT_LLR__)
                if (temp_m >= th1)           temp_m = EDGE_MAG_8;
                else if (temp_m >= th2)      temp_m = EDGE_MAG_7;
                else if (temp_m >= th3)      temp_m = EDGE_MAG_6;
                else if (temp_m >= th4)      temp_m = EDGE_MAG_5;
                else if (temp_m >= th5)      temp_m = EDGE_MAG_4;
                else if (temp_m >= th6)      temp_m = EDGE_MAG_3;
                else if (temp_m >= th7)      temp_m = EDGE_MAG_2;
                else                         temp_m = EDGE_MAG_1;
#else
                if (temp_m >= th1)            temp_m = EDGE_MAG_7;
                else if (temp_m >= th2)       temp_m = EDGE_MAG_5;
                else if (temp_m >= th3)       temp_m = EDGE_MAG_3;
                else                          temp_m = EDGE_MAG_1;
#endif
                if (temp > 0)                 temp = temp_m;
                else                          temp = -temp_m;
            }
            VNU_out[mux_idx][j] = temp;
            VNU_out_nq[mux_idx][j] = temp_nq;
#if defined (__LOG_VNU_IN_OUT__)
            m_log_VNU_in[mux_idx][bit_pos] = VNU_in[mux_idx][j];
            m_log_VNU_out[mux_idx][bit_pos] = VNU_out[mux_idx][j];
#endif
        }
    }
}
//==============================================
// Half Column Update 용
// Calculate V2C (VNU_out) for 2SD and 3SD
// v_deg : degree of VN
// idx_offset : start index of column block
//==============================================
void Decoder::VN_Cal_SD_HCU(int v_deg, int idx_offset, int G_idx, int iter)
{
    int ii, j, sum_t, temp, temp_nq;
    int sum_t_old_temp;
    int temp_m;
    int channel_llr = 0;
    int col_idx = idx_offset / m_PCM->z_sb;
    int ch1, ch2, ch3, ch4;
    int th1, th2, th3, th4, th5, th6, th7;
    int mag;
    int bTable;
    int bit_pos;
    int mux_idx;
    int separate_v_deg = 0;
    if (col_idx == HCU_start) {
        separate_v_deg = SEPARATE_V_DEG_1;
    }
    else if (col_idx == HCU_end) {
        separate_v_deg = SEPARATE_V_DEG_2;
    }
    int current_G_idx;
    current_G_idx = (G_idx + iter) % 2;
    int start_deg = 0;
    int end_deg = 0;
#if defined(__AUTO_LLR_OPT__)
    Get_VNU_LLR_SET_FILE(v_deg, col_idx, cur_set_idx, &ch1, &ch2, &ch3, &ch4, &th1, &th2, &th3, &th4, &th5, &th6, &th7);
#else
    Get_VNU_Ch_LLR_Adaptive(v_deg, col_idx, cur_set_idx, &ch1, &ch2, &ch3, &ch4);
    Get_VNU_Th_Adaptive(v_deg, col_idx, cur_set_idx, &th1, &th2, &th3, &th4, &th5, &th6, &th7);
#endif
    //th1 = th1 + 5;
    //th2 = th2 + 5;
    //th3 = th3 + 2;
    for (j = 0; j < m_PCM->z_sb; j++) {
        bit_pos = idx_offset + j;
        sum_t = 0;
        bTable = FALSE;
        if ((bit_pos >= m_ecc_info->bit_pos.info_sh_start) && (bit_pos < m_ecc_info->bit_pos.info_sh_end)) {
            /* shortening */
            channel_llr = CH_LLR_MAX;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start1) && (bit_pos < m_ecc_info->bit_pos.info_punc_end1)) {
            /* puncturing (info part) */
            //mag값 인가
            channel_llr = CH_LLR_MIN;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_punc_start2) && (bit_pos < m_ecc_info->bit_pos.info_punc_end2)) {
            /* puncturing (info part) */
            //mag값 인가
            channel_llr = CH_LLR_MIN;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.info_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.info_no_punc_end)) {
            bTable = TRUE;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.parity_no_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_no_punc_end)) {
            bTable = TRUE;
        }
        else if ((bit_pos >= m_ecc_info->bit_pos.parity_punc_start) && (bit_pos < m_ecc_info->bit_pos.parity_punc_end)) {
            /* puncturing (parity part) */
            channel_llr = CH_LLR_MIN;
        }
        if (TRUE == bTable) {
            if ((MODE_STOPPING_CRITERIA_ITER == m_param_dec->stopping_criteria) || ((MODE_STOPPING_CRITERIA_CYCLE == m_param_dec->stopping_criteria) && (Force_stopping < POWER_STOPPING_DELAY))) {
                mag = abs(Soft_LLR_PRIME[bit_pos]);
                if (MODE_DEC_2SD == m_param_dec->init_n) {
                    //if (mag >= EDGE_MAG_3) { channel_llr = ch1; }
                    if (mag > EDGE_MAG_3) { channel_llr = ch1; }
                    else { channel_llr = ch2; }
                }
                else if (MODE_DEC_3SD == m_param_dec->init_n) {
#if defined (__4_BIT_LLR__)
                    if (mag == EDGE_MAG_7) { channel_llr = ch1; }
                    else if (mag == EDGE_MAG_5) { channel_llr = ch2; }
                    else if (mag == EDGE_MAG_3) { channel_llr = ch3; }
                    else { channel_llr = ch4; }
#else
                    if (mag == EDGE_MAG_7) { channel_llr = ch1; }
                    else if (mag == EDGE_MAG_5) { channel_llr = ch2; }
                    else if (mag == EDGE_MAG_3) { channel_llr = ch3; }
                    else { channel_llr = ch4; }
#endif
                }
            }
            else {
                /* Power stopping algorithm (Part 2) */
                channel_llr = CH_LLR_MAX;
            }
        }
        /* syndrome aided decoding */
        //sum_t = abs(channel_llr);
        sum_t = channel_llr;
#if defined (__ECC_TV__)
        if (Variable_mem[bit_pos] == 0) tv_llr_out[bit_pos] = sum_t;
        else                            tv_llr_out[bit_pos] = -sum_t;
#endif
        if (current_G_idx == 0) {
            sum_t_old_temp = 0;
            //for (ii = 0; ii < v_deg / 2; ii++) {
            for (ii = 0; ii < separate_v_deg; ii++) {
                mux_idx = m_PCM->Mux_idx[ii][col_idx];
                sum_t_old_temp = sum_t_old_temp + VNU_in[mux_idx][j];
            }
            Sum_t_OLD_G0[col_idx - (HCU_start)][j] = sum_t_old_temp;
            sum_t = sum_t + Sum_t_OLD_G0[col_idx - (HCU_start)][j];
            sum_t = sum_t + Sum_t_OLD_G1[col_idx - (HCU_start)][j];
        }
        else if (current_G_idx == 1) {
            sum_t_old_temp = 0;
            //for (ii = v_deg / 2; ii < v_deg; ii++) {
            for (ii = separate_v_deg; ii < v_deg; ii++) {
                mux_idx = m_PCM->Mux_idx[ii][col_idx];
                sum_t_old_temp = sum_t_old_temp + VNU_in[mux_idx][j];
            }
            Sum_t_OLD_G1[col_idx - (HCU_start)][j] = sum_t_old_temp;
            sum_t = sum_t + Sum_t_OLD_G1[col_idx - (HCU_start)][j];
            sum_t = sum_t + Sum_t_OLD_G0[col_idx - (HCU_start)][j];
        }
        if (G_idx == 1) {
            /* syndrome aided decoding */
            if (sum_t > 0)  cwc[bit_pos] = Variable_mem[bit_pos];
            else            cwc[bit_pos] = (Variable_mem[bit_pos] + 1) % 2;
        }
#if defined (__LOG_VNU_IN_OUT__)
        m_log_ch_llr[bit_pos] = abs(channel_llr);
        m_log_sum_t[bit_pos] = sum_t;
#endif
        if (current_G_idx == 0) {
            //start_deg = 0; end_deg = v_deg / 2;
            start_deg = 0; end_deg = separate_v_deg;
        }
        else if (current_G_idx == 1) {
            //start_deg = v_deg / 2; end_deg = v_deg;
            start_deg = separate_v_deg; end_deg = v_deg;
        }
        for (ii = start_deg; ii < end_deg; ii++) {
            mux_idx = m_PCM->Mux_idx[ii][col_idx];
            temp = sum_t - VNU_in[mux_idx][j];
            temp_m = abs(temp);
            temp_nq = temp;
            /* Zero V-out */
            if (temp_m == 0) {
#if defined (__4_BIT_LLR__)
                if (temp_m >= th1)          temp_m = EDGE_MAG_8;
                else if (temp_m >= th2)      temp_m = EDGE_MAG_7;
                else if (temp_m >= th3)      temp_m = EDGE_MAG_6;
                else if (temp_m >= th4)      temp_m = EDGE_MAG_5;
                else if (temp_m >= th5)      temp_m = EDGE_MAG_4;
                else if (temp_m >= th6)      temp_m = EDGE_MAG_3;
                else if (temp_m >= th7)      temp_m = EDGE_MAG_2;
                else                         temp_m = EDGE_MAG_1;
#else
                if (temp_m >= th1)            temp_m = EDGE_MAG_7;
                else if (temp_m >= th2)       temp_m = EDGE_MAG_5;
                else if (temp_m >= th3)       temp_m = EDGE_MAG_3;
                else                          temp_m = EDGE_MAG_1;
#endif
                if (VNU_in[mux_idx][j] > 0) temp = temp_m;
                else                         temp = -temp_m;
            }
            else {
#if defined (__4_BIT_LLR__)
                if (temp_m >= th1)           temp_m = EDGE_MAG_8;
                else if (temp_m >= th2)      temp_m = EDGE_MAG_7;
                else if (temp_m >= th3)      temp_m = EDGE_MAG_6;
                else if (temp_m >= th4)      temp_m = EDGE_MAG_5;
                else if (temp_m >= th5)      temp_m = EDGE_MAG_4;
                else if (temp_m >= th6)      temp_m = EDGE_MAG_3;
                else if (temp_m >= th7)      temp_m = EDGE_MAG_2;
                else                         temp_m = EDGE_MAG_1;
#else
                if (temp_m >= th1)            temp_m = EDGE_MAG_7;
                else if (temp_m >= th2)       temp_m = EDGE_MAG_5;
                else if (temp_m >= th3)       temp_m = EDGE_MAG_3;
                else                          temp_m = EDGE_MAG_1;
#endif
                if (temp > 0)                 temp = temp_m;
                else                          temp = -temp_m;
            }
            VNU_out[mux_idx][j] = temp;
            VNU_out_nq[mux_idx][j] = temp_nq;
#if defined (__LOG_VNU_IN_OUT__)
            m_log_VNU_in[mux_idx][bit_pos] = VNU_in[mux_idx][j];
            m_log_VNU_out[mux_idx][bit_pos] = VNU_out[mux_idx][j];
#endif
        }
    }
}
//==============================================
// Get 3SD LLR
//==============================================
int Decoder::Mapper_3bit_SD(int hd, int sd, int cc, int m1, int m2, int m3, int m4)
{
    int llr = 0;
    if (sd == 1 && cc == 1)
        llr = m1;    // very strong
    else if (sd == 1 && cc == 0)
        llr = m2;    // normal strong
    else if (sd == 0 && cc == 0)
        llr = m3;    // normal weak
    else if (sd == 0 && cc == 1)
        llr = m4;    // very weak
    if (hd == 1)
        llr = -llr;
    return llr;
}
int Decoder::Mapper_3bit_SD_weak_degree(int hd, int sd, int cc, int m1, int m2, int m3, int m4)
{
    int llr = 0;
    if (sd == 1 && cc == 1)
        llr = 3;     // very strong
    else if (sd == 1 && cc == 0)
        llr = 2;     // normal strong
    else if (sd == 0 && cc == 0)
        llr = 1;     // normal weak
    else if (sd == 0 && cc == 1)
        llr = 0;     // very weak
    return llr;
}
//==============================================
// Get 2SD LLR
//==============================================
int Decoder::Mapper_2bit_SD(int hd, int sd, int m1, int m2)
{
    int llr = 0;
    if (sd == 1)
        llr = m1;    // strong
    else if (sd == 0)
        llr = m2;    // weak
    if (hd == 1)
        llr = -llr;
    return llr;
}
//==============================================
// Make LLR values (invert HD, make erasure)
//==============================================
void Decoder::Make_LLR(int* hd_input, int* sd_input, int* cc_input, int* cd_input)
{
    int n;
    int inv_hd = 0;
    int sd;
    int cc;
    if (MODE_DEC_2SD == m_param_dec->init_n) {
        for (n = 0; n < m_PCM->N; n++) {
            if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
                inv_hd = (hd_input[n] + 1) % 2;
            }
            else if (MODE_ALL_ZERO_CODEWORD == m_ecc_info->mode_all_one_cw) {
                inv_hd = hd_input[n];
            }
            sd = sd_input[n];
            //Soft_LLR[n] = Mapper_2bit_SD(inv_hd, sd, EDGE_MAG_8, EDGE_MAG_1);
            //Soft_LLR_PRIME[n] = Mapper_2bit_SD(inv_hd, sd, EDGE_MAG_8, EDGE_MAG_1);    // PRIME 추기
#if defined (__4_BIT_LLR__)
            Soft_LLR[n] = Mapper_2bit_SD(inv_hd, sd, EDGE_MAG_7, EDGE_MAG_3);
            Soft_LLR_PRIME[n] = Mapper_2bit_SD(inv_hd, sd, EDGE_MAG_7, EDGE_MAG_3); // PRIME 추기
#else
            Soft_LLR[n] = Mapper_2bit_SD(inv_hd, sd, EDGE_MAG_5, EDGE_MAG_1);
            Soft_LLR_PRIME[n] = Mapper_2bit_SD(inv_hd, sd, EDGE_MAG_5, EDGE_MAG_1); // PRIME 추기
#endif
        }
    }
    else if (MODE_DEC_3SD == m_param_dec->init_n) {
        for (n = 0; n < m_PCM->N; n++) {
            if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
                inv_hd = (hd_input[n] + 1) % 2;
            }
            else if (MODE_ALL_ZERO_CODEWORD == m_ecc_info->mode_all_one_cw) {
                inv_hd = hd_input[n];
            }
            sd = sd_input[n];
            cc = cc_input[n];
#if defined (__4_BIT_LLR__)
            Soft_LLR[n] = Mapper_3bit_SD(inv_hd, sd, cc, EDGE_MAG_7, EDGE_MAG_5, EDGE_MAG_3, EDGE_MAG_1);
            Soft_LLR_PRIME[n] = Mapper_3bit_SD(inv_hd, sd, cc, EDGE_MAG_7, EDGE_MAG_5, EDGE_MAG_3, EDGE_MAG_1); // PRIME 추기
#else
            Soft_LLR[n] = Mapper_3bit_SD(inv_hd, sd, cc, EDGE_MAG_7, EDGE_MAG_5, EDGE_MAG_3, EDGE_MAG_1);
            Soft_LLR_weak_degree[n]=Mapper_3bit_SD_weak_degree(inv_hd, sd, cc, EDGE_MAG_7, EDGE_MAG_5, EDGE_MAG_3, EDGE_MAG_1);
            Soft_LLR_PRIME[n] = Mapper_3bit_SD(inv_hd, sd, cc, EDGE_MAG_7, EDGE_MAG_5, EDGE_MAG_3, EDGE_MAG_1); // PRIME 추기
#endif
        }
    }
    else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
        for (n = 0; n < m_PCM->N; n++) {
            CD[n] = (hd_input[n] + cd_input[n]) % 2;
        }
    }
}
//==============================================
// Compare with the original codeword
//==============================================
void Decoder::Check_Genie_CRC()
{
    int en = 0;
    failure_flag = FLAG_LOW;
    //for (int q = 0; q < m_PCM->N - m_PCM->M; q++) {
    for (int q = 0; q < m_PCM->N - m_PCM->M - 256; q++) {
        if (cwc[q] != m_genie_inv_cw[q]) {
            en++;
            failure_flag = FLAG_HIGH;
        }
    }
}
//==============================================
// Power stopping algorithm (part 3)
//==============================================
int Decoder::Jump_Iter(int* cur_iteration)
{
    int mn = *cur_iteration;
    jump_flag = FLAG_LOW;
    if (FLAG_HIGH == flag_dec_1iter) {
        if (FLAG_LOW == CRC_flag) {
            mn = MN;
        }
        else {
            mn = MN_old;
        }
        iter_num = mn;
        *cur_iteration = mn;    // update
#if defined (__ONLY_FOR_DEBUG__)
        cout << "flag_dec_1iter : 1,  mn : " << mn << endl;
#endif
        return TRUE;
    }
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) { // TLC 용 LLR set 선택 22.01.01 민기
        if (MODE_DEC_HD == m_param_dec->init_n) {
            if (Error_count_reg > m_param_dec->diverse_th) {
                jump_flag = FLAG_HIGH;
#if defined(__CORNER_CHECKER__)
                m_corner->Event_Flag(CornerChecker::IDX_FLAG_JUMP);
#endif
            }
            if (FLAG_HIGH == jump_flag) {
                Set_CSW(CSW_VALUE_JUMP);
            }
        }
        else if (MODE_DEC_2SD == m_param_dec->init_n) {
            if (Error_count_reg > m_param_dec->diverse_th) {
                jump_flag = FLAG_HIGH;
#if defined(__CORNER_CHECKER__)
                m_corner->Event_Flag(CornerChecker::IDX_FLAG_JUMP);
#endif
            }
            if (FLAG_HIGH == jump_flag) {
                Set_CSW(CSW_VALUE_JUMP);
#ifdef __4_BIT_LLR__
                if (mn < RSP1_2SD_PRIME_1 - 1 && mn > 0) {
                    mn = RSP1_2SD_PRIME_1 - 1;   // jump point
                    if (MN < RSP1_2SD_PRIME_1) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_2SD_PRIME_1;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_2SD_PRIME_2 - 1 && mn >= RSP1_2SD_PRIME_1) {
                    mn = RSP1_2SD_PRIME_2 - 1;   // jump point
                    if (MN < RSP1_2SD_PRIME_2) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_2SD_PRIME_2;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_2SD_PRIME_3 - 1 && mn >= RSP1_2SD_PRIME_2) {
                    mn = RSP1_2SD_PRIME_3 - 1;   // jump point
                    if (MN < RSP1_2SD_PRIME_3) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_2SD_PRIME_3;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_2SD_PRIME_4 - 1 && mn >= RSP1_2SD_PRIME_3) {
                    mn = RSP1_2SD_PRIME_4 - 1;   // jump point
                    if (MN < RSP1_2SD_PRIME_4) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_2SD_PRIME_4;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_2SD_PRIME_5 - 1 && mn >= RSP1_2SD_PRIME_4) {
                    mn = RSP1_2SD_PRIME_5 - 1;   // jump point
                    if (MN < RSP1_2SD_PRIME_5) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_2SD_PRIME_5;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_2SD_PRIME_6 - 1 && mn >= RSP1_2SD_PRIME_5) {
                    mn = RSP1_2SD_PRIME_6 - 1;   // jump point
                    if (MN < RSP1_2SD_PRIME_6) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_2SD_PRIME_6;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_2SD_PRIME_7 - 1 && mn >= RSP1_2SD_PRIME_6) {
                    mn = RSP1_2SD_PRIME_7 - 1;   // jump point
                    if (MN < RSP1_2SD_PRIME_7) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_2SD_PRIME_7;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_2SD_PRIME_8 - 1 && mn >= RSP1_2SD_PRIME_7) {
                    mn = RSP1_2SD_PRIME_8 - 1;   // jump point
                    if (MN < RSP1_2SD_PRIME_8) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_2SD_PRIME_8;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn >= RSP1_2SD_PRIME_8) {
                    CRC_flag = FLAG_HIGH;
                    mn = MN;
                    iter_num = mn;
                    *cur_iteration = mn; // update
                    return TRUE;
                }
#else
                if (mn < RSP1_2SD_PRIME_1 - 1 && mn > 0) {
                    mn = RSP1_2SD_PRIME_1 - 1;   // jump point
                    if (MN < RSP1_2SD_PRIME_1) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_2SD_PRIME_1;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_2SD_PRIME_2 - 1 && mn >= RSP1_2SD_PRIME_1) {
                    mn = RSP1_2SD_PRIME_2 - 1;   // jump point
                    if (MN < RSP1_2SD_PRIME_2) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_2SD_PRIME_2;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn >= RSP1_2SD_PRIME_2) {
                    CRC_flag = FLAG_HIGH;
                    mn = MN;
                    iter_num = mn;
                    *cur_iteration = mn; // update
                    return TRUE;
                }
#endif // __4_BIT_LLR__
            }
        }
        else if (MODE_DEC_3SD == m_param_dec->init_n) {
            if (Error_count_reg > m_param_dec->diverse_th) {
                jump_flag = FLAG_HIGH;
#if defined(__CORNER_CHECKER__)
                m_corner->Event_Flag(CornerChecker::IDX_FLAG_JUMP);
#endif
            }
            if (FLAG_HIGH == jump_flag) {
                Set_CSW(CSW_VALUE_JUMP);
#ifdef __4_BIT_LLR__
                if (mn < RSP1_3SD_PRIME_1 - 1 && mn > 0) {
                    mn = RSP1_3SD_PRIME_1 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_1) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_1;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_3SD_PRIME_2 - 1 && mn >= RSP1_3SD_PRIME_1) {
                    mn = RSP1_3SD_PRIME_2 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_2) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_2;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_3SD_PRIME_3 - 1 && mn >= RSP1_3SD_PRIME_2) {
                    mn = RSP1_3SD_PRIME_3 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_3) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_3;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_3SD_PRIME_4 - 1 && mn >= RSP1_3SD_PRIME_3) {
                    mn = RSP1_3SD_PRIME_4 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_4) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_4;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_3SD_PRIME_5 - 1 && mn >= RSP1_3SD_PRIME_4) {
                    mn = RSP1_3SD_PRIME_5 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_5) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_5;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_3SD_PRIME_6 - 1 && mn >= RSP1_3SD_PRIME_5) {
                    mn = RSP1_3SD_PRIME_6 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_6) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_6;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_3SD_PRIME_7 - 1 && mn >= RSP1_3SD_PRIME_6) {
                    mn = RSP1_3SD_PRIME_7 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_7) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_7;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_3SD_PRIME_8 - 1 && mn >= RSP1_3SD_PRIME_7) {
                    mn = RSP1_3SD_PRIME_8 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_8) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_8;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn >= RSP1_3SD_PRIME_8) {
                    CRC_flag = FLAG_HIGH;
                    mn = MN;
                    iter_num = mn;
                    *cur_iteration = mn; // update
                    return TRUE;
                }
#else
                if (mn < RSP1_3SD_PRIME_1 - 1 && mn > 0) {
                    mn = RSP1_3SD_PRIME_1 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_1) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_1;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_3SD_PRIME_2 - 1 && mn >= RSP1_3SD_PRIME_1) {
                    mn = RSP1_3SD_PRIME_2 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_2) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_2;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_3SD_PRIME_3 - 1 && mn >= RSP1_3SD_PRIME_2) {
                    mn = RSP1_3SD_PRIME_3 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_3) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_3;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_3SD_PRIME_4 - 1 && mn >= RSP1_3SD_PRIME_3) {
                    mn = RSP1_3SD_PRIME_4 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_4) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_4;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_3SD_PRIME_5 - 1 && mn >= RSP1_3SD_PRIME_4) {
                    mn = RSP1_3SD_PRIME_5 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_5) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_5;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn < RSP1_3SD_PRIME_6 - 1 && mn >= RSP1_3SD_PRIME_5) {
                    mn = RSP1_3SD_PRIME_6 - 1;   // jump point
                    if (MN < RSP1_3SD_PRIME_6) {
                        if (FLAG_LOW == flag_dec_1iter) {
                            MN_old = MN;
                            MN = RSP1_3SD_PRIME_6;   // update
                            flag_dec_1iter = FLAG_HIGH; // flag on
                        }
                    }
                }
                else if (mn >= RSP1_3SD_PRIME_6) {
                    CRC_flag = FLAG_HIGH;
                    mn = MN;
                    iter_num = mn;
                    *cur_iteration = mn; // update
                    return TRUE;
                }
#endif // __4_BIT_LLR__
            }
        }
        else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
            if (Error_count_reg > m_param_dec->diverse_th) {
                jump_flag = FLAG_HIGH;
#if defined(__CORNER_CHECKER__)
                m_corner->Event_Flag(CornerChecker::IDX_FLAG_JUMP);
#endif
            }
            if (FLAG_HIGH == jump_flag) {
                Set_CSW(CSW_VALUE_JUMP);
            }
        }
    }
#if defined (__ONLY_FOR_DEBUG__)
	if (FLAG_HIGH == jump_flag) {
		cout << "start mn : " << *cur_iteration << " jump mn : " << mn << endl;
	}
#endif
	* cur_iteration = mn;	// update
	return FALSE;
}
//=============================================
// Check whether CRC is satisfied or not
//=============================================
int Decoder::Check_End_Iter(int* cur_iteration)
{
	int mn = *cur_iteration;
	int crc_shortened_bits = 0;
	crc_shortened_bits = CRC_LOGIC_SHORTENED;
	if (MODE_CRC_FULL == m_param_dec->CRC_Option_F_P) {
	//CRC_decoder(cwc, m_PCM->N_b - m_PCM->M_b, &failure_flag, crc_dec_LFSR_final, crc_shortened_bits);
#if defined(__ECC_TV_)
	CRC_decoder(cwc, m_PCM->N_b - m_PCM->M_b, &failure_flag, crc_dec_LFSR_final, crc_dec_LFSR_internal, crc_shortened_bits);
#else
	CRC_decoder(cwc, m_PCM->N_b - m_PCM->M_b, &failure_flag, crc_dec_LFSR_final, crc_shortened_bits);
#endif
	memcpy(&crc_dec_LFSR_iter[CRC_LEN * (real_mn - 1)], crc_dec_LFSR_final, sizeof(int) * CRC_LEN);
#if defined (__ECC_TV_)
#if defined(__FULL_CRC__)
	m_tv_dec_inter.Print_TV_full_crc(crc_dec_LFSR_final, mn);
	m_tv_dec_inter.Print_TV_full_crc_internal(crc_dec_LFSR_internal, mn);
#endif
#endif
}
else if (MODE_CRC_PARTIAL == m_param_dec->CRC_Option_F_P || MODE_PCRC_GENIE == m_param_dec->CRC_Option_F_P) {
	if ((PCRC_STOP_TYPE_1 == stop_by_partial_crc) || (PCRC_STOP_TYPE_2 == stop_by_partial_crc)) {
		failure_flag = FLAG_LOW;
	}
	else {
		failure_flag = FLAG_HIGH;
	}
}
else if (MODE_CRC_GENIE == m_param_dec->CRC_Option_F_P) {
	Check_Genie_CRC();
}
else if (MODE_CRC_PARTIAL_LAST_ONLY == m_param_dec->CRC_Option_F_P) {
	if (PCRC_STOP_TYPE_2 == stop_by_partial_crc) {
		failure_flag = FLAG_LOW;
	}
	else {
		failure_flag = FLAG_HIGH;
	}
}
if (FLAG_LOW == failure_flag) {
	/* cor */
	iter_num = mn;
	CRC_flag = FLAG_LOW;
	return TRUE;
}
else {
	/* uncor */
	if (mn == MN) {
		//if ((FLAG_HIGH == flag_dec_1iter) || (FLAG_HIGH == flag_HBF_HD_SMN)) {
		if (FLAG_HIGH == flag_dec_1iter) {
			mn = MN_old;
		}
		iter_num = mn;
		CRC_flag = FLAG_HIGH;
		*cur_iteration = mn;	// update
		return TRUE;
	}
}
return FALSE;
}
//=============================================
// decoding 결과 얻기
// error bit 수
// strong error bit 수
// 0에서 1로 flip된 bit 수
//=============================================
void Decoder::Get_Err_Cnt(int* i_HD_input, int* i_SD_input, int* dec_output, int* err_cnt, int* strong_err_cnt, int* zero_to_one_flip_cnt, int* weak_cor_cnt)
{
	int n;
	int info_length = 0;
	int err = 0;
	int str_err = 0;
	int weak_err = 0;
	int zero_to_one_flip = 0;
	//info_length = (m_PCM->N - m_PCM->M) - m_ecc_info->shortened_bit_info_offset_end - m_ecc_info->shortened_bit_info;
	info_length = (m_PCM->N - m_PCM->M) - m_ecc_info->shortened_bit_info_offset_end;
	for (n = 0; n < info_length; n++) {
	if (Variable_mem[n] != cwc[n]) {
		err++;
		//if (n >= (m_ecc_info->shortened_bit_info + m_ecc_info->punctured_bit_info)) {
		if (n >= (m_ecc_info->shortened_bit_info)) {
			//if ((dec_output[n] == 0) && (i_HD_input[n] == 1)) {
			if ((dec_output[n] == 0) && ((Variable_mem[n]+1) % 2 == 1)) {
				zero_to_one_flip++;
			}
			if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
				if (i_SD_input[n] == 1) {
					str_err++;
				}
			}
		}
	}

else {
	if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
		if (n >= (m_ecc_info->shortened_bit_info)) {
			//if (n >= (m_ecc_info->shortened_bit_info + m_ecc_info->punctured_bit_info)) {
			if (i_SD_input[n] == 0) {
				weak_err++;
			}
		}
	}
}
}
*err_cnt = err;
*strong_err_cnt = str_err;
*zero_to_one_flip_cnt = zero_to_one_flip;
*weak_cor_cnt = weak_err;
}
//=============================================
// user data에서 1인 bit 수 count
//=============================================
int Decoder::Get_One_Cnt(int* dec_output)
{
	int n;
	int bit_counter = 0;
int info_length = 0;
info_length = (m_PCM->N - m_PCM->M) - m_ecc_info->shortened_bit_info_offset_end;
for (n = m_ecc_info->shortened_bit_info ; n < info_length; n++) {
	bit_counter += dec_output[n];
}
/*bit_counter = 0;
for (n = m_ecc_info->shortened_bit_info; n < 256; n++) {
	bit_counter += dec_output[n];
}
printf("%d\n", 224 - bit_counter);
bit_counter = 0;
for (n = 256; n < 512; n++) {
	bit_counter += dec_output[n];
}
printf("%d\n", 256 - bit_counter);
for (int i = 2; i < 128; i++)
{
	bit_counter = 0;
	for (int j = 0; j < 256; j++)
	{
		bit_counter += dec_output[i*256 + j];
	}
	printf("%d\n", bit_counter);
}
bit_counter = 0;
for (n = info_length - 176; n < info_length; n++) {
	bit_counter += dec_output[n];
}
printf("%d\n", bit_counter);*/
return bit_counter;
}
//================================================
// Min position default 값을 얻는다.
//================================================
int Decoder::Get_Default_Min_Pos(int row_idx)
{
int pos = 0;
return pos;
}
//================================================
// 매 column 마다 flip한 bit 수를 count함
// jj-th column block
//================================================
void Decoder::Count_Flip_Bits(int jj)
{
int i;
int N_b = m_PCM->N_b;
int M_b = m_PCM->M_b;
int z_sb = m_PCM->z_sb;
int bit_pos;
if ((jj >= 0) && (jj < N_b - M_b - 1)) {	// user data only (perfect block)
	for (i = 0; i < z_sb; i++) {
		bit_pos = z_sb * jj + i;
		if (cwc[bit_pos] != Variable_mem[bit_pos]) Error_count_reg++;
	}
}
else if (jj == N_b - M_b - 1) { // user data only (non-perfect block)
	for (i = 0; i < z_sb; i++) {
		bit_pos = z_sb * jj + i;
		if (bit_pos < m_ecc_info->bit_pos.info_end) {
			if (cwc[bit_pos] != Variable_mem[bit_pos]) Error_count_reg++;
		}
	}
}
}
//================================================
// Power stopping 조건을 만족하는지 판단한다.
// jj-th column block
//================================================
void Decoder::Check_Power_Stopping_Cond(int jj)
{
int N_b = m_PCM->N_b;
int M_b = m_PCM->M_b;
//Deneb때 RTL과의 정합성을 위해 에외처리 없이 모두 clk based로 power-stopping check
if ((jj >= 0) && (jj < N_b - M_b)) {
	if (Error_count_reg > m_param_dec->diverse_th) {
#if defined(__CORNER_CHECKER__)
		m_corner->Event_Flag(CornerChecker::IDX_FLAG_POWER_STOPPING);
		if (FALSE == pre_Force_stopping) {
			m_corner->Event_Power_Stopping(jj);
		}
#endif
		pre_Force_stopping = TRUE;
	}
}
}
//================================================
// Cycle 마다 TV를 출력한다.
// jj-th column block
//================================================
void Decoder::Print_TV_Cycle_Based(int jj, int clk)
{
if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
	if (mn >= 1) {
		m_tv_dec_inter.Print_TV_cnd_min(tv_upt_min, tv_min_weak, tv_min_weak2, mn, jj, clk);
		m_tv_dec_inter.Print_TV_check_sum(Check_REG, Syndrome, FALSE, mn, jj);
	}
}
else if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
	if (mn >= 0) {
		m_tv_dec_inter.Print_TV_cnd_min(tv_upt_min, tv_min_weak, tv_min_weak2, mn, jj, clk);
		//m_tv_dec_inter.Print_TV_check_sum(Check_REG, Syndrome, FALSE, mn, jj);
		// Check_SUM만 iter 1부터 출력되도록 수정
		// 2SD, 3SD시 HW에서는 iter=0 전에 PR 완료된 상태인 반면, Ref-C에서는 HD와 동일하게 iter=0에서 PR 수행하기 때문에 TV 정합성 검증 시 수행
		if (jj==CYCLE_END) m_tv_dec_inter.Print_TV_check_sum(Check_REG, Syndrome, FALSE, mn, jj);
		else {
			if (mn>=1) m_tv_dec_inter.Print_TV_check_sum(Check_REG, Syndrome, FALSE, mn, jj);
		}
	}
}
}
void Decoder::DU_Manager()
{
//참고: http://edm2.sec.samsung.net/cc/link/verLink/160929367424604534/18 (2021.05.13 KHY)
//PCRC와 관련된 조건 모두 제거 (2023.11.21 Song minki)
if ((m_PCM->ColW[col_M1] <= DV_5 && m_PCM->ColW[col_M1] >= DV_2) &&
	(m_PCM->ColW[col_M1 + 1] <= DV_5 && m_PCM->ColW[col_M1 + 1] >= DV_2) &&
	(col_M1 + 1 < m_PCM->N_b))
{
	DU_flag_M1 = TRUE;
}
else
{
	DU_flag_M1 = FALSE;
}
if ((m_PCM->ColW[col_Z] <= DV_5 && m_PCM->ColW[col_Z] >= DV_2) &&
	(m_PCM->ColW[col_Z + 1] <= DV_5 && m_PCM->ColW[col_Z + 1] >= DV_2) &&
	(col_Z + 1 < m_PCM->N_b))
{
	DU_flag_Z = TRUE;
}
else
{
	DU_flag_Z = FALSE;
}
if ((m_PCM->ColW[col_P1] <= DV_5 && m_PCM->ColW[col_P1] >= DV_2) &&
	(m_PCM->ColW[col_P1 + 1] <= DV_5 && m_PCM->ColW[col_P1 + 1] >= DV_2) &&
	(col_P1 + 1 < m_PCM->N_b))
{
	DU_flag_P1 = TRUE;
}
else
{
	DU_flag_P1 = FALSE;
}
if ((m_PCM->ColW[col_P2] <= DV_5 && m_PCM->ColW[col_P2] >= DV_2) &&
	(m_PCM->ColW[col_P2 + 1] <= DV_5 && m_PCM->ColW[col_P2 + 1] >= DV_2) &&
	(col_P2 + 1 < m_PCM->N_b))
{
	DU_flag_P2 = TRUE;
}
else
{
	DU_flag_P2 = FALSE;
}
if ((m_PCM->ColW[col_P3] <= DV_5 && m_PCM->ColW[col_P3] >= DV_2) &&
	(m_PCM->ColW[col_P3 + 1] <= DV_5 && m_PCM->ColW[col_P3 + 1] >= DV_2) &&
	(col_P3 + 1 < m_PCM->N_b))
{
	DU_flag_P3 = TRUE;
}
else
{
	DU_flag_P3 = FALSE;
}
if ((m_PCM->ColW[col_P4] <= DV_5 && m_PCM->ColW[col_P4] >= DV_2) &&
	(m_PCM->ColW[col_P4 + 1] <= DV_5 && m_PCM->ColW[col_P4 + 1] >= DV_2) &&
	(col_P4 + 1 < m_PCM->N_b))
{
	DU_flag_P4 = TRUE;
}
else
{
	DU_flag_P4 = FALSE;
}
/*
//if (col_M1 == m_PCM->N_b - m_PCM->M_b)
if (col_M1 == m_PCM->N_b - m_PCM->M_b - 1)
{
	DU_flag_M1 = FALSE;
}
else if ((m_PCM->ColW[col_M1] <= DV_5 && m_PCM->ColW[col_M1] >= DV_2) &&
	(m_PCM->ColW[col_M1 + 1] <= DV_5 && m_PCM->ColW[col_M1 + 1] >= DV_2) &&
	(col_M1 + 1 < m_PCM->N_b))
{
	DU_flag_M1 = TRUE;
}
else
{
	DU_flag_M1 = FALSE;
}
//if (col_Z == m_PCM->N_b - m_PCM->M_b)
if (col_Z == m_PCM->N_b - m_PCM->M_b - 1)
{
	DU_flag_Z = FALSE;
}
else if ((m_PCM->ColW[col_Z] <= DV_5 && m_PCM->ColW[col_Z] >= DV_2) &&
	(m_PCM->ColW[col_Z + 1] <= DV_5 && m_PCM->ColW[col_Z + 1] >= DV_2) &&
	(col_Z + 1 < m_PCM->N_b))
{
	DU_flag_Z = TRUE;
}
else
{
	DU_flag_Z = FALSE;
}
//if (col_P1 == m_PCM->N_b - m_PCM->M_b)
if (col_P1 == m_PCM->N_b - m_PCM->M_b - 1)
{
	DU_flag_P1 = FALSE;
}
else if ((m_PCM->ColW[col_P1] <= DV_5 && m_PCM->ColW[col_P1] >= DV_2) &&
	(m_PCM->ColW[col_P1 + 1] <= DV_5 && m_PCM->ColW[col_P1 + 1] >= DV_2) &&
	(col_P1 + 1 < m_PCM->N_b))
{
	DU_flag_P1 = TRUE;
}
else
{
	DU_flag_P1 = FALSE;
}
//if (col_P2 == m_PCM->N_b - m_PCM->M_b)
if (col_P2 == m_PCM->N_b - m_PCM->M_b - 1)
{
	DU_flag_P2 = FALSE;
}
else if ((m_PCM->ColW[col_P2] <= DV_5 && m_PCM->ColW[col_P2] >= DV_2) &&
	(m_PCM->ColW[col_P2 + 1] <= DV_5 && m_PCM->ColW[col_P2 + 1] >= DV_2) &&
	(col_P2 + 1 < m_PCM->N_b))
{
	DU_flag_P2 = TRUE;
}
else
{
	DU_flag_P2 = FALSE;
}
//if (col_P3 == m_PCM->N_b - m_PCM->M_b)
if (col_P3 == m_PCM->N_b - m_PCM->M_b - 1)
{
	DU_flag_P3 = FALSE;
}
else if ((m_PCM->ColW[col_P3] <= DV_5 && m_PCM->ColW[col_P3] >= DV_2) &&
	(m_PCM->ColW[col_P3 + 1] <= DV_5 && m_PCM->ColW[col_P3 + 1] >= DV_2) &&
	(col_P3 + 1 < m_PCM->N_b))
{
	DU_flag_P3 = TRUE;
}
else
{
	DU_flag_P3 = FALSE;
}
//if (col_P4 == m_PCM->N_b - m_PCM->M_b)
if (col_P4 == m_PCM->N_b - m_PCM->M_b - 1)
{
	DU_flag_P4 = FALSE;
}
else if ((m_PCM->ColW[col_P4] <= DV_5 && m_PCM->ColW[col_P4] >= DV_2) &&
	(m_PCM->ColW[col_P4 + 1] <= DV_5 && m_PCM->ColW[col_P4 + 1] >= DV_2) &&
	(col_P4 + 1 < m_PCM->N_b))
{
	DU_flag_P4 = TRUE;
}
else
{
	DU_flag_P4 = FALSE;
}
*/
}
//================================================
// Calculate V2C (VNU_out)
// jj-th column block
//================================================
void Decoder::V2C_Cal(int jj)
{
#if defined (__ONLY_FOR_DEBUG__)
cout << "V2C_cal() : " << jj << endl;
#endif
int i;
int z_sb = m_PCM->z_sb;
int idx_offset = jj * z_sb;
if (MODE_DEC_HD == m_param_dec->init_n) {
	if (TRUE == Is_Iter_Type_Init(mn)) {
		VN_Cal_Pre(jj);
	}
	else {
		VN_Cal_HD(m_PCM->ColW[jj], idx_offset, mn);
	}
}
else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
	if (TRUE == Is_Iter_Type_Init(mn)) {
		VN_Cal_Pre(jj);
}
else {
	VN_Cal_CD(m_PCM->ColW[jj], idx_offset, mn);
}
}
else if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
	if (TRUE == Is_Iter_Type_Init(mn)) {
		VN_Cal_Pre(jj);
	}
	else {
		VN_Cal_SD(m_PCM->ColW[jj], idx_offset, mn);
	}
}
/* Copy for PCRC */
for (i = 0; i < z_sb; i++) { dec_d[i] = cwc[idx_offset + i]; }
}
//================================================
// Calculate V2C (VNU_out)
// Half Column Update용
// jj-th column block
//================================================
void Decoder::V2C_Cal_HCU(int jj, int G_idx)
{
#if defined (__ONLY_FOR_DEBUG__)
cout << "V2C_cal() : " << jj << endl;
#endif
int i;
int z_sb = m_PCM->z_sb;
int idx_offset = jj * z_sb;
if (MODE_DEC_HD == m_param_dec->init_n) {
	if (TRUE == Is_Iter_Type_Init(mn)) {
		VN_Cal_Pre_HCU(jj, G_idx);
	}
	else {
		VN_Cal_HD_HCU(m_PCM->ColW[jj], idx_offset, G_idx, mn);
	}
}
else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
	if (TRUE == Is_Iter_Type_Init(mn)) {
		VN_Cal_Pre_HCU(jj, G_idx);
	}
	else {
		VN_Cal_CD(m_PCM->ColW[jj], idx_offset, mn);
	}
}
else if ((MODE_DEC_2SD == m_param_dec->init_n) || (MODE_DEC_3SD == m_param_dec->init_n)) {
	if (TRUE == Is_Iter_Type_Init(mn)) {
		VN_Cal_Pre_HCU(jj, G_idx);
	}
	else {
		VN_Cal_SD_HCU(m_PCM->ColW[jj], idx_offset, G_idx, mn);
	}
}
/* Copy for PCRC */
if (G_idx == 1) {
	for (i = 0; i < z_sb; i++) { dec_d[i] = cwc[idx_offset + i]; }
}
}
//================================================
// PMU SRAM 전체를 초기화 한다.
//================================================
void Decoder::Clear_PMU()
{
int n;
int i;
int factor = m_PCM->z_sb / PMU_UNIT_SIZE;
#if defined(__HALF_COL_UPDATE__)
int tot_PMU_len = factor * MAX_DV_GLOBAL_HALF * PMU_UNIT_WIDTH;
for (n = 0; n < m_PCM->N_b+m_PCM->punct_col_num; n++) {
	for (i = 0; i < tot_PMU_len; i++) {
		PMU_SRAM[n][i] = PMU_HIT;
	}
}
#else
int tot_PMU_len = factor * m_PCM->J * PMU_UNIT_WIDTH;
for (n = 0; n < m_PCM->N_b; n++) {
	for (i = 0; i < tot_PMU_len; i++) {
		PMU_SRAM[n][i] = PMU_HIT;
	}
}
#endif
}
//================================================
// PMU SRAM 전체를 초기화 한다.
//================================================
void Decoder::Clear_Sum_t_OLD()
{
for (int i = 0;i < m_PCM->punct_col_num;i++) Init_Buf(Sum_t_OLD_G0[i], m_PCM->z_sb);
for (int i = 0;i < m_PCM->punct_col_num;i++) Init_Buf(Sum_t_OLD_G1[i], m_PCM->z_sb);
}
//================================================
// PMU read를 수행한다.
//================================================
void Decoder::PMU_Read(int jj)
{
#if defined (__ONLY_FOR_DEBUG__)
cout << "PMU_Read() : " << jj << endl;
#endif
int n;
int i;
int status;
#if defined(__HALF_COL_UPDATE__)
//int sram_inst_num = MAX_DV_GLOBAL;
int sram_inst_num = 2 * MAX_DV_GLOBAL_HALF;
#else
int sram_inst_num = 2 * m_PCM->J;
#endif
int eff_sram_inst_num = 2 * m_PCM->ColW[jj];
int fragment;
int sub_idx = 0;
int mux_idx;
int offset;
int zero;
int bRead = FALSE;
if (FALSE == Is_Iter_Type_Init(mn)) {
	bRead = TRUE;
}
if (TRUE == bRead) {
	/* De-compression */
	for (n = 0; n < /*eff_sram_inst_num*/ sram_inst_num; n++) {
		mux_idx = n / 2;
		fragment = n % 2;
		offset = n * PMU_UNIT_WIDTH;
#if defined(__HALF_COL_UPDATE__)
		//status = PMU_SRAM[jj+m_PCM->punct_col_num][offset];
		if (jj < HCU_start) {
			status = PMU_SRAM[jj][offset];
		}
		else {
			status = PMU_SRAM[jj + m_PCM->punct_col_num][offset];
		}
#else
		status = PMU_SRAM[jj][offset];
#endif
		if (PMU_HIT == status) {
			Intentional_Blank();
		}
		else {
			zero = TRUE;
			for (i = 1; i < PMU_UNIT_WIDTH; i++) {
#if defined(__HALF_COL_UPDATE__)
				//if (PMU_SRAM[jj + m_PCM->punct_col_num][offset + i] == 1) { zero = FALSE; break; }
				if (jj < HCU_start) {
					if (PMU_SRAM[jj][offset + i] == 1) {
						zero = FALSE;
						break;
					}
				}
				else {
					if (PMU_SRAM[jj + m_PCM->punct_col_num][offset + i] == 1) {
						zero = FALSE;
						break;
					}
				}
#else
				if (PMU_SRAM[jj][offset + i] == 1) { zero = FALSE;  break; }
#endif
			}
			if (FALSE == zero) {
				/* case (2) number of minus sign is greater than 1 */
				MAIN_SRAM_read_rq[n] = TRUE;
			}
		}
	} // end for loop (n)
}
}
//================================================
// PMU write을 관리한다.
//================================================
void Decoder::PMU_Write(int jj)
{
if ((jj >= 0) && (jj < m_PCM->N_b)) {
#if defined (__ONLY_FOR_DEBUG__)
	cout << "PMU_Write() : " << jj << endl;
#endif
	int n;
	int i;
	int factor = m_PCM->z_sb / PMU_UNIT_SIZE;
#if defined(__HALF_COL_UPDATE__)
	//int sram_inst_num = MAX_DV_GLOBAL;
	//int sram_inst_num = 2 * MAX_DV_GLOBAL_HALF;
	int sram_inst_num = 2 * MAX_DV_GLOBAL_HALF;
#else
	int sram_inst_num = factor * m_PCM->J;
#endif
	int eff_sram_inst_num = factor * m_PCM->ColW[jj];
	int fragment;
	int sub_idx;
	int offset;
	int minus_cnt;
	int pos;
	int mux_idx;
	int bWrite = FALSE;
	if (FALSE == Is_Iter_Type_Init(mn)) {
		bWrite = TRUE;
	}
	if (TRUE == bWrite) {
		/* Compression */
		for (int ii = 0; ii < m_PCM->ColW[jj]; ii++) {
			mux_idx = m_PCM->Mux_idx[ii][jj];
			for (fragment = 0; fragment < factor; fragment++) {
				n = mux_idx * factor + fragment;
				offset = n * PMU_UNIT_WIDTH;
				/* Count number of minus sign */
				minus_cnt = 0;
				sub_idx = 0;
				for (i = 0; i < PMU_UNIT_SIZE; i++) {
					if (mn > 0) {
						pos = (m_PCM->z_sb - 1) - i - (fragment * PMU_UNIT_SIZE);
						if (VNU_out3_temp[mux_idx][pos] < 0) {
							minus_cnt++;
							sub_idx = i;
						}
					}
				}
				/* PMU write */
                if (minus_cnt == 0) {
#if defined(__HALF_COL_UPDATE__)
				if (jj < HCU_start) {
					PMU_SRAM[jj][offset] = PMU_NON_HIT;
					for (i = 1; i < PMU_UNIT_WIDTH; i++) {
						PMU_SRAM[jj][offset + i] = 0;
					}
				}
				else {
					PMU_SRAM[jj + m_PCM->punct_col_num][offset] = PMU_NON_HIT;
					for (i = 1; i < PMU_UNIT_WIDTH; i++) {
						PMU_SRAM[jj + m_PCM->punct_col_num][offset + i] = 0;
					}
				}
#else
				PMU_SRAM[jj][offset] = PMU_NON_HIT;
				for (i = 1; i < PMU_UNIT_WIDTH; i++) { PMU_SRAM[jj][offset + i] = 0; }
#endif
			}
#if defined(__PMU_ERROR_ONE__)
			else if (minus_cnt == 1) {
				/* PMU write */
#if defined(__HALF_COL_UPDATE__)
				if (jj < HCU_start) {
					PMU_SRAM[jj][offset] = PMU_HIT;
					PMU_SRAM[jj][offset + 7] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[jj][offset + 6] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[jj][offset + 5] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[jj][offset + 4] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[jj][offset + 3] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[jj][offset + 2] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[jj][offset + 1] = sub_idx % 2;
				}
				else {
					PMU_SRAM[jj + m_PCM->punct_col_num][offset] = PMU_HIT;
					PMU_SRAM[jj + m_PCM->punct_col_num][offset + 7] = sub_idx % 2;  sub_idx = sub_idx / 2;
					PMU_SRAM[jj + m_PCM->punct_col_num][offset + 6] = sub_idx % 2;  sub_idx = sub_idx / 2;
					PMU_SRAM[jj + m_PCM->punct_col_num][offset + 5] = sub_idx % 2;  sub_idx = sub_idx / 2;
					PMU_SRAM[jj + m_PCM->punct_col_num][offset + 4] = sub_idx % 2;  sub_idx = sub_idx / 2;
					PMU_SRAM[jj + m_PCM->punct_col_num][offset + 3] = sub_idx % 2;  sub_idx = sub_idx / 2;
					PMU_SRAM[jj + m_PCM->punct_col_num][offset + 2] = sub_idx % 2;  sub_idx = sub_idx / 2;
					PMU_SRAM[jj + m_PCM->punct_col_num][offset + 1] = sub_idx % 2;
				}
#else
				PMU_SRAM[jj][offset] = PMU_HIT;
				PMU_SRAM[jj][offset + 7] = sub_idx % 2; sub_idx = sub_idx / 2;
				PMU_SRAM[jj][offset + 6] = sub_idx % 2; sub_idx = sub_idx / 2;
				PMU_SRAM[jj][offset + 5] = sub_idx % 2; sub_idx = sub_idx / 2;
				PMU_SRAM[jj][offset + 4] = sub_idx % 2; sub_idx = sub_idx / 2;
				PMU_SRAM[jj][offset + 3] = sub_idx % 2; sub_idx = sub_idx / 2;
				PMU_SRAM[jj][offset + 2] = sub_idx % 2; sub_idx = sub_idx / 2;
				PMU_SRAM[jj][offset + 1] = sub_idx % 2;
#endif
			}
#endif
			else {
				/* PMU Write */
#if defined(__HALF_COL_UPDATE__)
				if (jj < HCU_start) {
					PMU_SRAM[jj][offset] = PMU_NON_HIT;
					for (i = 1; i < PMU_UNIT_WIDTH; i++) {
						PMU_SRAM[jj][offset + i] = 1;
					}
				}
				else {
					PMU_SRAM[jj + m_PCM->punct_col_num][offset] = PMU_NON_HIT;
					for (i = 1; i < PMU_UNIT_WIDTH; i++) {
						PMU_SRAM[jj + m_PCM->punct_col_num][offset + i] = 1;
					}
				}
#else
				PMU_SRAM[jj][offset] = PMU_NON_HIT;
				for (i = 1; i < PMU_UNIT_WIDTH; i++) { PMU_SRAM[jj][offset + i] = 1; }
#endif
				/* Main SRAM write */
				MAIN_SRAM_write_rq[n] = TRUE;
			}
		}
		}
	}
}
}
//================================================
// Half Column Update용 Group index 반영
// PMU read를 수행한다.
//================================================
void Decoder::PMU_Read_HCU(int jj, int G_idx)
{
#if defined (__ONLY_FOR_DEBUG__)
cout << "PMU_Read() : " << jj << endl;
#endif
int n;
int i;
int status;
int sram_inst_num = 0;
int sram_inst_num_separate_column = 0;
//int eff_sram_inst_num = 2 * m_PCM->ColW[jj];
int fragment;
int sub_idx = 0;
int mux_idx;
int offset;
int zero;
int bRead = FALSE;
//int sram_inst_num_half_column = sram_inst_num / 2;
// Dv17 Case
// iter가 even
// G0: 0~9 / G1: 10~16
// iter가 odd
// G0: 7~16 / G1: 0~6
// Dv13 Case
// iter가 even
// G0: 0~9 / G1: 10~12
// iter가 odd
// G0: 3~12 / G1: 0~2
if (jj == HCU_start) {
	sram_inst_num = 2 * MAX_DV_GLOBAL;
	//if (mn % 2 ==0) sram_inst_num_separate_column = 2 * 10;
	//else sram_inst_num_separate_column = 2 * 7;
	sram_inst_num_separate_column = 2 * 9;
}
else if (jj == HCU_end) {
	sram_inst_num = 2 * MAX_DV_GLOBAL_2ND;
	//if (mn % 2 == 0) sram_inst_num_separate_column = 2 * 10;
	//else sram_inst_num_separate_column = 2 * 3;
	sram_inst_num_separate_column = 2 * 7;
}
int start_idx = 0;
int end_idx = 0;
int current_G_idx;
current_G_idx = (G_idx + mn) % 2;
if (current_G_idx == 0) { start_idx = 0; end_idx = sram_inst_num_separate_column; }
else if (current_G_idx == 1) { start_idx = sram_inst_num_separate_column; end_idx = sram_inst_num; }
if (FALSE == Is_Iter_Type_Init(mn)) {
	bRead = TRUE;
}
if (TRUE == bRead) {
	/* De-compression */
	//for (n = 0; n < /*eff_sram_inst_num*/ sram_inst_num; n++) {
	for (n = start_idx; n < end_idx; n++) {
		mux_idx = n / 2;
		fragment = n % 2;
		//offset = n * PMU_UNIT_WIDTH;
		//status = PMU_SRAM[jj][offset];
		offset = (n-start_idx) * PMU_UNIT_WIDTH;
		//status = PMU_SRAM[2 * jj + current_G_idx][offset];
		status = PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset];
		if (PMU_HIT == status) {
			/* case (1) number of minus sign is equal to 1 */
			Intentional_Blank();
		}
		else {
			zero = TRUE;
			for (i = 1; i < PMU_UNIT_WIDTH; i++) {
				//if (PMU_SRAM[jj][offset + i] == 1) { zero = FALSE;	break; }
				//if (PMU_SRAM[2 * jj + current_G_idx][offset + i] == 1) { zero = FALSE;	break; }
				if (PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset + i] == 1) {
					zero = FALSE;
					break;
				}
			}
			if (FALSE == zero) {
				/* case (2) number of minus sign is greater than 1 */
				//MAIN_SRAM_read_rq[n] = TRUE;
				MAIN_SRAM_read_rq[n - start_idx] = TRUE;
			}
		}
	} // end for loop (n)
}
}
//================================================
// Half Column Update용 Group index 반영
// PMU write을 관리한다.
//================================================
void Decoder::PMU_Write_HCU(int jj, int G_idx)
{
if ((jj >= 0) && (jj < m_PCM->N_b)) {
#if defined (__ONLY_FOR_DEBUG__)
	cout << "PMU_Write() : " << jj << endl;
#endif
	int n;
	int i;
	int factor = m_PCM->z_sb / PMU_UNIT_SIZE;
	int Dv_max = 0;
	int DV_seperate = 0;
	//int sram_inst_num = factor * m_PCM->J;
	//int eff_sram_inst_num = factor * m_PCM->ColW[jj];
	int fragment;
	int sub_idx;
	int offset;
	int minus_cnt;
	int pos;
	int mux_idx;
	int bWrite = FALSE;
	int Half_dv_max = m_PCM->J / 2;
	int start_idx = 0;
	int end_idx = 0;
	int current_G_idx = (G_idx + mn) % 2;
	if (jj == HCU_start) {
		Dv_max = MAX_DV_GLOBAL;
		DV_seperate = SEPARATE_V_DEG_1;
	}
	else if (jj == HCU_end) {
		Dv_max = MAX_DV_GLOBAL_2ND;
		DV_seperate = SEPARATE_V_DEG_2;
	}
	if (current_G_idx == 0) {
		start_idx = 0;
		end_idx = DV_seperate;
	}
	else if (current_G_idx == 1) {
		start_idx = DV_seperate;
		end_idx = Dv_max;
	}
	if (FALSE == Is_Iter_Type_Init(mn)) {
		bWrite = TRUE;
	}
	if (TRUE == bWrite) {
		/* Compression */
		//for (int ii = 0; ii < m_PCM->ColW[jj]; ii++) {
		for (int ii = start_idx; ii < end_idx; ii++) {
			mux_idx = m_PCM->Mux_idx[ii][jj];
			for (fragment = 0; fragment < factor; fragment++) {
				//n = mux_idx * factor + fragment;
				if (current_G_idx == 0) n = mux_idx * factor + fragment;
				else if (current_G_idx == 1) n = (mux_idx - DV_seperate) * factor + fragment;
				offset = n * PMU_UNIT_WIDTH;
				/* Count number of minus sign */
				minus_cnt = 0;
				sub_idx = 0;
				for (i = 0; i < PMU_UNIT_SIZE; i++) {
					if (mn > 0) {
						pos = (m_PCM->z_sb - 1) - i - (fragment * PMU_UNIT_SIZE);
						if (VNU_out3_temp[mux_idx][pos] < 0) {
							minus_cnt++;
							sub_idx = i;
						}
					}
				}
				if (minus_cnt == 0) {
					/* PMU write */
					//PMU_SRAM[jj][offset] = PMU_NON_HIT;
					//for (i = 1; i < PMU_UNIT_WIDTH; i++) { PMU_SRAM[jj][offset + i] = 0; }
					//PMU_SRAM[2 * jj + current_G_idx][offset] = PMU_NON_HIT;
					//for (i = 1; i < PMU_UNIT_WIDTH; i++) { PMU_SRAM[2 * jj + current_G_idx][offset + i] = 0; }
					PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset] = PMU_NON_HIT;
					for (i = 1; i < PMU_UNIT_WIDTH; i++) {
						PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset + i] = 0;
					}
				}
#if defined(__PMU_ERROR_ONE__)
				else if (minus_cnt == 1) {
					/* PMU write */
					/*
					PMU_SRAM[jj][offset] = PMU_HIT;
					PMU_SRAM[jj][offset + 7] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[jj][offset + 6] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[jj][offset + 5] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[jj][offset + 4] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[jj][offset + 3] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[jj][offset + 2] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[jj][offset + 1] = sub_idx % 2;
					*/
					/*
					if (jj < HCU_start) {
					PMU_SRAM[2 * jj + current_G_idx][offset] = PMU_HIT;
					PMU_SRAM[2 * jj + current_G_idx][offset + 7] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[2 * jj + current_G_idx][offset + 6] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[2 * jj + current_G_idx][offset + 5] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[2 * jj + current_G_idx][offset + 4] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[2 * jj + current_G_idx][offset + 3] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[2 * jj + current_G_idx][offset + 2] = sub_idx % 2; sub_idx = sub_idx / 2;
					PMU_SRAM[2 * jj + current_G_idx][offset + 1] = sub_idx % 2;
					*/
					PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset] = PMU_HIT;
					PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset + 7] = sub_idx % 2;	sub_idx = sub_idx / 2;
					PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset + 6] = sub_idx % 2;	sub_idx = sub_idx / 2;
					PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset + 5] = sub_idx % 2;	sub_idx = sub_idx / 2;
					PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset + 4] = sub_idx % 2;	sub_idx = sub_idx / 2;
					PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset + 3] = sub_idx % 2;	sub_idx = sub_idx / 2;
					PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset + 2] = sub_idx % 2;	sub_idx = sub_idx / 2;
					PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset + 1] = sub_idx % 2;
				}
#endif
				else {
					/* PMU write */
					//PMU_SRAM[jj][offset] = PMU_NON_HIT;
					//for (i = 1; i < PMU_UNIT_WIDTH; i++) { PMU_SRAM[jj][offset + i] = 1; }
					//PMU_SRAM[2 * jj + current_G_idx][offset] = PMU_NON_HIT;
					//for (i = 1; i < PMU_UNIT_WIDTH; i++) { PMU_SRAM[2 * jj + current_G_idx][offset + i] = 1; }
					PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset] = PMU_NON_HIT;
					for (i = 1; i < PMU_UNIT_WIDTH; i++) {
						PMU_SRAM[jj + 2 * (jj - (HCU_start)) + current_G_idx][offset + i] = 1;
					}
					/* Main SRAM write */
					MAIN_SRAM_write_rq[n] = TRUE;
					//MAIN_SRAM_write_rq[n-start_idx] = TRUE;
				}
			}
		}
	}
}
}
//================================================
// Clk을 관리한다.
// phase P1에서 발생한 main SRAM read
// request와 phase P4에서 발생한 main SRAM
// write request, FIFO level을 보고 판단한다.
//================================================
void Decoder::Clk_Manager(int clk)
{
#if defined (__ONLY_FOR_DEBUG__)
cout << "Clk_Manager()" << endl;
#endif
int n;
int factor = m_PCM->z_sb / PMU_UNIT_SIZE;
#if defined(__HALF_COL_UPDATE__)
int sram_inst_num = factor * MAX_DV_GLOBAL_HALF;
#else
int sram_inst_num = factor * m_PCM->J;
#endif
int condition = 0;
int idx;
int insert_idle = FALSE;
for (n = 0; n < sram_inst_num; n++) {
	/* queue delete */
	if (FIFO_level[n] > 0) {
		if ((MAIN_SRAM_read_rq2[n] == FALSE) && (MAIN_SRAM_write_rq[n] == FALSE)) {
			// write가 가능한 시점이기 때문에 FIFO에 저장되어 있던 write request를 꺼낸다.
			FIFO_level[n]--;
		}
	}
	/* queue insert */
	if ((MAIN_SRAM_read_rq2[n] == TRUE) && (MAIN_SRAM_write_rq[n] == TRUE)) {
		// 현 clk에 동시에 read와 write request가 들어옴
		// read를 우선으로 처리함 (다음 clk에서 enable 시킴)
		// write request는 FIFO에 추가
		FIFO_level[n]++;
	}
	/* flag condition */
	if ((MAIN_SRAM_read_rq[n] == TRUE) && (FIFO_level[n] >= 2)) {
		insert_idle = TRUE;
		condition = 1;
		idx = n;
	}
	else if (FIFO_level[n] == 4) {
		insert_idle = TRUE;
		condition = 2;
		idx = n;
	}
} // end for (n)
	/* idle cycle counter update */
	if (TRUE == insert_idle) {
	if (0 == cnt_idle_cycle) {
		cnt_idle_cycle = 2;
#if defined (__ONLY_FOR_DEBUG__)
		cout << "*** idle_cycle == condition : " << condition << "\tidx : " << idx << endl;
#endif
#if defined(__CORNER_CHECKER__)
		m_corner->Event_Flag(CornerChecker::IDX_FLAG_IDLE_CYCLE);
#endif
	}
}
}
//=============================================
// Phase에 맞게 처리할 column 번호를 설정한다.
//=============================================
int Decoder::Clk_Inc(int clk)
{
#if defined (__ONLY_FOR_DEBUG__)
	FILE* fp = fopen("phase.dat", "a");
	fprintf(fp, "%3d\t%3d\t%3d\t%3d\t%3d\t%3d\t%3d\n", mn, clk, col_M1, col_Z, col_P1, col_P2, col_P3, col_P4);
	fclose(fp);
#endif
#if defined (__ONLY_FOR_DEBUG__)
	cout << "Clk_Inc()" << endl;
#endif
	col_P4 = col_P3;
	col_P3 = col_P2;
	col_P2 = col_P1;
	col_P1 = col_Z;
	col_Z = col_M1;
	col_P4_G = col_P3_G;
	col_P3_G = col_P2_G;
	col_P2_G = col_P1_G;
	col_P1_G = col_Z_G;
	col_Z_G = col_M1_G;
	if (CYCLE_END == col_M1) {
		/* 가장 빠른 phase가 모든 column을 수행한 경우 다른 phase도 끝날 때 까지 기다림 */
		Intentional_Blank();
	}
	else if ((DU_flag_M1 == TRUE && col_M1 + 1 == m_PCM->N_b - 1) ||
		 (DU_flag_M1 == FALSE && col_M1 == m_PCM->N_b - 1)) {
	/* 마지막 column까지 처리하는 순서가 모두 결정되었는데 이때 cnt_idle_cycle이 2라서 idle cycle이 삽입되는 경우를 방지하기 위함 */
	if (DU_flag_M1 == TRUE)
		col_M1 = col_M1 + 2;
	else
		col_M1 = col_M1 + 1;
	/* 종료 판단 */
	if (col_M1 == m_PCM->N_b)
		col_M1 = CYCLE_END;
}
else {
	if (2 == cnt_idle_cycle) {
		/* Clk_Manager()에서 idle cycle을 2개 삽입하라고 한 상태 */
		if (CYCLE_IDLE != col_M1) {
			col_M1_temp = col_M1;	// 현재까지 수행한 column 번호
			col_M1_temp_G = col_M1_G;
			DU_flag_M1_temp = DU_flag_M1;
			col_M1 = CYCLE_IDLE;
		}
		cnt_idle_cycle--;
	}
	else {
		if (CYCLE_IDLE == col_M1) {
			if (1 == cnt_idle_cycle) {
				cnt_idle_cycle--;
			}
			else if (0 == cnt_idle_cycle) {
				/* 삽입했던 2개 idle cycle이 다 끝나서 원래 column으로 돌아가는 경우 */
				col_M1 = col_M1_temp;
				col_M1_G = col_M1_temp_G;
				DU_flag_M1 = DU_flag_M1_temp;
				if (DU_flag_M1 == TRUE)
					col_M1 = col_M1 + 2;
				else {
#if defined(__HALF_COL_UPDATE__)
#if defined(__HACRC_IKD_5B__)
#else
			//if (col_M1 == 0 && col_M1_G == 0) { col_M1 = col_M1; col_M1_G = col_M1_G + 1; }
			//else if (col_M1 == 0 && col_M1_G == 1) { col_M1 = col_M1 + 1; col_M1_G = 0; }
			//else if (col_M1 == 1 && col_M1_G == 0) { col_M1 = col_M1;  col_M1_G = col_M1_G + 1; }
			//else if (col_M1 == 1 && col_M1_G == 1) { col_M1 = col_M1 + 1; col_M1_G = 0; }
			//else { col_M1 = col_M1 + 1; }
			if (col_M1 == HCU_start && col_M1_G == 0)		{ col_M1 = col_M1; col_M1_G = col_M1_G + 1; }
			else if (col_M1 == HCU_start && col_M1_G == 1) { col_M1 = col_M1 + 1; col_M1_G = 0; }
			else if (col_M1 == HCU_end && col_M1_G == 0)	{ col_M1 = col_M1;  col_M1_G = col_M1_G + 1; }
			else if (col_M1 == HCU_end && col_M1_G == 1)	{ col_M1 = col_M1 + 1; col_M1_G = 0; }
			else { col_M1 = col_M1 + 1; }
#endif
#else
					col_M1 = col_M1 + 1;
#endif
				}
				/* 종료 판단 */
				if (col_M1 == m_PCM->N_b)
                    col_M1 = CYCLE_END;
            }
            }
            else {
				if (DU_flag_M1 == TRUE)
					col_M1 = col_M1 + 2;
				else
#if defined(__HALF_COL_UPDATE__)
#if defined(__HACRC_IKD_5B__)
#else
			//if (col_M1 == 0 && col_M1_G == 0) { col_M1 = col_M1; col_M1_G = col_M1_G + 1; }
			//else if (col_M1 == 0 && col_M1_G == 1) { col_M1 = col_M1 + 1; col_M1_G = 0; }
			//else if (col_M1 == 1 && col_M1_G == 0) { col_M1 = col_M1;  col_M1_G = col_M1_G + 1; }
			//else if (col_M1 == 1 && col_M1_G == 1) { col_M1 = col_M1 + 1; col_M1_G = 0; }
			//else { col_M1 = col_M1 + 1; }
			if      (col_M1 == HCU_start && col_M1_G == 0)	{ col_M1 = col_M1;		col_M1_G = col_M1_G + 1; }
			else if (col_M1 == HCU_start && col_M1_G == 1) { col_M1 = col_M1 + 1; col_M1_G = 0; }
			else if (col_M1 == HCU_end && col_M1_G == 0)	{ col_M1 = col_M1;		col_M1_G = col_M1_G + 1; }
			else if (col_M1 == HCU_end && col_M1_G == 1)	{ col_M1 = col_M1 + 1; col_M1_G = 0; }
			else									{ col_M1 = col_M1 + 1; }
#endif
#else
					col_M1 = col_M1 + 1;
#endif
			/* 종료 판단 */
            if (col_M1 == m_PCM->N_b)
                col_M1 = CYCLE_END;
            }
        }
	}
if (CYCLE_END == col_P4) {
	return TRUE;	// 가장 느린 phase인 P4도 모든 column까지 처리한 경우
}
else {
	return FALSE;
}
}
//================================================
// RTL timing 관련 변수를 초기화
//================================================
void Decoder::Clk_Init()
{
#if defined (__ONLY_FOR_DEBUG__)
	cout << "Clk_Init()" << endl;
#endif
	int n;
	int factor = m_PCM->z_sb / PMU_UNIT_SIZE;
	col_M1 = 0; // 시작 column 번호
	col_M1_temp = CYCLE_IDLE;
	col_Z = CYCLE_BEFORE_START;
	col_P1 = CYCLE_BEFORE_START;
	col_P2 = CYCLE_BEFORE_START;
	col_P3 = CYCLE_BEFORE_START;
	col_P4 = CYCLE_BEFORE_START;
	cnt_idle_cycle = 0;
	//for (n = 0; n < m_PCM->J * factor; n++) {
	//  FIFO_level[n] = 0;
	//}
	for (n = 0; n < MAX_DV_GLOBAL_HALF * factor; n++) {
	    FIFO_level[n] = 0;
	}
	Init_Main_SRAM_RQ(TRUE);
	// iter=0에서는 Puncturing Recovery시 Col 0, 1을 skip하고 수행
	// 2SD (3SD) 에서 restart시에는 iter=0에서 Puncturing Recovery를 통해 획득한 복원 bit를 활용
	// col_M1=0부터 시작해서 Syndrome만 계산하면 됨.
#if defined(__HACRC_IKD_5B__)
	if (mn == 0) { col_M1 = 3; }
#else
	//if (mn == 0) { col_M1 = 2; }
	//if (mn == 0 && (m_param_dec->init_n == MODE_DEC_HD)) { col_M1 = 2; }
#endif
	// Half Column Update 반영을 위한 Group 변수 초기화
	col_M1_G = 0;
	col_M1_temp_G = CYCLE_IDLE;
	col_Z_G = CYCLE_BEFORE_START;
	col_P1_G = CYCLE_BEFORE_START;
	col_P2_G = CYCLE_BEFORE_START;
	col_P3_G = CYCLE_BEFORE_START;
	col_P4_G = CYCLE_BEFORE_START;
#if defined (__RUN_ITER34_HIGH_DV_SKIP__)
	if (MODE_DEC_HD == m_param_dec->init_n) {
		//if ((mn == 4 + ITER_MAX_HBF) || (mn == 4)) {
		//if (mn == 4 + ITER_MAX_HBF) {
		if ((mn == 4 + ITER_MAX_HBF) || (mn == 3 + ITER_MAX_HBF)) {
			col_M1 = skip_idx;
		}
	}
#endif
}
//================================================
// RTL timing을 위해 1 clk delay 시키는 부분
//================================================
void Decoder::Clk_Delay_REG()
{
#if defined (__ONLY_FOR_DEBUG__)
	cout << "Clk_Delay_REG()" << endl;
#endif
	int n;
	int factor = m_PCM->z_sb / PMU_UNIT_SIZE;
#if defined(__HALF_COL_UPDATE__)
	int sram_inst_num = factor * MAX_DV_GLOBAL_HALF;
#else
	int sram_inst_num = factor * m_PCM->J;
#endif
	for (n = 0; n < sram_inst_num; n++) {
	    MAIN_SRAM_read_rq2[n] = MAIN_SRAM_read_rq[n];
	}
}
//================================================
// 주어진 phase에서 column은 동작시킬 필요가
// 있는지 판단함
//================================================
int Decoder::Clk_Valid_Col(int phase)
{
	int v = FALSE;
	if (PHASE_M1 == phase) {
	    if ((col_M1 >= 0) && (col_M1 < m_PCM->N_b)) { v = TRUE; }
	}
	else if (PHASE_Z == phase) {
	    if ((col_Z >= 0) && (col_Z < m_PCM->N_b)) { v = TRUE; }
	}
	else if (PHASE_P1 == phase) {
	    if ((col_P1 >= 0) && (col_P1 < m_PCM->N_b)) { v = TRUE; }
	}
	else if (PHASE_P2 == phase) {
	    if ((col_P2 >= 0) && (col_P2 < m_PCM->N_b)) { v = TRUE; }
	}
	else if (PHASE_P3 == phase) {
	    if ((col_P3 >= 0) && (col_P3 < m_PCM->N_b)) { v = TRUE; }
	}
	else if (PHASE_P4 == phase) {
	    if ((col_P4 >= 0) && (col_P4 < m_PCM->N_b)) { v = TRUE; }
	}
	else if (PHASE_PREV2 == phase) {
	    if ((prev_variable_node2_print >= 0) && (prev_variable_node2_print < m_PCM->N_b)) { v = TRUE; }
	}
	return v;
}
//================================================
// SRAM의 read, write request를 초기화한다.
// PMU_Read()와 PMU_Write() 함수에서
// TRUE로 바뀔 수 있음
//================================================
void Decoder::Init_Main_SRAM_RQ(int first)
{
	int n;
	int factor = m_PCM->z_sb / PMU_UNIT_SIZE;
#if defined(__HALF_COL_UPDATE__)
	int sram_inst_num = factor * MAX_DV_GLOBAL_HALF;
#else
	int sram_inst_num = factor * m_PCM->J;
#endif
	for (n = 0; n < sram_inst_num; n++) {
	    MAIN_SRAM_read_rq[n] = FALSE;
	    MAIN_SRAM_write_rq[n] = FALSE;
	}
	if (TRUE == first) {
	    for (n = 0; n < sram_inst_num; n++) {
	        MAIN_SRAM_read_rq2[n] = FALSE;
	    }
	}
}
//================================================
// 현재 iteration이 edge clear를 하는
// iteration인지를 판단하여 맞으면
// TRUE로 return 한다.
//================================================
int Decoder::Is_Iter_Type_Edge_Clear(int iter)
{
	int bClear = FALSE;
#if defined(__AUTO_LLR_OPT__)
	if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
		if (iter == 0 ||
			iter == 1 ||
			iter == ITER_MAX_HBF + 1) {
			bClear = TRUE;
		}
		else {
			for (int i = 0; i < m_param_LLR->restart_num; i++) {
				if (iter == m_param_LLR->restart_iter[i])
					bClear = TRUE;
			}
		}
	}
	else {
	    if (iter == 0) {
	        bClear = TRUE;
	    }
	    else {
	        for (int i = 0; i < m_param_LLR->restart_num; i++) {
	            if (iter == m_param_LLR->restart_iter[i])
	                bClear = TRUE;
	        }
	    }
	}
#else
	if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) { // TLC 용 LLR set 선택 22.01.01 민기
	    if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
	        if (iter == 0 ||
	            iter == 1 || //V2C_Store @iter0: Ref-C 작동, RTL 미작동 ==> 동작차이를 제거하기 위해 Iter 1에서 Edge clear 수행 (KHY, 21.03.23)
	            iter == ITER_MAX_HBF + 1 /*||
	            iter == RSP1_TLC_HD_PRIME_1*/
	            ) {
	            bClear = TRUE;
	        }
	    }
	    else if (MODE_DEC_2SD == m_param_dec->init_n) {
	        if (iter == 0 ||
	            iter == RSP1_2SD_PRIME_1 ||
	            iter == RSP1_2SD_PRIME_2 ) {
	            bClear = TRUE;
	        }
	    }
	    else if (MODE_DEC_3SD == m_param_dec->init_n) {
	        if (iter == 0 ||
	    iter == RSP1_3SD_PRIME_1 ||
	    iter == RSP1_3SD_PRIME_2 ||
	    iter == RSP1_3SD_PRIME_3 ||
	    iter == RSP1_3SD_PRIME_4 ||
	    iter == RSP1_3SD_PRIME_5 ||
	    iter == RSP1_3SD_PRIME_6) {
	    bClear = TRUE;
	}
    }
}
#endif
	return bClear;
}
//================================================
// 현재 iteration이 초기화 하는 (Min값, Edge sgn값, CheckSum값, Synd값(for SD))
// iteration인지를 판단하여 맞으면
// TRUE로 return 한다.
// SD는 Is_Iter_Type_Edge_Clear와 동일
// HD는 Edge clear를 수행할때 초기화 과정이 필요없기에 mn==0에서만 초기화 작업 (Pre-update) 수행
//================================================
int Decoder::Is_Iter_Type_Init(int iter)
{
	int bInit = FALSE;
#if defined(__AUTO_LLR_OPT__)
	if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
	    if (iter == 0) {
	        bInit = TRUE;
	    }
	}
	else {
	    if (iter == 0) {
	        bInit = TRUE;
	    }
	    else {
	        for (int i = 0; i < m_param_LLR->restart_num; i++) {
	            if (iter == m_param_LLR->restart_iter[i])
	                bInit = TRUE;
	        }
	    }
	}
#else
	if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) {  // TLC 용 LLR set 선택 22.01.01 민기
	    if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
	        if (iter == 0) {
	            bInit = TRUE;
	        }
	    }
	    else if (MODE_DEC_2SD == m_param_dec->init_n) {
	        if (iter == 0 ||
#if defined(__4_BIT_LLR__)
	            iter == RSP1_2SD_PRIME_1 ||
	            iter == RSP1_2SD_PRIME_2 ||
	            iter == RSP1_2SD_PRIME_3 ||
	            iter == RSP1_2SD_PRIME_4 ||
	            iter == RSP1_2SD_PRIME_5 ||
	            iter == RSP1_2SD_PRIME_6 ||
	            iter == RSP1_2SD_PRIME_7 ||
	            iter == RSP1_2SD_PRIME_8){
#else
	            iter == RSP1_2SD_PRIME_1 ||
	            iter == RSP1_2SD_PRIME_2) {
#endif
	            bInit = TRUE;
	        }
	    }
	    else if (MODE_DEC_3SD == m_param_dec->init_n) {
	        if (iter == 0||
#if defined(__4_BIT_LLR__)
	            iter == RSP1_3SD_PRIME_1 ||
	            iter == RSP1_3SD_PRIME_2 ||
	            iter == RSP1_3SD_PRIME_3 ||
	            iter == RSP1_3SD_PRIME_4 ||
	            iter == RSP1_3SD_PRIME_5 ||
	            iter == RSP1_3SD_PRIME_6 ||
	            iter == RSP1_3SD_PRIME_7 ||
	            iter == RSP1_3SD_PRIME_8) {
#else
	            iter == RSP1_3SD_PRIME_1 ||
	            iter == RSP1_3SD_PRIME_2 ||
	            iter == RSP1_3SD_PRIME_3 ||
	            iter == RSP1_3SD_PRIME_4 ||
	            iter == RSP1_3SD_PRIME_5 ||
	            iter == RSP1_3SD_PRIME_6) {
#endif
	            bInit = TRUE;
	        }
	    }
	}
#endif
	return bInit;
		}
//================================================
// 마지막 column update 후 CSW를 갱신한다.
//================================================
void Decoder::Set_CSW(int w)
{
	prev_CSW = w;
}
//================================================
// Return Channel LLR
// NOTE: excel로부터 생성한 txt에서 복사해서 사용
// common.h 부분 같이 update 필요
//================================================
void Decoder::Get_VNU_Ch_LLR_Adaptive(int dv, int col_idx, int table_idx, int* ch1, int* ch2, int* ch3, int* ch4)
{
	int dv_idx = 0;
	if (m_ecc_info->matrix_sel == LAYOUT_PRIME_512B_TLC_VSS_OFF) {
	    int Ch_LLR_HD[PRIME_HD_LLR_TABLE_NUM_ROW][PRIME_LLR_TABLE_NUM_DEGREE * 1] = {
#ifdef __4_BIT_LLR__
	        /*{17, 22, 13, 13},
	{12, 11, 12,  8},
	{12, 11, 12,  8},
	{10,  6,  6,  6},
	{ 4,  4,  4,  4},
	{ 2,  2,  2,  2},
	{24, 19, 15, 12},
	{24, 29, 12, 16},
	{ 8, 10, 12,  8},
	{14,  6,  6,  6},
	{ 8,  4,  4,  4},
	{ 9,  2,  2,  2},
	{27, 20, 15, 14},
	{12, 11, 12,  8},
	{14,  6,  6,  6},
	{ 3,  4,  4,  4},
	{ 3,  4,  4,  4},
	{ 2,  2,  2,  2},
	{11, 10, 12, 15},
	{11, 10, 12, 15},
	{ 8,  7,  7,  9},
	{ 3,  6,  5,  4},
	{19,  1,  3,  3},
	{23,  0,  2,  2},
	{11, 10, 12, 15},
	{ 8,  7,  7,  9},
	{ 3,  6,  5,  4},
	{19,  1,  3,  3},
	{23,  0,  2,  2},
	{10, 10, 10, 10},
	{ 9,  8,  8,  8},
	{ 4,  8,  8,  8},
	{10,  4,  4,  4},
	{20,  2,  2,  2},
	{11, 11, 12, 14},
	{ 7,  9, 10, 10},
	{ 4,  8,  8,  8},
	{ 2,  8,  6,  6},
	{24,  6,  4,  4},
	{26,  9,  2,  2}*/
	{17,     22, 13, 13},
	{10,     15, 19, 16},
	{12,     11, 12,  8},
	{10,      6,  6,  6},
	{4,  4,   4,  4},
	{2,  2,   2,  2},
	{24,     19, 15, 12},
	{24,     29, 12, 16},
	{8, 10, 12,  8},
	{14,      6,  6,  6},
	{8,  4,   4,  4},
	{9,  2,   2,  2},
	{27,     20, 15, 14},
	{12,     11, 12,  8},
	{14,      6,  6,  6},
	{3,  4,   4,  4},
	{3,  4,   4,  4},
	{2,  2,   2,  2},
	{11,     10, 12, 15},
	{11,     10, 12, 15},
	{8,  7,   7,  9},
	{3,  5,   5,  4},
	{19,      1,  3,  3},
	{23,      0,  2,  2},
	{11,     10, 12, 15},
	{8,  7,   7,  9},
	{3,  5,   5,  4},
	{19,      1,  3,  3},
	{23,      0,  2,  2},
	{10,     10, 10, 10},
	{9,  8,   8,  7},
	{13,      5,  6,  6},
	{10,      4,  4,  4},
	{20,      2,  2,  4},
	{11,     11, 10, 13},
	{8,  9,   9, 10},
	{4,  8,   8,  8},
	{2,  7,   6,  7},
	{24,      5,  4,  5},
	{26,      9,  1,  2}
#else
	
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10},
    {21, 14, 12, 10}
#endif // __4_BIT_LLR__
	};
        int Ch_LLR_2SD[PRIME_2SD_LLR_TABLE_NUM_ROW][PRIME_LLR_TABLE_NUM_DEGREE * 2] = {

#ifdef __4_BIT_LLR__
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4}
#else
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4},
            {15, 4, 15, 4, 17, 5, 13, 4}
#endif
        };
        int Ch_LLR_3SD[PRIME_3SD_LLR_TABLE_NUM_ROW][PRIME_LLR_TABLE_NUM_DEGREE * 4];
#ifdef __4_BIT_LLR__
        if (dv >= 5)	dv_idx = PRIME_LLR_TABLE_IDX_DV12;
	    else if (dv == 4)	dv_idx = PRIME_LLR_TABLE_IDX_DV4;
	    else if (dv == 3)	dv_idx = PRIME_LLR_TABLE_IDX_DV3;
	    else if (dv <= 2)	dv_idx = PRIME_LLR_TABLE_IDX_DV2;
#else
	    if (dv >= 8)	dv_idx = PRIME_LLR_TABLE_IDX_MAXDV;
	    else if (dv >= 5)	dv_idx = PRIME_LLR_TABLE_IDX_MIDDV;
	    else if (dv == 4)	dv_idx = PRIME_LLR_TABLE_IDX_DV4;
	    else if (dv == 3)	dv_idx = PRIME_LLR_TABLE_IDX_DV3;
	    else if (dv <= 2)	dv_idx = PRIME_LLR_TABLE_IDX_DV2;
#endif // __4_BIT_LLR__
#ifdef __LLR_PUNCT_TO_DV2__
	    if (col_idx < 2)
	        dv_idx = PRIME_LLR_TABLE_IDX_DV2;
#endif // __LLR_PUNCT_TO_DV2__
	if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
	    *ch1 = Ch_LLR_HD[table_idx][dv_idx];
	    *ch2 = 0;
	    *ch3 = 0;
	    *ch4 = 0;
	}
	else if (MODE_DEC_2SD == m_param_dec->init_n) {
	    *ch1 = Ch_LLR_2SD[table_idx][dv_idx * 2];
	    *ch2 = Ch_LLR_2SD[table_idx][dv_idx * 2 + 1];
	    *ch3 = 0;
	    *ch4 = 0;
	}
	else if (MODE_DEC_3SD == m_param_dec->init_n) {
	    *ch1 = Ch_LLR_3SD[table_idx][dv_idx * 4];
	    *ch2 = Ch_LLR_3SD[table_idx][dv_idx * 4 + 1];
	    *ch3 = Ch_LLR_3SD[table_idx][dv_idx * 4 + 2];
	    *ch4 = Ch_LLR_3SD[table_idx][dv_idx * 4 + 3];
	}
}
#if defined (__ONLY_FOR_DEBUG__)
	cout << "Get_VNU_Ch_LLR_Adaptive() ==> " << dv << ", " << table_idx << ", " << prev_CSW << " ==> th :  " << *ch1 << ", " << *ch2 << ", " <<
	cout << endl;
#endif
}
int Decoder::Get_Cur_LLR_Idx_FILE(int iter) {
	int table_row_idx = 0;
	int start_idx = 0;
	int end_idx = 0;
	int selected_group = -1;
	int i, g;
	int num_candidate;
	if (m_param_dec->init_n == MODE_DEC_HD && iter > 0) {
	    //Adjust_HD_Floor_Type(m_param_LLR->CSW_thr[m_param_LLR->num_row - 2], m_param_LLR->CSW_thr[m_param_LLR->num_row - 3]);
	    Adjust_HD_Floor_Type(Floor_Detect_CSW_TH1, Floor_Detect_CSW_TH2);
	}
#if defined (__AUTO_LLR_OPT__)
	for (g = m_param_LLR->num_group - 1; g >= 0; g--) {
	    start_idx = 0;
	    for (int gg = 0; gg < g; gg++) {
	        start_idx += m_param_LLR->num_set_each_group[gg];
	    }
	    end_idx = 0;
	    for (int gg = 0; gg <= g; gg++) {
	        end_idx += m_param_LLR->num_set_each_group[gg];
	    }
	    end_idx = end_idx - 1;
	    if ((iter >= m_param_LLR->iter_start[start_idx]) && (iter <= m_param_LLR->iter_end[end_idx])) {
	        selected_group = g;
	        break;
	    }
	}
#else
	if ((m_param_dec->init_n == MODE_DEC_HD) && (iter == 1)) {
	    if (FLAG_HD_1_4_SET_TYPE_0 == flag_HD_1_4_Set)
	        selected_group = 0;
	}
	else if ((m_param_dec->init_n == MODE_DEC_HD) && (iter >= 2) && (iter <= 4)) {
	    if (FLAG_HD_1_4_SET_TYPE_0 == flag_HD_1_4_Set)
	        selected_group = 1;
	}
	else if ((m_param_dec->init_n == MODE_DEC_HD) && (iter == 5)) {
	    if (FLAG_HD_5_8_SET_TYPE_0 == flag_HD_5_8_Set)
	        selected_group = 2;
	    else
	        selected_group = 4;
	}
	else if ((m_param_dec->init_n == MODE_DEC_HD) && (iter >= 6) && (iter <= 8)) {
	    if (FLAG_HD_5_8_SET_TYPE_0 == flag_HD_5_8_Set)
	        selected_group = 3;
	    else
	        selected_group = 5;
	}
	else {
	    for (g = m_param_LLR->num_group - 1; g >= 0; g--) {
	        start_idx = 0;
	        for (int gg = 0; gg < g; gg++) {
	            start_idx += m_param_LLR->num_set_each_group[gg];
	        }
	        end_idx = 0;
	        for (int gg = 0; gg <= g; gg++) {
	            end_idx += m_param_LLR->num_set_each_group[gg];
	        }
	        end_idx = end_idx - 1;
	        if ((iter >= m_param_LLR->iter_start[start_idx]) && (iter <= m_param_LLR->iter_end[end_idx])) {
	            selected_group = g;
	            break;
	        }
	    }
	}
	start_idx = 0;
	for (int gg = 0; gg < selected_group; gg++) {
	    start_idx += m_param_LLR->num_set_each_group[gg];
	}
	end_idx = 0;
	for (int gg = 0; gg <= selected_group; gg++) {
	    end_idx += m_param_LLR->num_set_each_group[gg];
	}
	end_idx = end_idx - 1;
#endif // __AUTO_LLR_OPT__
	if (selected_group == -1 || selected_group >= m_param_LLR->num_group) {
	    printf("[Error] @Cur_LLR_IDX (1): iter%d, state%d, CSW%d\n", iter, state_hd_error_floor_set, prev_CSW);
	}
	if (GROUP_TYPE_ITER == m_param_LLR->type_each_group[selected_group]) {
	    for (i = start_idx; i <= end_idx; i++) {
	        if ((iter >= m_param_LLR->iter_start[i]) && (iter <= m_param_LLR->iter_end[i])) {
	            table_row_idx = i;
	            break;
	        }
	    }
	}
	else if (GROUP_TYPE_CSW == m_param_LLR->type_each_group[selected_group]) {
	    table_row_idx = start_idx;
	    num_candidate = m_param_LLR->num_set_each_group[selected_group];
	    for (i = num_candidate - 1; i > 0; i--) {
	        if (prev_CSW <= m_param_LLR->CSW_thr[start_idx + i]) {
	            table_row_idx = start_idx + i;
	            break;
	        }
	    }
	}
	if (table_row_idx < 0 || table_row_idx >= m_param_LLR->num_row) {
	    printf("[Error] @Cur_LLR_IDX (2): iter%d, state%d, CSW%d, table_row%d\n", iter, state_hd_error_floor_set, prev_CSW, table_row_idx);
	}
	return table_row_idx;
}
void Decoder::Get_VNU_LLR_SET_FILE(int dv, int col_idx, int table_row_idx, int* ch1, int* ch2, int* ch3, int* ch4, int* th1, int* th2, int* th3, int* th4, int* th5, int* th6, int* th7){
	int table_col_idx = 0;
	int i;
	//
	for (i = 0; i < m_param_LLR->num_dv; i++) {
	    if ((dv >= m_param_LLR->dv_from[i]) && (dv <= m_param_LLR->dv_to[i])) {
	        table_col_idx = i * m_param_LLR->num_para_each_set;
	        break;
	    }
	}
#if defined(__LLR_TWO_DV3__)
	if (dv == 3 && col_idx < 88)
	    table_col_idx = table_col_idx - m_param_LLR->num_para_each_set;
#endif
	if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
	    *ch1 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx];
	    *ch2 = 0;
	    *ch3 = 0;
	    *ch4 = 0;
	    *th1 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 1];
	    *th2 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 2];
	    *th3 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 3];
#if defined(__4_BIT_LLR__)
	    *th4 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 4];
	    *th5 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 5];
	    *th6 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 6];
	    *th7 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 7];
#endif
	}
	else if (MODE_DEC_2SD == m_param_dec->init_n) {
	    *ch1 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx];
	    *ch2 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 1];
	    *ch3 = 0;
	    *ch4 = 0;
	    *th1 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 2];
	    *th2 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 3];
	    *th3 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 4];
#if defined(__4_BIT_LLR__)
	    *th4 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 5];
	    *th5 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 6];
	    *th6 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 7];
	    *th7 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 8];
#endif
	}
	else if (MODE_DEC_3SD == m_param_dec->init_n) {
	    *ch1 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx];
	    *ch2 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 1];
	    *ch3 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 2];
	    *ch4 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 3];
	    *th1 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 4];
	    *th2 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 5];
	    *th3 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 6];
#if defined(__4_BIT_LLR__)
	    *th4 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 7];
	    *th5 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 8];
	    *th6 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 9];
	    *th7 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx + 10];
#endif
	}
}
//================================================
// Return VNU_out threshold
// NOTE: excel로부터 생성한 txt에서 복사해서 사용
// common.h 부분 같이 update 필요
//================================================
void Decoder::Get_VNU_Th_Adaptive(int dv, int col_idx, int table_idx, int* th1, int* th2, int* th3, int* th4, int* th5, int* th6, int* th7)
{
	int dv_idx = 0;
	if (m_ecc_info->matrix_sel == LAYOUT_PRIME_512B_TLC_VSS_OFF) {
        int table_HD[PRIME_HD_LLR_TABLE_NUM_ROW][PRIME_LLR_TABLE_NUM_DEGREE * PRIME_LLR_TABLE_NUM_TH];
        int table_2SD[PRIME_2SD_LLR_TABLE_NUM_ROW][PRIME_LLR_TABLE_NUM_DEGREE * PRIME_LLR_TABLE_NUM_TH];
        int table_3SD[PRIME_3SD_LLR_TABLE_NUM_ROW][PRIME_LLR_TABLE_NUM_DEGREE * PRIME_LLR_TABLE_NUM_TH];

#ifdef __4_BIT_LLR__
        if (dv >= 5) dv_idx = PRIME_LLR_TABLE_IDX_DV12;
        else if (dv == 4) dv_idx = PRIME_LLR_TABLE_IDX_DV4;
        else if (dv == 3) dv_idx = PRIME_LLR_TABLE_IDX_DV3;
        else if (dv <= 2) dv_idx = PRIME_LLR_TABLE_IDX_DV2;
#else
    if (dv >= 8) dv_idx = PRIME_LLR_TABLE_IDX_MAXDV;
	else if (dv >= 5)    dv_idx = PRIME_LLR_TABLE_IDX_MIDDV;
	else if (dv == 4)    dv_idx = PRIME_LLR_TABLE_IDX_DV4;
	else if (dv == 3)    dv_idx = PRIME_LLR_TABLE_IDX_DV3;
	else if (dv <= 2)    dv_idx = PRIME_LLR_TABLE_IDX_DV2;
#endif // __4_BIT_LLR__
#ifdef __LLR_PUNCT_TO_DV2__
	if (col_idx < 2)
		dv_idx = PRIME_LLR_TABLE_IDX_DV2;
#endif // __LLR_PUNCT_TO_DV2__
	if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
	    *th1 = table_HD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH];
	    *th2 = table_HD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 1];
	    *th3 = table_HD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 2];
#if defined (__4_BIT_LLR__)
	    *th4 = table_HD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 3];
	    *th5 = table_HD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 4];
	    *th6 = table_HD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 5];
	    *th7 = table_HD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 6];
#endif
	}
	else if (MODE_DEC_2SD == m_param_dec->init_n) {
	    *th1 = table_2SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH];
	    *th2 = table_2SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 1];
	    *th3 = table_2SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 2];
#if defined (__4_BIT_LLR__)
	    *th4 = table_2SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 3];
	    *th5 = table_2SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 4];
	    *th6 = table_2SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 5];
	    *th7 = table_2SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 6];
#endif
	}
	else if (MODE_DEC_3SD == m_param_dec->init_n) {
	    *th1 = table_3SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH];
	    *th2 = table_3SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 1];
	    *th3 = table_3SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 2];
#if defined (__4_BIT_LLR__)
	    *th4 = table_3SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 3];
	    *th5 = table_3SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 4];
	    *th6 = table_3SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 5];
	    *th7 = table_3SD[table_idx][dv_idx * PRIME_LLR_TABLE_NUM_TH + 6];
#endif
	    }
	}
#if defined (__ONLY_FOR_DEBUG__)
	cout << "Get_VNU_Th_Adaptive()    ==> " << dv << ", " << table_idx << ", " << prev_CSW << " ==> th : " << *th1 << ", " << *th2 << ", " << *th3;
	cout << endl;
#endif
}
//==============================================
// Decoding status에 맞는 table index return
// NOTE: excel로부터 생성한 txt에서 복사해서 사용
// common.h 부분 같이 update 필요
//==============================================
int Decoder::Get_VNU_Table_Idx(int iter)
{
    return 0;
}
//=============================================
// Puncturing이 적용된 information column을
// 미리 한 번 update한다.
//=============================================
void Decoder::Preprocessing()
{
    /* last info column (punctured) */
    //cur_variable_node = 0;
    cur_variable_node = m_PCM->N_b - m_PCM->M_b - 3;
    col_P2 = cur_variable_node;
    C2V_cal(col_P2);
    V2C_Cal(col_P2);
    Delay_2clk(FALSE);
    Delay_2clk(FALSE);
    V2C_Store(prev_variable_node2, TRUE);
    /* ??? */
    cur_variable_node = m_PCM->N_b - m_PCM->M_b - 2;
    col_P2 = cur_variable_node;
    C2V_cal(col_P2);
    V2C_Cal(col_P2);
    Delay_2clk(FALSE);
    Delay_2clk(FALSE);
    V2C_Store(prev_variable_node2, TRUE);
    /* initialize */
    Clk_Init();
}
//=============================================
// Effective iteration 수를 return 한다.
//=============================================
int  Decoder::Get_Real_MN()
{
    return real_mn;
}
//=============================================
// Full CRC 매 iteration 결과를 모은 pointer
// return 한다. (VSS + ECC Top TV 용)
//=============================================
int* Decoder::Get_CRC_LFSR_iter()
{
    return crc_dec_LFSR_iter;
}
//=============================================
// jj번째 column에 포함된 error 수를 count한다.
//=============================================
int Decoder::Count_Error_Bit_Column(int  jj)
{
    int en = 0;
    int q;
    int offset = jj * m_PCM->z_sb;
    int bit_pos;
    for (q = 0; q < m_PCM->z_sb; q++) {
        bit_pos = offset + q;
        if (cwc[bit_pos] != m_genie_inv_cw[bit_pos]) {
            en++;
        }
    }
    return en;
}
//=============================================
// Codeword 전체와 DATA 영역에 (LCRC 제외)
// bit error 수를 count한다.
//=============================================
void Decoder::Count_Error_Bit(int* cw, int* info)
{
    int en_info = 0;
    int en_cw = 0;
    int q;
    for (q = 0; q < m_PCM->N; q++) {
        if (cwc[q] != m_genie_inv_cw[q]) {
            en_cw++;
            if (q < m_ecc_info->bit_pos.info_end) {
                en_info++;
            }
        }
    }
    *cw = en_cw;
    *info = en_info;
}
//=============================================
// Checksum weight를 계산한다.
// 순수 4KB LDPC 부분만 count
//=============================================
int Decoder::Compute_CSW()
{
    int check_sum_prime = 0;
    int cur_chk_sum_weight = 0;
    int num_CN = 0;
    num_CN = m_PCM->M;
    for (int i = 0; i < num_CN; i++) {
        check_sum_prime = (Check_REG[i][IDX_CHECK_SUM] + Syndrome[i]) % 2;
        if (check_sum_prime == 1)    cur_chk_sum_weight++;
    }
    return cur_chk_sum_weight;
}
//=============================================
// Syndrome weight를 계산한다.
// Preupdate 직후의 경우 마지막 row block은
// 포함하지 않는다.
//=============================================
int Decoder::Compute_SW(int bPreudate)
{
    int num = 0;
    int idx_cn;
    int cn_block;
    int synd_val = 0;
    int sub_idx;
    if (TRUE == bPreudate) {
        for (int j = 0; j < m_PCM->M - m_PCM->z_sb; j++) {
            if (Syndrome[j] == 1) num++;
        }
    }
    else {
        for (idx_cn = 0; idx_cn < m_PCM->M; idx_cn++) {
            cn_block = idx_cn / m_PCM->z_sb;
            synd_val = 0;
            for (sub_idx = 0; sub_idx < m_PCM->RowW[cn_block]; sub_idx++) {
                if (mn == 0) {
                    synd_val += Variable_mem[m_PCM->C_net[idx_cn][sub_idx]];
                }
                else {
                    synd_val += cwc[m_PCM->C_net[idx_cn][sub_idx]];
                }
            }
            if ((synd_val % 2) != 0) { num++; }
        }
    }
    return num;
}
#ifdef __AUTO_LLR_OPT__
int Decoder::Compute_CSW_Auto()
{
    int check_sum_prime = 0;
    int cur_chk_sum_weight = 0;
    int num_CN = 0;
    num_CN = m_PCM->M;
    for (int i = 0; i < num_CN; i++) {
        check_sum_prime = (Check_REG[i][IDX_CHECK_SUM] + Syndrome[i]) % 2;
        if (check_sum_prime == 1)    cur_chk_sum_weight++;
    }
    return cur_chk_sum_weight;
}
#endif // __AUTO_LLR_OPT__
int Decoder::Compute_PSW(int bPreudate)
{
    int num = 0;
    int idx_cn;
    int cn_block;
    int synd_val = 0;
    int sub_idx;
    int temp;
    if (TRUE == bPreudate) {
        for (int j = 0; j < m_PCM->M - m_PCM->z_sb; j++) {
            cn_block = j / m_PCM->z_sb;
            temp = m_PCM->PCM_b[cn_block][0];
            if (temp == -1) {
                if (Syndrome[j] == 1)  num++;
            }
        }
    }
    else {
        for (idx_cn = 0; idx_cn < m_PCM->M; idx_cn++) {
            cn_block = idx_cn / m_PCM->z_sb;
            synd_val = 0;
            temp = m_PCM->PCM_b[cn_block][0];
            if (temp == -1) {
                for (sub_idx = 0; sub_idx < m_PCM->RowW[cn_block]; sub_idx++) {
                    if (mn == 0) {
                        synd_val += Variable_mem[m_PCM->C_net[idx_cn][sub_idx]];
                    }
                    else {
                        synd_val += cwc[m_PCM->C_net[idx_cn][sub_idx]];
                    }
                }
                if ((synd_val % 2) != 0) { num++; }
            }
        }
    }
    return num;
}
void Decoder::Compute_Err_In_CN(int row_blk, int* err_sum, int* max, int* min1_v)
{
    int idx_cn;
    int idx_vn;
    int num;
    int tot_num_in_blk = 0; // 해당 row block와 연결된 error가 있는 VN 수
    int max_err_num = 0;
    int min1_value = 0;
    for (int j = 0; j < m_PCM->z_sb; j++) {
        num = 0;
        idx_cn = row_blk * m_PCM->z_sb + j;
        for (int sub_idx = 0; sub_idx < m_PCM->RowW[row_blk]; sub_idx++) {
            idx_vn = m_PCM->C_net[idx_cn][sub_idx];
            if (cwc[idx_vn] != m_genie_inv_cw[idx_vn]) {
                num++;
            }
        }
        tot_num_in_blk += num;
        if (num > max_err_num) {
            max_err_num = num;
            min1_value = REG_min1_value[idx_cn];
        }
    }
    *err_sum = tot_num_in_blk;
    *max = max_err_num;
    *min1_v = min1_value;
}
int Decoder::Compute_Min1_Sum()
{
    int min1_sum = 0;
    int num_CN = 0;
    num_CN = m_PCM->M;
    for (int i = 0; i < num_CN; i++) {
        min1_sum += REG_min1_value[i];
    }
    return min1_sum;
}
int Decoder::Compute_Min2_Sum()
{
    int min2_sum = 0;
    int num_CN = 0;
    num_CN = m_PCM->M;
    for (int i = 0; i < num_CN; i++) {
        min2_sum += REG_min2_value[i];
    }
    return min2_sum;
}
int Decoder::Compute_Min1_Sum_MSB()
{
    int min1_sum = 0;
    int num_CN = 0;
    num_CN = m_PCM->M;
    for (int i = 0; i < num_CN; i++) {
        if (REG_min1_value[i] >= 2) {
            min1_sum++;
        }
    }
    return min1_sum;
}
//=================================================
// SRAM 충돌용 FIFO의 log를 출력한다.
//=================================================
void Decoder::Print_Log_FIFO(int end, int PCRC)
{
    int i;
    int factor = m_PCM->z_sb / PMU_UNIT_SIZE;
    //int PMU_inst_num = factor * MAX_DV_GLOBAL;
    int PMU_inst_num = factor * MAX_DV_GLOBAL_HALF;
    FILE* fp = fopen("fifo_level.dat", "a");
    if (TRUE == end) {
        fprintf(fp, "\n");
    }
    else {
        if (FALSE == flag_parity_skip) {
            fprintf(fp, "%3d\t%3d\t%3d\t", mn, prev_variable_node2_print, col_P1);
            for (i = 0; i < PMU_inst_num; i++) { fprintf(fp, "%d", MAIN_SRAM_write_rq[i]); }
            fprintf(fp, " ");
            if (FALSE == PCRC) {
                for (i = 0; i < PMU_inst_num; i++) { fprintf(fp, "%d", MAIN_SRAM_read_rq2[i]); }
                fprintf(fp, " ");
            }
            else {
                for (i = 0; i < PMU_inst_num; i++) { fprintf(fp,  "0" ); }
                fprintf(fp, " ");
            }
            for (i = 0; i < PMU_inst_num; i++) { fprintf(fp, "%d", FIFO_level[i]); }
            fprintf(fp, "\n");
        }
    }
    fclose(fp);
}
//=============================================
// Power stopping log를 출력한다.
//=============================================
void Decoder::Print_Log_Power_Stopping(int end)
{
    FILE* fp = fopen("power_stopping.dat", "a");
    if (FALSE == flag_parity_skip) {
        if (TRUE == end) {
            fprintf(fp, "\n");
        }
        else {
            fprintf(fp, "%3d\t%3d\t%3d\t%3d\t%3d\t", mn, prev_variable_node2_print, col_P4, col_P2, col_P1);
            if (TRUE == pre_Force_stopping) {
                fprintf(fp, "ON\t%d\t%4d\n", Force_stopping, Error_count_reg);
            }
            else {
                fprintf(fp, "  \t%d\t%4d\n", Force_stopping, Error_count_reg);
            }
        }
    }
    fclose(fp);
}
//=============================================
// 분석용 log 파일을 생성한다.
//=============================================
void Decoder::Open_Log_Files()
{
#if defined (__LOG_DECODING_STATUS__)
    fp_log_bit_err_col = fopen("log_bit_err_column.dat", "a");
    fp_log_err_dv = fopen("log_bit_err_dv.dat", "a");
    fp_log_bit_err = fopen("log_bit_err.dat", "a");
    fp_log_SW = fopen("log_SW.dat", "a");
    fp_log_PSW = fopen("log_PSW.dat", "a");
    fp_log_CSW = fopen("log_CSW.dat", "a");
    fp_log_min1 = fopen("log_min1.dat", "a");
    fp_log_min2 = fopen("log_min2.dat", "a");
    fp_log_min_pos = fopen("log_min_pos.dat", "a");
    fp_log_check_sum = fopen("log_check_sum.dat", "a");
    fp_log_punc = fopen("log_punc.dat", "a");
    fp_log_LLR_idx = fopen("log_LLR_idx.dat", "a");
#endif
#if defined (__AUTO_LLR_OPT__)
    if (m_param_dec->flag_print_CSW_log) {
        char fn_CSW[LEN_FILENAME];
        sprintf(fn_CSW, "log_CSW_%d.txt", m_param_dec->rank_supercom);
        fp_log_CSW_auto = fopen(fn_CSW, "a");
    }
#endif
}
//=============================================
// 분석용 log 파일을 닫는다.
//=============================================
void Decoder::Close_Log_Files()
{
#if defined (__LOG_DECODING_STATUS__)
    fclose(fp_log_bit_err_col);
    fclose(fp_log_bit_err);
    fclose(fp_log_err_dv);
    fclose(fp_log_SW);
    fclose(fp_log_PSW);
    fclose(fp_log_CSW);
    fclose(fp_log_min1);
    fclose(fp_log_min2);
    fclose(fp_log_min_pos);
    fclose(fp_log_check_sum);
    fclose(fp_log_punc);
    fclose(fp_log_LLR_idx);
#endif
#if defined (__AUTO_LLR_OPT__)
    if (m_param_dec->flag_print_CSW_log) {
        fclose(fp_log_CSW_auto);
    }
#endif
}
//=============================================
// 분석용 log 파일을 출력한다.
//=============================================
void Decoder::Print_Log_Files()
{
#if defined (__LOG_DECODING_STATUS__)
    Print_Log_Bit_Err_Col(fp_log_bit_err_col);
    Print_Log_Bit_Err(fp_log_bit_err);
    Print_Log_Err_Dv(fp_log_err_dv);
    Print_Log_SW(fp_log_SW);
    Print_Log_PSW(fp_log_PSW);
    Print_Log_CSW(fp_log_CSW);
    Print_Log_Punc(fp_log_punc);
    Print_Log_LLR_Idx(fp_log_LLR_idx);
    Print_Log_Min1(fp_log_min1);
    Print_Log_Min2(fp_log_min2);
    Print_Log_Check_Sum_First_Row(fp_log_check_sum);
    Print_Log_Min_Pos_First_Row(fp_log_min_pos);
#endif
#if defined (__AUTO_LLR_OPT__)
    if (m_param_dec->flag_print_CSW_log) {
        Print_Log_CSW_Auto(fp_log_CSW_auto);
    }
#endif
}
void Decoder::Padding_Zero_Log(int iter, int CRC_flag)
{
#if defined (__LOG_DECODING_STATUS__)
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    int N_b = m_PCM->N_b;
    if (FALSE == CRC_flag) {
        for (int i = iter + 1; i < MN_size; i++) {
            m_log_bit_err[i] = 0;
            m_log_punct_bit_err[i] = 0;
            m_log_CSW[i] = 0;
            m_log_SW[i] = 0;
            for (int jj = 0; jj < N_b; jj++) {
                m_log_bit_err_col[i][jj] = 0;
            }
        }
    }
#endif
}
void Decoder::Print_CRC_result(int end_pos)
{
#if defined (__LOG_DECODING_STATUS__)
    fp_log_CRC = fopen("log_crc.dat", "a");
    fprintf(fp_log_CRC, "%5d\t%3d\t%d\n", m_sector_idx, mn, end_pos);
    fclose(fp_log_CRC);
#endif
}
void Decoder::Print_Log_Sum_T(int show_type)
{
    int bit_pos;
    int dv;
    FILE* fp = fopen("sum_t.dat", "a");
    int offset;
    int pass;
    for (int col = 0; col < m_PCM->N_b; col++) {
        dv = m_PCM->ColW[col];
        offset = col * m_PCM->z_sb;
        for (int j = 0; j < m_PCM->z_sb; j++) {
            bit_pos = offset + j;
            if (LOG_SHOW_TYPE_ERR == show_type && cwc[bit_pos] != m_genie_inv_cw[bit_pos])
                pass = TRUE;
            else if (LOG_SHOW_TYPE_ALL == show_type)
                pass = TRUE;
            else if (LOG_SHOW_TYPE_ONE == show_type && j == 0)
                pass = TRUE;
            else
                pass = FALSE;
            if (TRUE == pass) {
                fprintf(fp, "%5d\t%3d\t%d\t%3d\t%5d\t", m_sector_idx, mn, dv, col, bit_pos);
                fprintf(fp, "%d\n", m_log_sum_t[bit_pos]);
            }
        }
    }
    fclose(fp);
}
//=============================================
// 분석용 log로 VNU_in을 출력한다.
// col번째 block의 VN의 VNU_in
//=============================================
void Decoder::Print_Log_VNU_in(int show_type)
{
    int bit_pos;
    int dv;
    int offset;
    int cnt_plus;
    int cnt_minus;
    int pass;
    FILE* fp = fopen("vnu_in.dat", "a");
    for (int col = 0; col < m_PCM->N_b; col++) {
        dv = m_PCM->ColW[col];
        offset = col * m_PCM->z_sb;
        for (int j = 0; j < m_PCM->z_sb; j++) {
            bit_pos = offset + j;
            if (LOG_SHOW_TYPE_ERR == show_type && cwc[bit_pos] != m_genie_inv_cw[bit_pos]) //Err만
                pass = TRUE;
            else if (LOG_SHOW_TYPE_ALL == show_type) // All
                pass = TRUE;
            else if (LOG_SHOW_TYPE_ONE == show_type && j == 0) //각 block당 첫번째만
                pass = TRUE;
            else
                pass = FALSE;
            if (TRUE == pass) {
                cnt_plus = 0;
                cnt_minus = 0;
                fprintf(fp, "%5d\t%3d\t%3d\t%3d\t%5d\t", m_sector_idx, mn, dv, col, bit_pos);
                fprintf(fp, "%d\t", m_log_ch_llr[bit_pos]);
                for (int k = 0; k < m_PCM->J; k++) {
                    fprintf(fp, "%d\t", m_log_VNU_in[k][bit_pos]);
                    if (m_log_VNU_in[k][bit_pos] > 0)    cnt_plus++;
                    else if (m_log_VNU_in[k][bit_pos] < 0) cnt_minus++;
                }
                fprintf(fp, "%d\t%d", cnt_plus, cnt_minus);
                fprintf(fp, "\n");
            }
        }
    }
    fclose(fp);
}
//=============================================
// 분석용 log로 VNU_out을 출력한다.
// col번째 block의 VN의 VNU_out
//=============================================
void Decoder::Print_Log_VNU_out(int show_type)
{
    int bit_pos;
    int dv;
    int pass;
    int offset;
    FILE* fp = fopen("vnu_out.dat", "a");
    for (int col = 0; col < m_PCM->N_b; col++) {
        dv = m_PCM->ColW[col];
        offset = col * m_PCM->z_sb;
        for (int j = 0; j < m_PCM->z_sb; j++) {
            bit_pos = offset + j;
            if (LOG_SHOW_TYPE_ERR == show_type && cwc[bit_pos] != m_genie_inv_cw[bit_pos])
                pass = TRUE;
            else if (LOG_SHOW_TYPE_ALL == show_type)
                pass = TRUE;
            else if (LOG_SHOW_TYPE_ONE == show_type && j == 0)
                pass = TRUE;
            else
                pass = FALSE;
            if (TRUE == pass) {
                fprintf(fp, "%5d\t%3d\t%3d\t%d\t%3d\t%5d\t", m_sector_idx, mn, clk_copy, dv, col, bit_pos);
                for (int k = 0; k < m_PCM->J; k++) {
                    fprintf(fp, "%d\t", m_log_VNU_out[k][bit_pos]);
                }
                fprintf(fp, "\n");
            }
        }
    }
    fclose(fp);
}
//=============================================
// Sector의 decoding log 배열 초기화
//=============================================
void Decoder::Init_Log_Data()
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    int N_b = m_PCM->N_b;
    int M_b = m_PCM->M_b;
    int z_sb = m_PCM->z_sb;
    for (int i = 0; i < MN_size; i++) {
        m_log_bit_err[i] = -1;
        m_log_punct_bit_err[i] = -1;
        /* column */
        for (int j = 0; j < N_b; j++) {
            m_log_bit_err_col[i][j] = -1;
        }
        /* row */
        for (int j = 0; j < M_b; j++) {
            m_log_min1_sum[i][j] = 0;
            m_log_min2_sum[i][j] = 0;
        }
        for (int j = 0; j < z_sb; j++) {
            m_log_check_sum_first_row[i][j] = 0;
            m_log_min_pos_first_row[i][j] = 0;
        }
        m_log_CSW[i] = -1;
        m_log_SW[i] = -1;
        m_log_PSW[i] = -1;
        m_log_LLR_idx[i] = 0;
#ifdef __AUTO_LLR_OPT__
        m_log_CSW_auto[i] = -1;
#endif // __AUTO_LLR_OPT__
    }
}
//=============================================
// Sector의 decoding log 배열 생성
//=============================================
void Decoder::Alloc_Log_Data()
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    int N_b = m_PCM->N_b;
    int M_b = m_PCM->M_b;
    int z_sb = m_PCM->z_sb;
    m_log_bit_err = new int[MN_size];
    m_log_CSW = new int[MN_size];
    m_log_bit_err_col = new int*[MN_size];
    m_log_min1_sum = new int*[MN_size];
    m_log_min2_sum = new int*[MN_size];
    m_log_check_sum_first_row = new int*[MN_size];
    m_log_min_pos_first_row = new int*[MN_size];
    m_log_punct_bit_err = new int[MN_size];
    m_log_SW = new int[MN_size];
    m_log_PSW = new int[MN_size];
    m_log_LLR_idx = new int[MN_size];
    for (int i = 0; i < MN_size; i++) {
        m_log_bit_err_col[i] = new int[N_b];
        m_log_min1_sum[i] = new int[M_b];
        m_log_min2_sum[i] = new int[M_b];
        m_log_check_sum_first_row[i] = new int[z_sb];
        m_log_min_pos_first_row[i] = new int[z_sb];
    }
#ifdef __AUTO_LLR_OPT__
    m_log_CSW_auto = new int[MN_size];
#endif // __AUTO_LLR_OPT__
}
//=============================================
// Sector의 decoding log 배열 삭제
//=============================================
void Decoder::Release_Log_Data()
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    for (int i = 0; i < MN_size; i++) {
        /* column */
        delete[] m_log_bit_err_col[i];
        /* row */
        delete[] m_log_min1_sum[i];
        delete[] m_log_min2_sum[i];
        delete[] m_log_check_sum_first_row[i];
        delete[] m_log_min_pos_first_row[i];
    }
    delete[] m_log_bit_err;
    delete[] m_log_punct_bit_err;
    delete[] m_log_bit_err_col;
    delete[] m_log_min1_sum;
    delete[] m_log_min2_sum;
    delete[] m_log_check_sum_first_row;
    delete[] m_log_min_pos_first_row;
    delete[] m_log_CSW;
    delete[] m_log_SW;
    delete[] m_log_PSW;
    delete[] m_log_LLR_idx;
#ifdef __AUTO_LLR_OPT__
    delete[] m_log_CSW_auto;
#endif // __AUTO_LLR_OPT__
}
//=============================================
// Sector의 decoding log 배열값 update
//=============================================
void Decoder::Update_Log_Data(int iter)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    int N_b = m_PCM->N_b;
    int M_b = m_PCM->M_b;
    int z_sb = m_PCM->z_sb;
    int p_start1 = m_ecc_info->bit_pos.info_punc_start1;
    int p_end1 = m_ecc_info->bit_pos.info_punc_end1;
    int p_start2 = m_ecc_info->bit_pos.info_punc_start2;
    int p_end2 = m_ecc_info->bit_pos.info_punc_end2;
    int num = 0;
    int total = 0;
    if (iter < MN_size) { // jump하여 종료 예외 case
        // column
        for (int jj = 0; jj < N_b; jj++) {
            num = Count_Error_Bit_Column(jj);
            m_log_bit_err_col[iter][jj] = num;
            total += num;
        }
        m_log_bit_err[iter] = total;
        num = 0;
        for (int j = p_start1; j < p_end1; j++) {
            if (cwc[j] != m_genie_inv_cw[j]) {
                num++;
            }
        }
        for (int j = p_start2; j < p_end2; j++) {
            if (cwc[j] != m_genie_inv_cw[j]) {
                num++;
            }
        }
        m_log_punct_bit_err[iter] = num;
        // row
        for (int jj = 0; jj < M_b; jj++) {
            num = 0;
            for (int i = 0; i < z_sb; i++) {
                num += REG_min1_value[jj * z_sb + i];
            }
            m_log_min1_sum[iter][jj] = num;
            num = 0;
            for (int i = 0; i < z_sb; i++) {
                num += REG_min2_value[jj * z_sb + i];
            }
            m_log_min2_sum[iter][jj] = num;
        }
        for (int jj = 0; jj < z_sb; jj++) {
            m_log_check_sum_first_row[iter][jj] = (Check_REG[jj][IDX_CHECK_SUM] + Syndrome[jj]) % 2;
            m_log_min_pos_first_row[iter][jj] = REG_min1_pos[jj];
        }
        m_log_CSW[iter] = Compute_CSW();
        if ((MODE_DEC_HD == m_param_dec->init_n) && (iter == 0)) {
            m_log_SW[iter] = Compute_SW(TRUE);
            m_log_PSW[iter] = Compute_PSW(TRUE);
        }
        else {
            m_log_SW[iter] = Compute_SW(FALSE);
            m_log_PSW[iter] = Compute_PSW(FALSE);
        }
        m_log_LLR_idx[iter] = cur_set_idx + 1;// update log, LLR_SET을 1부터 indexing
    }
}
//=============================================
// jj번째 column에 존재하는 error bit 수를
// 출력한다
//=============================================
void Decoder::Print_Log_Bit_Err_Col(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    int N_b = m_PCM->N_b;
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t%d\t", m_sector_idx, i);
        for (int jj = 0; jj < N_b; jj++) {
            fprintf(fp, "%d\t", m_log_bit_err_col[i][jj]);
        }
        fprintf(fp, "\n");
    }
}
void Decoder::Print_Log_Bit_Err(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    fprintf(fp, "%d\t", m_sector_idx);
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t", m_log_bit_err[i]);
    }
    fprintf(fp, "\n");
}
void Decoder::Print_Log_Err_Dv(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    int J = m_PCM->J;
    int N_b = m_PCM->N_b;
    int num_err;
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t%d\t", m_sector_idx, i);
        for (int d = 0; d < J; d++) {
            num_err = 0;
            for (int jj = 0; jj < N_b; jj++) {
                if (m_PCM->ColW[jj] == d + 1) {
                    num_err += m_log_bit_err_col[i][jj];
                }
            }
            if (num_err < 0)
                fprintf(fp, "%d\t", 0);
            else
                fprintf(fp, "%d\t", num_err);
        }
        fprintf(fp, "\n");
    }
}
void Decoder::Print_Log_SW(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    fprintf(fp, "%d\t", m_sector_idx);
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t", m_log_SW[i]);
    }
    fprintf(fp, "\n");
}
#ifdef __AUTO_LLR_OPT__
void Decoder::Print_Log_CSW_Auto(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    fprintf(fp, "%d\t", m_sector_idx);
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t", m_log_CSW_auto[i]);
    }
    fprintf(fp, "\n");
}
#endif // __AUTO_LLR_OPT__
void Decoder::Print_Log_PSW(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    fprintf(fp, "%d\t", m_sector_idx);
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t", m_log_PSW[i]);
    }
    fprintf(fp, "\n");
}
void Decoder::Print_Log_CSW(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    fprintf(fp, "%d\t", m_sector_idx);
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t", m_log_CSW[i]);
    }
    fprintf(fp, "\n");
}
void Decoder::Print_Log_Min1(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    int M_b = m_PCM->M_b;
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t%d\t", m_sector_idx, i);
        for (int jj = 0; jj < M_b; jj++) {
            fprintf(fp, "%d\t", m_log_min1_sum[i][jj]);
        }
        fprintf(fp, "\n");
    }
}
void Decoder::Print_Log_Min2(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    int M_b = m_PCM->M_b;
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t%d\t", m_sector_idx, i);
        for (int jj = 0; jj < M_b; jj++) {
            fprintf(fp, "%d\t", m_log_min2_sum[i][jj]);
        }
        fprintf(fp, "\n");
    }
}
void Decoder::Print_Log_Check_Sum_First_Row(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    int M_b = m_PCM->M_b;
    int z_sb = m_PCM->z_sb;
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t%d\t", m_sector_idx, i);
        for (int jj = 0; jj < z_sb; jj++) {
            fprintf(fp, "%d\t", m_log_check_sum_first_row[i][jj]);
        }
        fprintf(fp, "\n");
    }
}
void Decoder::Print_Log_Min_Pos_First_Row(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    int M_b = m_PCM->M_b;
    int z_sb = m_PCM->z_sb;
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t%d\t", m_sector_idx, i);
        for (int jj = 0; jj < z_sb; jj++) {
            fprintf(fp, "%d\t", m_log_min_pos_first_row[i][jj]);
        }
        fprintf(fp, "\n");
    }
}
void Decoder::Print_Log_LLR_Idx(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    fprintf(fp, "%d\t", m_sector_idx);
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t", m_log_LLR_idx[i]);
    }
    fprintf(fp, "\n");
}
void Decoder::Print_Log_Punc(FILE* fp)
{
    int MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1;// iter 0 포함
    int p_start1 = m_ecc_info->bit_pos.info_punc_start1;
    int p_end1 = m_ecc_info->bit_pos.info_punc_end1;
    int p_start2 = m_ecc_info->bit_pos.info_punc_start2;
    int p_end2 = m_ecc_info->bit_pos.info_punc_end2;
    int num_err = 0;
    fprintf(fp, "%d\t", m_sector_idx);
    for (int i = 0; i < MN_size; i++) {
        fprintf(fp, "%d\t", m_log_punct_bit_err[i]);
    }
    fprintf(fp, "\n");
}
//=============================================
// Sector의 decoding log 배열 pointer 반환
//=============================================
int** Decoder::Get_Log_Bit_Err_Col()
{
    return m_log_bit_err_col;
}
//=============================================
// Sector의 decoding log 배열 pointer 반환
//=============================================
int** Decoder::Get_Log_Min1()
{
    return m_log_min1_sum;
}
//=============================================
// Sector의 decoding log 배열 pointer 반환
//=============================================
int* Decoder::Get_Log_Checksum_Weight()
{
    return m_log_CSW;
}
void Decoder::Set_TV_Cycle_Based_On(int v)
{
    m_TV_cycle_based_on = v;
}
void Decoder::Adjust_HD_Floor_Type(int CSW_TH1, int CSW_TH2)
{
#if defined(__HD_FLOOR_SET__)
    int start_iter;
    int end_iter;
    if (m_ecc_info->matrix_sel == LAYOUT_PRIME_512B_TLC_VSS_OFF) {   //TLC, QLC용 Floor detect 따로 관리 22.01.21 변경
        start_iter = FLOOR_DETECT_ON_ITER_START_TLC;
        end_iter = FLOOR_DETECT_ON_ITER_END_TLC;
    }
    else if ((m_ecc_info->matrix_sel == LAYOUT_PRIME_512B_QLC_VSS_OFF) || (m_ecc_info->matrix_sel == LAYOUT_PRIME_512B_QLC_VSS_ON)) {
        start_iter = FLOOR_DETECT_ON_ITER_START_QLC;
        end_iter = FLOOR_DETECT_ON_ITER_END_QLC;
    }
    /*
    NOTE:  수정 전보환 2021.07.14
        사유: if문 조건 오류
        조치: && 에서 ||로 변경
    */
    if (mn < start_iter || mn > end_iter) {
        state_hd_error_floor_set = FLAG_HD_FLOOR_TYPE_0;
        cnt_hd_error_floor = 0;      //reset
    }
#if defined(__CORNER_CHECKER__)
        if (mn == start_iter - 1) {
            m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_FLOOR_TYPE_0 + state_hd_error_floor_set);
        }
#endif
    }
    else {
        if (cnt_hd_error_floor >= HD_FLOOR_CNT_TH2) {
            if (prev_CSW <= CSW_TH2) {
                cnt_hd_error_floor++;
            }
            else {
                cnt_hd_error_floor = 0; //reset
            }
        }
        else {
            if (prev_CSW <= CSW_TH1) {
                cnt_hd_error_floor++;
            }
            else {
                cnt_hd_error_floor = 0; //reset
            }
        }
        if ((state_hd_error_floor_set < FLAG_HD_FLOOR_TYPE_3) && (cnt_hd_error_floor >= HD_FLOOR_CNT_TH1)) {
            state_hd_error_floor_set++; // change state
            cnt_hd_error_floor = 0;      //reset
#if defined(__CORNER_CHECKER__)
            m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_FLOOR_TYPE_0 + state_hd_error_floor_set);
#endif
    }
}
#else
#ifdef __AUTO_LLR_OPT__
    state_hd_error_floor_set = FLAG_HD_FLOOR_TYPE_0;
#else
    state_hd_error_floor_set = FLAG_HD_FLOOR_TYPE_0;
#endif
#endif
}
