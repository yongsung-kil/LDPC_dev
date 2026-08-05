#ifndef ECCTG_DECODER_H
#define ECCTG_DECODER_H

#include <stdint.h>
#include "common.h"
#include "partial_CRC.h"
#include "full_CRC.h"
#include "ecc_data.h"
#include "Corner.h"
#include "random.h"

#ifndef __VSS_ECC_TOP__
#include "TV_Dec_Inter.h"

/* bit 위치별 구간 분류 (Build_Bit_Region) */
#define BIT_REGION_NONE     0
#define BIT_REGION_SH       1
#define BIT_REGION_PUNC     2
#define BIT_REGION_TABLE    3
#endif

//======================================
// Prime ECC Decoder
//======================================

/* 4-3: CN 상태 struct 묶음 — C2V_Cal/V2C_Store가 같은 row 인덱스로 함께 접근하는
   5개 배열(REG_min1_pos/REG_min1_value/REG_min2_value/Check_REG/Syndrome)을
   CN당 1개 struct로 통합 (원소당 캐시 라인 5개 → 1개 접근).
   20byte로 의도적으로 패딩하지 않음 — row block 순회 시 전 바이트를 읽으므로 밀도가 우선 */
struct CN_STATE {
    int min1_pos;
    int min1_value;
    int min2_value;
    int check_sum;      // 기존 Check_REG[i] (checksum 슬롯)
    int syndrome;       // 기존 Syndrome[i]
};

class Decoder
{
public:
    Decoder();
    ~Decoder();
    void    Init_Dec(ECC_INFO * info, PCM * pcm, PARAM_DEC * param, PARAM_LLR * param_LLR, int myrank);
    void    Init_Dec(ECC_INFO * info, PCM * pcm, PARAM_DEC * param, int myrank);
    void    Init_Dec_Option();
    void    LDPC_Decoder(
                int* i_HD_input,
                int* i_SD_input,
                int* i_CC_input,
                int* i_CD_input,
                int  i_DecOpt,
                int* i_genie_inv_msg,
                int  i_TV_idx,
                int  i_TV_sub_idx,
                int* o_iter_num,
                int* o_CRC_flag,
                int* o_n_error,
                int* o_str_n_error,
                int* o_1_counter,
                int* o_0_1_flip_counter,
                int* o_dec_d,
                int* o_BF_on,
                int* o_overall_clk,
                int* o_weak_correct_cnt,
                CornerChecker * io_corner);
    void    LDPC_Decoder(
                int* i_HD_input,
                int* i_SD_input,
                int* i_CC_input,
                int* i_CD_input,
                int  i_DecOpt,
                int* i_genie_inv_msg,
                int  i_TV_idx,
                int  i_TV_sub_idx,
                int* o_iter_num,
                int* o_CRC_flag,
                int* o_n_error,
                int* o_str_n_error,
                int* o_1_counter,
                int* o_0_1_flip_counter,
                int* o_dec_d,
                int* o_BF_on,
                int* o_overall_clk,
                int* o_weak_correct_cnt);
    int     Get_Real_MN();
    int*     Get_CRC_LFSR_iter();
private:
    void    Alloc_Dec();
    void    Release_Dec();
    void    Initialize_Dec();

    /* LDPC decoding algorithm */
    void    C2V_cal(int jj);
    void    C2V_Cal(int jj, int ii, int iter);
    int     C2V_Cal_New_Sgn(int iter, int synd, int check_sum, int edge_sgn, int col_idx);
    void    CNU_Remove_Old_Sgn(int iter, int pre_v2c_sgn, int * check_sum, int col_idx);
    void    CNU_Update_New_Sgn(int v2c_sgn, int * check_sum);
    void    CNU_Update_New_Mag(int v2c_mag, int * min1_value, int * min2_value, int * min1_pos, int cur_pos, int cur_pos_p2, int* update_flag, int row_idx);

    void    V2C_Cal(int jj);
    void    VN_Cal_Pre(int jj);
    void    VN_Cal_HD(int v_deg, int idx_offset, int iter);
    void    VN_Cal_CD(int v_deg, int idx_offset, int iter);
    void    VN_Cal_SD(int v_deg, int idx_offset, int iter);
    void    V2C_Store(int jj, int skip);
    void    V2C_Store(int jj, int ii, int iter, int store_checksum_REG, int store_min_REG, int store_edge_SRAM);
    void    Preprocessing();

