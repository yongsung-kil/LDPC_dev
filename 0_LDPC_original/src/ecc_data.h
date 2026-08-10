#ifndef ECCTG_ECC_DATA_H
#define ECCTG_ECC_DATA_H

#include "common.h"

//==================================================
// Data structures
//==================================================

/* ECC layout */
struct BIT_POS {
    int info_end;
    int info_sh_start;
    int info_sh_end;
    int info_punc_start1;
    int info_punc_end1;
    int info_punc_start2;
    int info_punc_end2;
    int info_no_punc_start;
    int info_no_punc_end;
    int parity_no_punc_start;
    int parity_no_punc_end;
    int parity_punc_start;
    int parity_punc_end;
};

struct DEC_IN_STATUS {
    int len_noPS;
    int c1;
    int c2;
    int c3;
    int c4;
    int e1;
    int e2;
    int e3;
    int e4;
};

struct ECC_INFO{
    int H_mat_idx;
    int matrix_sel;
    char str_matrix_name[LEN_FILENAME];
    int mode_all_one_cw;
    int shortened_bit_info;
    int punctured_bit_info;
    int punctured_bit_parity;
    int shortened_bit_info_offset_end;
    BIT_POS bit_pos;
};

struct PARAM_REF_C {
    int ch_type;
    double RBER;
    int num_fixed_err;
    double fixed_SCR;
    double fixed_SER;

    double fixed_VSCR;
    double fixed_NSCR;
    double fixed_NWCR;
    double fixed_VWCR;

    double fixed_VSER;
    double fixed_NSER;
    double fixed_NWER;
    double fixed_VWER;

    double fixed_erasure_ratio;
    int fn;
    int max_num_test;
    int mode_seed;
    int mode_init_seed;
    int mode_scenario;
    int mode_data_input;
    char str_result_name_4KB[LEN_FILENAME];

    int frame_sum;
    int frame_err_num;
    double iter_sum;
    int mode_iter;

    int frame_err_num_opt;
    int frame_sum_opt;
    double Avit_opt;

    int LLR_seed;
    int LLR_opt_row_idx1;
    int LLR_opt_row_idx2;
    int LLR_opt_col_idx1;
    int LLR_opt_col_idx2;

    int LLR_opt_dev;
    int LLR_opt_mag;

    int LLR_dev_num;
    int** LLR_dev;

    double* FER_local;
    double* FER_MPI;

    int LLR_MAT_idx;
};

struct PARAM_TV_GEN{
    int TS_idx;
    int mode_rand;
    int mode_error_pos;
    int err_case;
    int mass_case;
    int e_pos;
    int e_step;
    int mode_init_seed;
    int mode_scenario;
    int ch_type;
    double RBER;
    int num_fixed_err;
    double fixed_SCR;
    double fixed_SER;
    double fixed_erasure_ratio;
};

struct PARAM_DEC {
    int init_n;
    int power_index;
    int stopping_criteria;
    int CRC_Option_F_P;
    int BF_mode;
    int diverse_th;
    int MN_num;
    int* MN;

    int LLR_opt_csw_idx1;
    int LLR_opt_csw_idx2;
    int LLR_opt_flip_idx1;
    int LLR_opt_flip_idx2;

    int LLR_seed;
    int LLR_opt_csw_mag;
    int LLR_opt_q_mag;
    int LLR_opt_th_mag;
    int LLR_opt_dev;

#ifdef __AUTO_LLR_OPT__
    int flag_print_CSW_log;
    int rank_supercom;
#endif
};

struct PCM{
    int N_b;    // number of column blocks
    int M_b;    // number of row blocks
    int N;      // number of variable nodes
    int M;      // number of check nodes
    int J;      // max variable node degree
    int K;      // max check node degree
    int z_sb;   // size of parallelism
    int** PCM_b;    // parity checkmatrix (base + shift value)
    int** PCM_b_enc;    // parity checkmatrix for encoding(base + shift value)
    int* RowW;      // row weight
    int* ColW;      // col weight
    int** V_net_b;
    int** VtoC_ID;
    int** C_net;
    int** PCM_GT;
    int** Mux_Matrix;
    int** Mux_idx;
    int* ar;

    int punct_col_num;
    int* punct_col_idx;
    int* punct_row_num;
    int** punct_vote;
    int** punct_vote_disjoint;
    int*** punct_vote_b;
    int*** punct_vote_joint;

};

struct PARAM_LLR{
    int num_para_each_set;
    int num_dv;
    int num_row;
    int* dv_from;
    int* dv_to;
    int num_group;
    int* num_set_each_group;
    int num_col;
    int* type_each_group;
    int restart_num;
    int* restart_iter;
    int* max_value;
    int* min_value;
    int** LLR_MATRIX;
    int* CSW_thr;
    int* iter_start;
    int* iter_end;
    int* floor_flag;
};

struct PARAM_OPT{
    int matrix_idx;
    int opt_type;
    int measure;
    int** opt_flag_matrix;
    int opt_idx_num;
    int opt_trial_num_1dim;
    int opt_trial_tot_num;
    int* opt_idx;
    int opt_mag;
    int opt_dim;
    int* curr_row_idx;
    int* curr_col_idx;
    int* curr_sign;
    int* curr_value;
    int** opt_LLR_MATRIX;
    int* opt_CSW_thr;
    double opt_FER;
    double curr_FER;
    double opt_Avit;
    double curr_Avit;
    int dv_opt_loop_num;
    int dv_opt_per_num;

};
#endif