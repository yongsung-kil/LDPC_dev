#ifndef ECCTG_ECC_TOP_H
#define ECCTG_ECC_TOP_H

#include "common.h"
#include "ecc_data.h"
#include "Decoder.h"
#include "Encoder.h"
#include "full_CRC.h"
#include "partial_CRC.h"
#include "random.h"
#include "input.h"
#include "GT.h"
#include "Corner.h"

#ifndef __VSS_ECC_TOP__
#include "channel.h"
#include "TV_Dec.h"
#include "TV_Enc.h"
#endif

//======================================
// ECC Top
//======================================

class ECC_Top
{
public:
    ECC_Top();
    ~ECC_Top();
    void    Init_ECC_Top(ECC_INFO* info, PARAM_DEC* param_dec, PARAM_LLR* param_LLR, int my_rank, int num_pro);  // ECC only
    void    Init_ECC_Top(ECC_INFO* info, PARAM_DEC* param_dec, int my_rank, int num_pro);  // ECC only
    void    Init_ECC_Top(ECC_INFO* info, PARAM_DEC* param_dec);  // VSS + ECC
    void    Run_ECC_Top_Ref_C(PARAM_REF_C * p_ref_c);
    void    Run_ECC_Top_TV_Gen(PARAM_TV_GEN * p_tv_gen);

    PCM*    Get_PCM();
    Encoder*    Get_Enc();
    Decoder*    Get_Dec();

private:
    void    Run_Ref_C_Scenario_4KB();
    void    Run_TV_Gen_Scenario_4KB();
    void    Run_TV_Gen_Scenario_4KB_XOR25_Seed_File();
    void    Run_TV_Gen_Scenario_4KB_DIN_File();

    void    Load_PCM(PCM* pcm, ECC_INFO *ecc_info);
    void    Release_PCM(PCM* pcm);

    void    Alloc_Buffer();
    void    Load_ECC_Input(FILE* fp, char * filename);
    void    Load_ECC_Input_TV(FILE* fp, char* filename, int * seed_size);
    void    Print_Result_Part1(int Flag_16KB);
    void    Print_Result_Part1_Auto();

    void    Print_Result_Part2_Memory_Opt(int bFile, int rn, int* fr, double iter_sum, double clk_sum, double clk_sum_throughput, int bEnd, double* FER);
    void    Print_Result_Part2_Memory_Opt_Auto(int bFile, int rn, int* fr, double iter_sum, double clk_sum, double clk_sum_throughput, int bEnd, double* FER);
    void    Print_Result_Part2(int bFile, int rn, int * fr, double iter_sum, double clk_sum, double clk_sum_throughput, int bEnd, int Flag_16KB);
#if defined (__RUN_MPI__)
    void    Print_Result_MPI(int mode, int FER_num);
    int     Gather_Result_MPI(int bFinal, int rn_part, double iter_part, double clk_part, int* fr_part, int fr_fly, int fr_num);
#endif
    void    Print_TV_Log_FIFO(int idx);
    void    Print_TV_Log_Power_Stopping(int idx);
    void    Set_Bit_Pos();
    void    Set_Real_Err_Pos_4KB(int err_pos_num);

    void    Make_TV_Folder();
    void    Make_TV_Fixed_Err_Case_4KB(int e);

    void    Gen_Regular_Err(int * err_pos, int len_max, int e_num, int e_pos, int e_step);
    void    Make_Dec_Input_Ref_C_Fixed_4KB(int * cw, int* HD_input, int * SD_input, int * CC_input, int * CD_input);
    void    Make_Dec_Input_TV_Fixed_4KB(int * cw, int* HD_input, int * SD_input, int * CC_input, int * CD_input, FILE *fp);
    void    Make_Dec_Input_TV_Gen_Fixed_4KB(int * cw, int* HD_input, int * SD_input, int * CC_input, int * CD_input);