    /* Half Column Update */
    void    C2V_cal_HCU(int jj, int G_idx);
    void    V2C_Cal_HCU(int jj, int G_idx);
    void    VN_Cal_Pre_HCU(int jj, int G_idx);
    void    VN_Cal_HD_HCU(int v_deg, int idx_offset, int G_idx, int iter);
    void    VN_Cal_SD_HCU(int v_deg, int idx_offset, int G_idx, int iter);
    void    V2C_Store_HCU(int jj, int G_idx, int skip);
    void    PMU_Read_HCU(int jj, int G_idx);
    void    PMU_Write_HCU(int jj, int G_idx);

    /* TV */
    void    Print_TV_Cycle_Based(int jj, int clk);

    /* HW Timing */
    void    Delay_2clk(int parity_skip);         // HCU
    void    PMU_Read(int jj);
    void    PMU_Write(int jj);
    void    Clk_Manager(int clk);
    int    Clk_Inc(int clk);
    void    Clk_Init();                          // HCU
    void    Clk_Delay_REG();
    int     Clk_Valid_Col(int phase);
    void    Init_Main_SRAM_RQ(int first);

    /* Dual update */
    void    DU_Manager();

    /* LLR mapping */
    int     Mapper_3bit_SD(int hd, int sd, int cc, int m1, int m2, int m3, int m4);
    int     Mapper_3bit_SD_weak_degree(int hd, int sd, int cc, int m1, int m2, int m3, int m4);
    int     Mapper_2bit_SD(int hd, int sd, int m1, int m2);
    void    Make_LLR(int * hd_input, int * sd_input, int * cc_input, int * cd_input);
    void    Get_VNU_Ch_LLR_Adaptive(int dv, int col_idx, int table_idx, int* ch1, int* ch2, int* ch3, int* ch4);
    void    Get_VNU_Th_Adaptive(int dv, int col_idx, int table_idx, int* th1, int* th2, int* th3, int* th4, int* th5, int* th6, int* th7);
    int     Get_VNU_Table_Idx(int iter);
    int     Get_Cur_LLR_Idx_FILE(int iter);
    void     Get_VNU_LLR_SET_FILE(int dv, int col_idx, int table_row_idx, int* ch1, int* ch2, int* ch3, int* ch4, int* th1, int* th2, int* th3, int* th4, int* th5, int* th6, int* th7 );
    void    Adjust_HD_Floor_Type(int CSW_TH1, int CSW_TH2);

    /* Clear */
    void    Clear_Flag();
    void    Clear_Iter_Start();
    void    Clear_CN_REG(int type);
    void    Clear_Edge_SRAM();
    void    Clear_Delay_REG();
    void    Clear_PMU();
    void    Clear_Sum_t_OLD();
    void    Clear_Edge_SRAM_Sgn();
    void    Clear_Syndrome();
    void    Clear_Edge_Restart();
    void    Clear_REG_min_pos();
    void    Clear_REG_min_value(int bMin1, int bMin2);
    void    Clear_TV_buffer();
    void    Clear_TV_Min_Val();
    void    Clear_TV_Min_Upt();

    /* Algorithms */
    void    Init_PCRC_REG(int jj);
    void    Cal_PCRC(int jj);
    void    Cal_PCRC_Last_Only(int jj);
    void    Check_Genie_PCRC(int jj);
    void    Check_Genie_CRC();
    int     Check_End_Iter(int *cur_iteration);
    void    Count_Flip_Bits(int jj);
    void    Check_Power_Stopping_Cond(int jj);
    int     Jump_Iter(int *cur_iteration);
    void    Select_BF();
    //void    Select_Iteration_Set();
    int     Is_Iter_Type_Edge_Clear(int cur_iteration);
    int     Is_Iter_Type_Init(int cur_iteration);
    void    Load_LLR_Tables();
    void    Build_Bit_Region();
#if defined (__ECC_TV__)
    int**   Get_Check_REG_View();
    int*    Get_Syndrome_View();
    int*    Get_Min1_Pos_View();
    int*    Get_Variable_Mem_View();
#endif
    int*    Get_Cwc_View();
    void    Get_Err_Cnt(int* i_HD_input, int * i_SD_input, int * dec_output, int * err_cnt, int * strong_err_cnt, int* zero_to_one_flip_cnt, int *weak_cor_cnt);
    int     Get_One_Cnt(int* dec_output);
    void    Set_CSW(int w);
    int     Get_Default_Min_Pos(int row_idx);

    /* Log */
    int     Compute_CSW();
    int     Compute_SW(int bPreudate);
    int     Compute_PSW(int bPreudate);
    int     Compute_Min1_Sum();
    int     Compute_Min2_Sum();
    int     Compute_Min1_Sum_MSB();
    void    Compute_Err_In_CN(int row_blk, int * err_sum, int * max, int *min1_v);
    void    Count_Error_Bit(int *cw, int* info);
    int     Count_Error_Bit_Column(int jj);

    void    Open_Log_Files();
    void    Close_Log_Files();
    void    Padding_Zero_Log(int iter, int CRC_flag);
    void    Print_Log_Files();
    void    Print_Log_Bit_Err_Col(FILE* fp);
    void    Print_Log_Bit_Err(FILE* fp);
    void    Print_Log_Err_Dv(FILE* fp);
    void    Print_Log_SW(FILE* fp);

#ifdef __AUTO_LLR_OPT__
    int    Compute_CSW_Auto();
    void    Print_Log_CSW_Auto(FILE* fp);
#endif // __AUTO_LLR_OPT__

    void    Print_Log_PSW(FILE* fp);
    void    Print_Log_CSW(FILE* fp);
    void    Print_Log_Punc(FILE* fp);
    void    Print_Log_LLR_Idx(FILE* fp);
    void    Print_Log_Min1(FILE *fp);
    void    Print_Log_Min2(FILE *fp);
    void    Print_Log_Min_Pos_First_Row(FILE *fp);
    void    Print_Log_Check_Sum_First_Row(FILE *fp);

    void    Print_CRC_result(int end_pos);
    void    Print_Log_FIFO(int end, int PCRC);
    void    Print_Log_Power_Stopping(int end);
    void    Print_Log_VNU_in(int show_type);
    void    Print_Log_VNU_out(int show_type);
    void    Print_Log_Sum_T(int show_type);

private:
    ECC_INFO*       m_ecc_info;
    PCM*            m_PCM;
    PARAM_DEC*      m_param_dec;
    PARAM_LLR*      m_param_LLR;
#if defined(__CORNER_CHECKER__)
    CornerChecker * m_corner;
#endif

    CN_STATE*   m_CN;               // [M] CN 상태 통합 (기존 REG_min1_pos/REG_min1_value/REG_min2_value/Check_REG/Syndrome)

    int8_t**    Check_SRAM_sgn;     // [M][K] 값 0/1 — int8_t 축소 (행당 104B → 26B, 캐시 밀도 4배)
#if defined (__ECC_TV__)
    int**       m_Check_REG_view;   // Print_TV_check_sum(int**) 시그니처 유지용 뷰
    int*        m_Syndrome_view;    // Print_TV_syndrome / Print_TV_check_sum(int*) 시그니처 유지용 뷰
    int*        m_min1_pos_view;    // Print_TV_min_pos(int*) 시그니처 유지용 뷰
    int*        m_Variable_mem_view; // Print_TV_llr_out/str_err_cnt_BLK(int*) 시그니처 유지용 뷰
#endif
    int8_t*    Variable_mem;        // [N] 값 0/1 (HD/genie/PR 비트) — int8_t 축소
    int*        m_bit_region;       // [N] bit 위치별 구간 분류 (BIT_REGION_*)
    int         m_bit_region_ready;
    int**       shift_tbl_C2V;      // [s][j] shift 순열 사전 계산 (dir=0). s = PCM_b shift 값 (0 ~ z_sb-1 전제)
    int**       shift_tbl_V2C;      // [s][j] shift 순열 사전 계산 (dir=1)

    /* LLR/threshold 테이블 파라미터화: llr_tables.txt에서 1회 로드 (없으면 코드 기본 테이블 사용) */
    int         m_llr_from_file;
    int         m_Ch_LLR_HD[PRIME_HD_LLR_TABLE_NUM_ROW][PRIME_LLR_TABLE_NUM_DEGREE * 1];
    int         m_Ch_LLR_2SD[PRIME_2SD_LLR_TABLE_NUM_ROW][PRIME_LLR_TABLE_NUM_DEGREE * 2];
    int         m_Ch_LLR_3SD[PRIME_3SD_LLR_TABLE_NUM_ROW][PRIME_LLR_TABLE_NUM_DEGREE * 4];
    int         m_Th_HD[PRIME_HD_LLR_TABLE_NUM_ROW][PRIME_LLR_TABLE_NUM_DEGREE * PRIME_LLR_TABLE_NUM_TH];
    int         m_Th_2SD[PRIME_2SD_LLR_TABLE_NUM_ROW][PRIME_LLR_TABLE_NUM_DEGREE * PRIME_LLR_TABLE_NUM_TH];
    int         m_Th_3SD[PRIME_3SD_LLR_TABLE_NUM_ROW][PRIME_LLR_TABLE_NUM_DEGREE * PRIME_LLR_TABLE_NUM_TH];