    void    Make_Dec_Input_Fixed_4KB(int *HD_input, int * SD_input, int * CC_input, int * CD_input, int all_one_masking, int c1, int c2, int c3, int c4, int e1, int e2, int e3, int e4, FILE *fp);
    void    Make_Dec_Input_AWGN_Quantize(int N, double *cwr, double var, int*  HD_input, int* SD_input, int* CC_input, int* CD_input);
    void    Make_Dec_Input_AWGN(int N, int *cw, int *cwt, double* cwr, double dev, double var, int*  HD_input, int* SD_input, int* CC_input, int* CD_input);
    void    Make_Dec_Input_TV_Gen_AWGN(int N, int *cw, int *cwt, double* cwr, int* HD_input, int* SD_input, int* CC_input, int* CD_input);
    void    Load_Msg_Vector(FILE * fp, int *msg, int msglen);
    void    Load_Dec_Input_Vector_Format(int N, int len_noPS);
    void    Set_Corner_Checker();
    void    Print_Corner_Checker_Total();
    int    Update_Corner_Checker_Total();
    void    Clear_Corner_Checker();

private:
    int         m_my_rank;
    int         m_num_process;

    ECC_INFO*       m_ecc_info;
    PARAM_DEC*      m_param_dec;
    PARAM_REF_C*    m_param_ref_c;
    PARAM_TV_GEN*   m_param_tv_gen;
    PARAM_LLR*      m_param_LLR;

    PCM             m_PCM;
    Decoder         m_dec;
    Encoder         m_enc;
    CornerChecker   m_corner_checker;
    CornerChecker   m_corner_checker_total;

    DEC_IN_STATUS   m_dec_in_status[1];
    time_t          m_time_start;
    time_t          m_time_end;

    double          m_gaussian_var;
    double          m_gaussian_dev;

    /* buffers */
    int*        m_msg;
    int*        m_inv_msg;
    int*        m_inv_cw;
    int*        m_inv_cw_input;
    int*        m_cw;
    int*     m_cwt;
    double*        m_cwr;

    int*        m_err_position;
    int*        m_err_position_noPS;

    int*        m_HD_channel;
    int*        m_SD_channel;
    int*        m_CC_channel;
    int*        m_CD_channel;
    int*        m_HD_input;
    int*        m_SD_input;
    int*        m_CC_input;
    int*        m_CD_input;
    int*        m_dec_output;

    TV_Dec          m_tv_dec;
    TV_Enc          m_tv_enc;

    int         rn;
    int*        fr_4KB;
    int        fr_over_fly;
    double      iter_sum;
    double      iter_temp;
    double      iter_effective;
    double      clk_sum = 0;
    double      clk_sum_throughput;
    double      clk_temp;

    /*  */
    int         o_iter_num;
    int         o_CRC_flag;
    int         o_n_error;
    int         o_str_n_error;
    int         o_weak_n_cor;
    int         o_0_1_flip_counter;
    int         o_1_counter;
    int         o_BF_on;
    int         o_overall_clk;

    unsigned int current_seed[SEED_LEN];
    FILE *      fp_uncor_seed;
    FILE *      fp_uncor_seed_2nd_decode;
    char        filename_uncor_seed[LEN_FILENAME];
    char        filename_uncor_seed_2nd_decode[LEN_FILENAME];

#ifdef __AUTO_LLR_OPT__
    /* for MOST_SIM_UNCOR_SEED_LOAD_INIT_SEED */
    FILE *      fp_init_seed;
    char        filename_init_seed[LEN_FILENAME];
#endif // __AUTO_LLR_OPT__

#if defined (__RUN_MPI__)
    double      tot_rn;
    double*     tot_fr;
    double      tot_iter_sum;
    double      tot_clk_sum;
    double      tot_fr_fly;
#endif

    /* Corner Checker */
    int flag_update_corner_check;

    int**       m_log_bit_err_column_tot;
    int**       m_log_min1_tot;
    int*        m_log_checksum_weight_tot;
    int*        m_log_iter_histogram_tot;
    int         m_tested_num;
    void        Init_Log_Data();
    void        Alloc_Log_Data();
    void        Release_Log_Data();
    void        Update_Log_Data();
    void        Print_Log_Data();
    void        Update_Log_Iter_Histogram(int iter, int pcrc);
    void        Open_Log_Files();

#if defined(__ENC_TV_INTER_DEBUG__)
    int**       m_Parity_inter;
#endif

};

#endif