    int**       VNU_in, **VNU_out, **VNU_out2, **VNU_out3; //HW delay consideration
#if defined (__ECC_TV__)
    int**        VNU_out_nq, **VNU_out2_nq, ** VNU_out3_nq;
#endif
    int**        VNU_out3_temp;
    /* Half Column */
    int**       Sum_t_OLD_G0;
    int**       Sum_t_OLD_G1;

    int**      pre_exist_sgn_reg, **pre_exist_sgn_reg2, **pre_exist_sgn_reg3; //HW delay consideration
#if defined (__ECC_TV__)
    int**      pre_exist_sgn_reg_BS, **pre_exist_sgn_reg2_BS, **pre_exist_sgn_reg3_BS; //HW delay consideration
#endif

    int*        Syndrome_intermediate;
#if defined(__ECC_TV_SYND_INTERNAL_DEBUG__)
    int**       Syndrome_intermediate_internal;
    int**      Punc_vote_Mag;
    int***      Punc_vote_Mag_Row;
    int***     Punc_vote_Mag_Row_before_BS;
    int**        Punc_vote_decision;
#endif
    int8_t*     cwc;                // [N] 값 0/1 — int8_t 축소 (CRC/TV 경계는 m_cwc_view로 전달)
    int*        m_cwc_view;         // CRC_decoder(int*)/Print_TV_cwc(int*) 시그니처 유지용 뷰 (CRC 경로가 무가드라 무조건 보유)
    int*        prev_cwc;
    //int**     out_err_cnt;        // up to 10 errors

    /* HW Timing */
    int**       PMU_SRAM;
    int*        FIFO_level;
    int*        MAIN_SRAM_read_rq;
    int*        MAIN_SRAM_read_rq2;  // HW delay consideration
    int*        MAIN_SRAM_write_rq;

    int         m_myrank;

    int         cnt_idle_cycle;
    int         col_M1;
    int         col_M1_temp;
    int         col_Z;
    int         col_P1;
    int         col_P2;
    int         col_P3;
    int         col_P4;
    int         clk_copy;

    // HW Timing for Half Column Update
    int         col_M1_G;
    int         col_M1_temp_G;
    int         col_Z_G;
    int         col_P1_G;
    int         col_P2_G;
    int         col_P3_G;
    int         col_P4_G;

    /* Dual update flag */
    int         DU_flag_M1_temp;
    int         DU_flag_M1;
    int         DU_flag_Z;
    int         DU_flag_P1;
    int         DU_flag_P2;
    int         DU_flag_P3;
    int         DU_flag_P4;

    /* SD LLR */
    int*        Soft_LLR;       // Soft-decision Initial LLR
    int*        Soft_LLR_weak_degree;
    int*        Soft_LLR_PRIME;

    /* 1.5SD */
    int*        CD;

    /* Decoder status and results */
    int         Force_stopping;     // Force stopping parameter
    int         pre_Force_stopping;
    int         real_mn;
    int         flag_BF_on;     // 0 : 3bit precision mode, 1: 1bit precision mode
    int         flag_HD_1_4_Set;
    int         flag_HD_5_8_Set;
    int         syn_weight;     // partial syndrome
    int         psyn_weight;    // partial syndrome
    int         syn_th_BF;      //
    int         syn_th_BF0;   // S-4 Set
    int         syn_th_BF1;   // S-4 Set
    //int         syn_th_BF2;   // S-4 Set
    int       syn_th_5_8_Set_0;   // S-8 Set
    int       syn_th_5_8_Set_1;   // S-8 Set
    int         flag_dec_1iter;
    //int       flag_BI_SRAM;
    int         Error_count_reg;
    int         cur_variable_node;
    int         prev_variable_node;
    int         prev_variable_node2;
    int         prev_variable_node2_print;
    // Half Column Update
    int         cur_variable_node_G_idx;
    int         prev_variable_node_G_idx;
    int         prev_variable_node2_G_idx;
    int         prev_variable_node2_print_G_idx;

    int         check_sum_weight;
    int         flag_parity_skip;
    int         failure_flag;
    int         jump_flag;
    int         iter_num;
    int         CRC_flag;
    int         MN_old;     // previous MN
    int         mn;
    int         MN;
    int         prev_CSW;
    int         prev_min1_v_sum;
    int         state_hd_error_floor_set;
    int         cnt_hd_error_floor;
    int         cur_set_idx;
    int         skip_idx;       // Iter 4: column index
    int         skip_idx2;      // Iter 5: column index
    int         Floor_Detect_CSW_TH1;
    int         Floor_Detect_CSW_TH2;
    /* Partial CRC */
    int*        dec_d;
    int*        lfsr_TP1;
    int*        lfsr_TP2;
    int*        lfsr_TP3;
    int*        lfsr_TP4;
    int*        pcrc_checksum;

    /* Full CRC */
    int         crc_dec_LFSR_final[CRC_LEN];
#if defined(__ECC_TV__)
    int**       crc_dec_LFSR_internal;
#endif
    int*         crc_dec_LFSR_iter;

    int         flagPassPCRC;
    int         out_last_column;
    int         stop_by_partial_crc;
    int         idxTermination[NUM_PCRC_TERMINATION_POINT];
    int*        m_genie_inv_cw;
    int         m_sector_idx;

    int         m_TV_cycle_based_on;

    int         PR_ERR_CNT;
    int         PR_ERR_MAG_CNT;
    int         PR_MAG_CNT;
    //int*      PR_bits_file_cnt;

    int*        PR_weak_cnt0;
    int*        PR_weak_cnt1;
    int*        PR_weak_cnt2;
    int*        PR_weak_cnt3;

    int*        PR_weak_cnt0_acc;
    int*        PR_weak_cnt1_acc;
    int*        PR_weak_cnt2_acc;
    int*        PR_weak_cnt3_acc;

    /* Test vector */
    TV_Dec_Inter    m_tv_dec_inter;
    int         m_TV_idx;
    int         m_TV_sub_idx;
    int*         tv_llr_out;
    int**       tv_vtc_inp;     // VNU_in (check_out)
    int**       tv_old_mag;
    int**       tv_old_sgn;
    int*        tv_upt_min;
    int*        tv_min_weak;
    int*        tv_min_weak2;
    int**        tv_new_sgn_mag;
    int*        tv_one_cnt_blk;
    int*        Punc_one_cnt;

#if defined(__HALF_COL_UPDATE__)
    int**       tv_vtc_inp_HCU;     // VNU_in (check_out) Half Column Update
    int**       tv_old_sgn_HCU;
    int**      tv_new_sgn_mag_HCU;
    int**      tv_new_sgn_mag_HCU_in;
    int**      tv_new_sgn_mag_HCU_in2;
    int**      tv_new_sgn_mag_HCU_in3;
    int**      tv_new_sgn_mag_HCU_in_nq;
    int**      tv_new_sgn_mag_HCU_in2_nq;
    int**      tv_new_sgn_mag_HCU_in3_nq;
    
    int HCU_start;
    int HCU_end;
#endif


    FILE*       fp_log_bit_err;
    FILE*       fp_log_bit_err_col;
    FILE*       fp_log_err_dv;
    FILE*       fp_log_min1;
    FILE*       fp_log_min2;
    FILE*       fp_log_check_sum;
    FILE*       fp_log_min_pos;
    FILE*       fp_log_SW;
    FILE*       fp_log_PSW;
    FILE*       fp_log_CSW;
    FILE*       fp_log_punc;
    FILE*       fp_log_CRC;
    FILE*       fp_log_LLR_idx;

    int*       m_log_bit_err;
    int**       m_log_bit_err_col;
    int*       m_log_punct_bit_err;
    int**        m_log_min1_sum;
    int**        m_log_min2_sum;
    int**       m_log_min_pos_first_row; //Polarized Log
    int**       m_log_check_sum_first_row; //Polarized Log
    int*        m_log_SW;

#if defined(__AUTO_LLR_OPT__)
    FILE*       fp_log_CSW_auto;
    int*        m_log_CSW_auto;
#endif

    int*        m_log_PSW;      // Partial SW
    int*        m_log_CSW;
    int*        m_log_LLR_idx;

    int**       m_log_VNU_in;
    int**       m_log_VNU_out;
    int*        m_log_sum_t;
    int*        m_log_ch_llr;
    
    void    Init_Log_Data();
    void    Alloc_Log_Data();
    void    Release_Log_Data();
    void    Update_Log_Data(int iter);
public:
    int**    Get_Log_Bit_Err_Col();
    int**    Get_Log_Min1();
    int*    Get_Log_Checksum_Weight();
    void    Set_TV_Cycle_Based_On(int v);
};

#endif