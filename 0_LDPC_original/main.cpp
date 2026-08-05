#include "common.h"
#include "ecc_data.h"
#include "ECC_Top.h"
#include "Local_Opt.h"
//================================================
// Prime ECC 3.0
//================================================
using namespace std;
int     Setup(int argc, char* argv[]);
int     Setup_Ref_C(int argc, char* argv[]);
int     Setup_TV_Gen(int argc, char* argv[]);
#ifdef __AUTO_LLR_OPT__
//int       Setup_Ref_C_Auto(int argc, char* argv[]);
void    Print_Mode_Define_File_Auto(int n);
#endif // __AUTO_LLR_OPT__
void    Run_Simulation();
void    Run_Simulation_Ref_C();
void    Run_Simulation_Local_Opt();
void    Run_Simulation_TV_Gen();
void    Set_H_Filename(char* buf_4KB, int matrix_sel);
void    Get_H_Filename(char* buf_4KB, char* input_H_name);   // H-matrix
void    Set_Punctured_Shortened_Bits();
void    Set_Ref_C_Result_Filename();
void    Set_Ref_C_Iteration();
void    Set_TV_Scenario_4KB();
void    Print_COH();
void    Print_Input_Err_Code(int code);
void    Usage();
void    Print_Mode_Define();
ECC_INFO      g_ecc_info;
PARAM_DEC     g_param_dec;
PARAM_REF_C   g_param_ref_c;
PARAM_TV_GEN  g_param_tv_gen;
ECC_Top* g_pECC = NULL;
LOCAL_OPT* g_LOPT = NULL;
int             g_myrank = ID_ROOT;
int             g_num_process = 1;
/* SCN LLR parameters */
int** Cand_LLR;
char filename_trial[255];
char filename_opt[255];
FILE* fp_trial = NULL;
FILE* fp_opt = NULL;
//================================================
// main
//================================================
int main(int argc, char* argv[]) {
    int err = FALSE;
#if defined(__RUN_MPI__)
    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &g_num_process);
    MPI_Comm_rank(MPI_COMM_WORLD, &g_myrank);
#endif
#ifdef __AUTO_LLR_OPT__
    Print_Mode_Define_File_Auto(atoi(argv[12]));
#else
    Print_Mode_Define();
#endif
    if (1 == argc) { Usage(); }
    else {
        err = Setup(argc, argv);
        if (FALSE == err) {
            Run_Simulation();
        }
    }
#if defined(__RUN_MPI__)
    MPI_Finalize();
#endif
    return 0;
}
//================================================
// Program parameter
//================================================
int Setup(int argc, char* argv[])
{
    int err = FALSE;
#if defined(__PROGRAM_MODE_TV_GEN__)
    err = Setup_TV_Gen(argc, argv);
#else
    err = Setup_Ref_C(argc, argv);
#endif
    return err;
}
//================================================
// Simulation
//================================================
void Run_Simulation()
{
#if defined(__PROGRAM_MODE_TV_GEN__)
    Run_Simulation_TV_Gen();
#else
#if defined(__AUTO_LLR_OPT__)
    Run_Simulation_Local_Opt();
#else
    Run_Simulation_Ref_C();
#endif
#endif
}
//================================================
// Reference C mode
//================================================
void Run_Simulation_Ref_C()
{
    g_pECC = new ECC_Top();
    g_pECC->Init_ECC_Top(&g_ecc_info, &g_param_dec, g_myrank, g_num_process);
    g_pECC->Run_ECC_Top_Ref_C(&g_param_ref_c);
    delete g_pECC;
    delete[] g_param_dec.MN;
    delete[] g_param_ref_c.FER_local;    g_param_ref_c.FER_local = nullptr;
    delete[] g_param_ref_c.FER_MPI; g_param_ref_c.FER_MPI = nullptr;
}
//================================================
// Reference C mode
//================================================
void Run_Simulation_Local_Opt()
{
    g_LOPT = new LOCAL_OPT();
    g_LOPT->Run_Local_Opt(&g_param_ref_c, &g_ecc_info, &g_param_dec, g_myrank, g_num_process, TRUE);
    delete g_LOPT;
}
//================================================
// TV mode
//================================================
void Run_Simulation_TV_Gen()
{
    g_pECC = new ECC_Top();
    g_pECC->Init_ECC_Top(&g_ecc_info, &g_param_dec, g_myrank, g_num_process);
    g_pECC->Run_ECC_Top_TV_Gen(&g_param_tv_gen);
    delete[] g_param_dec.MN;
    delete g_pECC;
}
//================================================
// Batch file Ref-C parameter
//
//================================================
int Setup_Ref_C(int argc, char* argv[])
{
    int err = FALSE;
    g_ecc_info.matrix_sel = atoi(argv[1]);
#ifdef __AUTO_LLR_OPT__
    if (argc > 19) {
        Get_H_Filename(g_ecc_info.str_matrix_name, argv[19]);
    }
    else {
        if (LAYOUT_PRIME_512B_TLC_VSS_OFF == g_ecc_info.matrix_sel) {
            Set_H_Filename(g_ecc_info.str_matrix_name, g_ecc_info.matrix_sel);
        }
        else {
            err = TRUE;
            Print_Input_Err_Code(1);
            return err;
        }
    }
#else
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == g_ecc_info.matrix_sel) {
        Set_H_Filename(g_ecc_info.str_matrix_name, g_ecc_info.matrix_sel);
    }
    else {
        err = TRUE;
        Print_Input_Err_Code(1);
        return err;
    }
#endif
    /********************************************/
    Set_Punctured_Shortened_Bits();
    /********************************************/
    g_param_dec.init_n = atoi(argv[2]);
    if ((MODE_DEC_HD > g_param_dec.init_n) || (MODE_DEC_1_5SD < g_param_dec.init_n)) {
        err = TRUE;
        Print_Input_Err_Code(2);
        return err;
    }
    /********************************************/
    g_param_ref_c.ch_type = atoi(argv[3]);
    if ((MODE_CH_RBER > g_param_ref_c.ch_type) && (MODE_CH_3SD_FIXED < g_param_ref_c.ch_type)) {
        err = TRUE;
        Print_Input_Err_Code(3);
        return err;
    }
    /********************************************/
    if (MODE_CH_RBER == g_param_ref_c.ch_type) {
        g_param_ref_c.RBER = atof(argv[4]);
        g_param_ref_c.num_fixed_err = 0;
        g_param_ref_c.fixed_SCR = 0;
        g_param_ref_c.fixed_SER = 0;
        g_param_ref_c.fixed_erasure_ratio = 0;
    }
    else if (MODE_CH_FIXED_ERROR == g_param_ref_c.ch_type) {
        g_param_ref_c.RBER = 0;
        g_param_ref_c.num_fixed_err = atoi(argv[5]);
        g_param_ref_c.fixed_SCR = 0;
        g_param_ref_c.fixed_SER = 0;
        g_param_ref_c.fixed_erasure_ratio = 0;
    }
    else if (MODE_CH_STRONG_ERROR == g_param_ref_c.ch_type) {
        g_param_ref_c.RBER = 0;
        g_param_ref_c.num_fixed_err = atoi(argv[5]);
        g_param_ref_c.fixed_SCR = atof(argv[6]);
        g_param_ref_c.fixed_SER = atof(argv[7]);
        g_param_ref_c.fixed_erasure_ratio = 0;
    }
    else if (MODE_CH_ERASURE == g_param_ref_c.ch_type) {
        g_param_ref_c.RBER = 0;
        g_param_ref_c.num_fixed_err = atoi(argv[5]);
        g_param_ref_c.fixed_SCR = 0;
        g_param_ref_c.fixed_SER = 0;
        g_param_ref_c.fixed_erasure_ratio = atof(argv[8]);
    }
    else if (MODE_CH_3SD_FIXED == g_param_ref_c.ch_type) {
        g_param_ref_c.RBER = 0;
        g_param_ref_c.num_fixed_err = atoi(argv[5]);
        g_param_ref_c.fixed_SCR = 0;
        g_param_ref_c.fixed_SER = 0;
        g_param_ref_c.fixed_erasure_ratio = 0;
        g_param_ref_c.fixed_VSCR = atof(argv[17]);
        g_param_ref_c.fixed_NSCR = atof(argv[18]);
        g_param_ref_c.fixed_NWCR = atof(argv[19]);
        g_param_ref_c.fixed_VWCR = 1 - g_param_ref_c.fixed_VSCR - g_param_ref_c.fixed_NSCR - g_param_ref_c.fixed_NWCR,
        g_param_ref_c.fixed_VSER = atof(argv[20]);
        g_param_ref_c.fixed_NSER = atof(argv[21]);
        g_param_ref_c.fixed_NWER = atof(argv[22]);
        g_param_ref_c.fixed_VWER = 1 - g_param_ref_c.fixed_VSER - g_param_ref_c.fixed_NSER - g_param_ref_c.fixed_NWER;
    }
    else {
        printf("PARAMETER ERROR...\n");
    }
    /********************************************/
    g_param_ref_c.fn = atoi(argv[9]);
    /********************************************/
    g_param_ref_c.max_num_test = atoi(argv[10]);
    /********************************************/
    g_param_dec.BF_mode = MODE_BF_ON;    // Prime 2.1은 항상 on 사용
    //g_param_dec.BF_mode = MODE_BF_OFF;    // Prime 2.1은 항상 on 사용
    /********************************************/
    g_param_ref_c.mode_seed = atoi(argv[11]);
    /********************************************/
    g_param_ref_c.mode_init_seed = atoi(argv[12]);
    /********************************************/
    g_ecc_info.mode_all_one_cw = atoi(argv[13]);
    /********************************************/
    g_param_dec.CRC_Option_F_P = atoi(argv[14]);
    /********************************************/
    /* set iterations */
    g_param_ref_c.mode_iter = atoi(argv[15]); // 추가 2021.07.28  (MODE_ITER_DEFAULT 또는 사용자 양의 정수 입력)
    Set_Ref_C_Iteration();
    /********************************************/
    /* set simulation scenario */
    g_param_ref_c.mode_scenario = atoi(argv[16]);
    /********************************************/
    /* set test message */
    g_param_ref_c.mode_data_input = MODE_INPUT_PATTERN_RANDOM;
    //g_param_ref_c.mode_data_input = MODE_INPUT_PATTERN_ALL_ZERO;
    //g_param_ref_c.mode_data_input = MODE_INPUT_PATTERN_ALL_ONE;
    /********************************************/
    /* set result file name */
    Set_Ref_C_Result_Filename();
    /********************************************/
    FILE* fp;
#ifdef __AUTO_LLR_OPT__
    /* Auto_LLR_OPT YS */
    g_param_ref_c.LLR_MAT_idx = atoi(argv[17]);
    g_param_dec.flag_print_CSW_log = atoi(argv[18]);
    g_param_dec.rank_supercom = g_param_ref_c.mode_init_seed;
    char fn_auto_result[LEN_FILENAME];
    sprintf(fn_auto_result, "Ref_C_result_%d.txt", g_param_ref_c.mode_init_seed);
    fp = fopen(fn_auto_result, "a");
#else
    fp = stdout;
#endif
    if (g_myrank == ID_ROOT) {
        fprintf(fp, "//////////////////////////////////////////\n");
        fprintf(fp, "//          Prime ECC 3.0 Ref-C         //\n");
        fprintf(fp, "//////////////////////////////////////////\n\n");
        fprintf(fp, "* matrix_sel : %d\n", g_ecc_info.matrix_sel);
        fprintf(fp, "\t==> %s\n", g_ecc_info.str_matrix_name);
        fprintf(fp, "* Shortened bits (info): %d, Punctured bits (info): %d, Punctured bits (parity): %d\n", g_ecc_info.shortened_bit_info, g_ecc_info.punctured_bit_info, g_ecc_info.punctured_bit_parity);
        fprintf(fp, "* decoding mode : %d\n", g_param_dec.init_n);
        fprintf(fp, "* channel type : %d\n", g_param_ref_c.ch_type);
        if (MODE_CH_RBER == g_param_ref_c.ch_type) {
            fprintf(fp, "* RBER : %.2e\n", g_param_ref_c.RBER);
        }
        else if (MODE_CH_FIXED_ERROR == g_param_ref_c.ch_type) {
            fprintf(fp, "* # of fixed err : %d\n", g_param_ref_c.num_fixed_err);
        }
        else if (MODE_CH_STRONG_ERROR == g_param_ref_c.ch_type) {
            fprintf(fp, "* # of fixed error bits: %d\n", g_param_ref_c.num_fixed_err);
            fprintf(fp, "* ratio of SC : %f\n", g_param_ref_c.fixed_SCR);
            fprintf(fp, "* ratio of SE : %f\n", g_param_ref_c.fixed_SER);
        }
        else if (MODE_CH_ERASURE == g_param_ref_c.ch_type) {
            fprintf(fp, "* # of fixed error bits: %d\n", g_param_ref_c.num_fixed_err);
            fprintf(fp, "* ratio of erasure : %f\n", g_param_ref_c.fixed_erasure_ratio);
        }
        else if (MODE_CH_3SD_FIXED == g_param_ref_c.ch_type) {
            fprintf(fp, "* # of fixed error bits: %d\n", g_param_ref_c.num_fixed_err);
            fprintf(fp, "* ratio of SCR  : %f\n", g_param_ref_c.fixed_VSCR + g_param_ref_c.fixed_NSCR);
            fprintf(fp, "* ratio of SER  : %f\n", g_param_ref_c.fixed_VSER + g_param_ref_c.fixed_NSER);
            fprintf(fp, "* ratio of VSCR : %f\n", g_param_ref_c.fixed_VSCR);
            fprintf(fp, "* ratio of NSCR : %f\n", g_param_ref_c.fixed_NSCR);
            fprintf(fp, "* ratio of NWCR : %f\n", g_param_ref_c.fixed_NWCR);
            fprintf(fp, "* ratio of VWCR : %f\n", g_param_ref_c.fixed_VWCR);
            fprintf(fp, "* ratio of VSER : %f\n", g_param_ref_c.fixed_VSER);
            fprintf(fp, "* ratio of NSER : %f\n", g_param_ref_c.fixed_NSER);
            fprintf(fp, "* ratio of NWER : %f\n", g_param_ref_c.fixed_NWER);
        }
        fprintf(fp, "* # of failed tests : %d\n", g_param_ref_c.fn);
        fprintf(fp, "* # of maximum tests : %d\n", g_param_ref_c.max_num_test);
        fprintf(fp, "* HBF mode : %d, SW_Threshold: %d \n", g_param_dec.BF_mode, SW_TH_BF_DEFAULT);
        fprintf(fp, "* Seed mode : %d\n", g_param_ref_c.mode_seed);
        fprintf(fp, "* Init seed mode : %d\n", g_param_ref_c.mode_init_seed);
        fprintf(fp, "* All one codeword mode (0: all zero codeword, 1: all one codeword): %d\n", g_ecc_info.mode_all_one_cw);
        fprintf(fp, "* CRC mode (0: full, 1: partial, 2: genie, 3: partial genie, 4: partial last only): %d\n", g_param_dec.CRC_Option_F_P);
#ifdef __AUTO_LLR_OPT__
        fprintf(fp, "* MN_num : %d\n", g_param_dec.MN_num);
        fprintf(fp, "* iteration number : ");
        for (int n = 0; n < g_param_dec.MN_num; n++) {
            fprintf(fp, "%d ", g_param_dec.MN[n]);
        }
        fprintf(fp, "\n");
#endif
        fprintf(fp, "* Result file name: %s\n", g_param_ref_c.str_result_name_4KB);
        fprintf(fp, "* mode_scenario mode : %d\n\n", g_param_ref_c.mode_scenario);
    }
#ifdef __AUTO_LLR_OPT__
    fclose(fp);
#endif
    return err;
}
//#ifdef __AUTO_LLR_OPT__
////================================================
//// Batch file Ref-C parameter
////
////================================================
//int Setup_Ref_C_Auto(int argc, char* argv[])
//{
//  int err = FALSE;
//
//  /********************************************/
//  g_ecc_info.matrix_sel = atoi(argv[1]);
//  if (LAYOUT_PRIME_512B_TLC_VSS_OFF <= g_ecc_info.matrix_sel) {
//      Set_H_Filename(g_ecc_info.str_matrix_name, g_ecc_info.matrix_sel);
//  }
//  else {
//      err = TRUE;
//      Print_Input_Err_Code(1);
//      return err;
//  }
//  /********************************************/
//  Set_Punctured_Shortened_Bits();
//  /********************************************/
//  g_param_dec.init_n = atoi(argv[2]);
//  /********************************************/
//  g_param_ref_c.ch_type = atoi(argv[3]);
//  /********************************************/
//  if (MODE_CH_RBER == g_param_ref_c.ch_type) {
//      g_param_ref_c.RBER = atof(argv[4]);
//      g_param_ref_c.num_fixed_err = 0;
//      g_param_ref_c.fixed_SCR = 0;
//      g_param_ref_c.fixed_SER = 0;
//      g_param_ref_c.fixed_erasure_ratio = 0;
//  }
//  else if (MODE_CH_FIXED_ERROR == g_param_ref_c.ch_type) {
//      g_param_ref_c.RBER = 0;
//      g_param_ref_c.num_fixed_err = atoi(argv[5]);
//      g_param_ref_c.fixed_SCR = 0;
//      g_param_ref_c.fixed_SER = 0;
//      g_param_ref_c.fixed_erasure_ratio = 0;
//  }
//  else if (MODE_CH_STRONG_ERROR == g_param_ref_c.ch_type) {
//      g_param_ref_c.RBER = 0;
//      g_param_ref_c.num_fixed_err = atoi(argv[5]);
//      g_param_ref_c.fixed_SCR = atof(argv[6]);
//      g_param_ref_c.fixed_SER = atof(argv[7]);
//      g_param_ref_c.fixed_erasure_ratio = 0;
//  }
//  else if (MODE_CH_ERASURE == g_param_ref_c.ch_type) {
//      g_param_ref_c.RBER = 0;
//      g_param_ref_c.num_fixed_err = atoi(argv[5]);
//      g_param_ref_c.fixed_SCR = 0;
//      g_param_ref_c.fixed_SER = 0;
//      g_param_ref_c.fixed_erasure_ratio = atof(argv[8]);
//  }
//  else if (MODE_CH_3SD_FIXED == g_param_ref_c.ch_type) {
//      g_param_ref_c.RBER = 0;
//      g_param_ref_c.num_fixed_err = atoi(argv[5]);
//      g_param_ref_c.fixed_SCR = 0;
//      g_param_ref_c.fixed_SER = 0;
//      g_param_ref_c.fixed_erasure_ratio = 0;
//
//      g_param_ref_c.fixed_VSCR = atof(argv[17]);
//      g_param_ref_c.fixed_NSCR = atof(argv[18]);
//      g_param_ref_c.fixed_NWCR = atof(argv[19]);
//      g_param_ref_c.fixed_VWCR = 1 - g_param_ref_c.fixed_VSCR - g_param_ref_c.fixed_NSCR - g_param_ref_c.fixed_NWCR,
//      g_param_ref_c.fixed_VSER = atof(argv[20]);
//      g_param_ref_c.fixed_NSER = atof(argv[21]);
//      g_param_ref_c.fixed_NWER = atof(argv[22]);
//      g_param_ref_c.fixed_VWER = 1 - g_param_ref_c.fixed_VSER - g_param_ref_c.fixed_NSER - g_param_ref_c.fixed_NWER;
//  }
//  /********************************************/
//  g_param_ref_c.fn = atoi(argv[9]);
//  /********************************************/
//  g_param_ref_c.max_num_test = atoi(argv[10]);
//  /********************************************/
//  g_param_dec.BF_mode = MODE_BF_ON;    // Prime 2.1
//  /********************************************/
//  g_param_ref_c.mode_seed = atoi(argv[11]);
//  /********************************************/
//  g_param_ref_c.mode_init_seed = atoi(argv[12]);
//  /********************************************/
//  g_ecc_info.mode_all_one_cw = atoi(argv[13]);
//  /********************************************/
//  g_param_dec.CRC_Option_F_P = atoi(argv[14]); // 2021.07.28
//  /********************************************/
//  /* set iterations */
//  g_param_ref_c.mode_iter = atoi(argv[15]); // 2021.07.28  (MODE_ITER_DEFAULT
//  Set_Ref_C_Iteration();
//  /********************************************/
//  /* set test message */
//  g_param_ref_c.mode_data_input = MODE_INPUT_PATTERN_RANDOM;
//  //g_param_ref_c.mode_data_input = MODE_INPUT_PATTERN_ALL_ZERO;
//  //g_param_ref_c.mode_data_input = MODE_INPUT_PATTERN_ALL_ONE;
//  /********************************************/
//  /* set result file name */
//  Set_Ref_C_Result_Filename();
//  /********************************************/
//
//  /* Auto_LLR_OPT YS */
//  g_param_ref_c.LLR_MAT_idx = atoi(argv[17]);
//  g_param_dec.flag_print_CSW_log = atoi(argv[18]);
//  g_param_dec.rank_supercom = g_param_ref_c.mode_init_seed;
//
//  char fn_auto_result[LEN_FILENAME];
//  sprintf(fn_auto_result, "Ref_C_result_%d.txt", g_param_ref_c.mode_init_seed);
//  FILE* fp;
//
//  fp = fopen(fn_auto_result, "a");
//
//
//  fprintf(fp, "//////////////////////////////////////////\n");
//  fprintf(fp, "//          Prime ECC 2.4 Ref-C         //\n");
//  fprintf(fp, "//////////////////////////////////////////\n\n");
//  fprintf(fp, "* matrix_sel : %d\n", g_ecc_info.matrix_sel);
//  fprintf(fp, "\t==> %s\n", g_ecc_info.str_matrix_name);
//  fprintf(fp, "* Shortened bits (info): %d, Punctured bits (info): %d, Punctured bits (parity): %d\n", g_ecc_info.shortened_bit_info, g_ecc_info.punctured_bit_info, g_ecc_info.punctured_bit_parity);
//
//  if ((MODE_DEC_HD <= g_param_dec.init_n) && (MODE_DEC_1_5SD >= g_param_dec.init_n)) {
//      fprintf(fp, "* decoding mode : %d\n", g_param_dec.init_n);
//  }
//  else {
//      err = TRUE;
//      Print_Input_Err_Code(2);
//      return err;
//  }
//
//  if ((MODE_CH_RBER <= g_param_ref_c.ch_type) && (MODE_CH_3SD_FIXED >= g_param_ref_c.ch_type)) {
//      fprintf(fp, "* channel type : %d\n", g_param_ref_c.ch_type);
//  }
//  else {
//      err = TRUE;
//      Print_Input_Err_Code(3);
//      return err;
//  }
//
//  if (MODE_CH_RBER == g_param_ref_c.ch_type) {
//      fprintf(fp, "* RBER : %.2e\n", g_param_ref_c.RBER);
//  }
//  else if (MODE_CH_FIXED_ERROR == g_param_ref_c.ch_type) {
//      fprintf(fp, "* # of fixed err : %d\n", g_param_ref_c.num_fixed_err);
//  }
//  else if (MODE_CH_STRONG_ERROR == g_param_ref_c.ch_type) {
//      fprintf(fp, "* # of fixed error bits: %d\n", g_param_ref_c.num_fixed_err);
//      fprintf(fp, "* ratio of SC : %f\n", g_param_ref_c.fixed_SCR);
//      fprintf(fp, "* ratio of SE : %f\n", g_param_ref_c.fixed_SER);
//  }
//  else if (MODE_CH_ERASURE == g_param_ref_c.ch_type) {
//      fprintf(fp, "* # of fixed error bits: %d\n", g_param_ref_c.num_fixed_err);
//      fprintf(fp, "* ratio of erasure : %f\n", g_param_ref_c.fixed_erasure_ratio);
//  }
//  else if (MODE_CH_3SD_FIXED == g_param_ref_c.ch_type) {
//      fprintf(fp, "* # of fixed error bits: %d\n", g_param_ref_c.num_fixed_err);
//      fprintf(fp, "* ratio of SCR  : %f\n", g_param_ref_c.fixed_VSCR + g_param_ref_c.fixed_NSCR);
//      fprintf(fp, "* ratio of SER  : %f\n", g_param_ref_c.fixed_VSER + g_param_ref_c.fixed_NSER);
//  return err;
//}
//#endif // __AUTO_LLR_OPT__
//================================================
// Batch file TV gen parameter
//
//================================================
int Setup_TV_Gen(int argc, char* argv[])
{
    int err = FALSE;
    int enc_only = FALSE;
    printf("//////////////////////////////////////////\n");
    printf("//          Prime ECC 3.1 TV Gen        //\n");
    printf("//      Final update: 2026-04-02        //\n");
    printf("//////////////////////////////////////////\n\n");
    /********************************************/
    g_ecc_info.matrix_sel = atoi(argv[1]);
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF <= g_ecc_info.matrix_sel) {
        // Predefined H matrix index
        Set_H_Filename(g_ecc_info.str_matrix_name, g_ecc_info.matrix_sel);
    }
    else {
        err = TRUE;
        Print_Input_Err_Code(1);
        return err;
    }
    printf("* Matrix selection : %d\n", g_ecc_info.matrix_sel);
    /********************************************/
    Set_Punctured_Shortened_Bits();
    /********************************************/
#if defined (__ENC_TV_ONLY__)
    enc_only = TRUE;
    printf("* Encoder only\n");
#endif
    /********************************************/
    g_param_dec.init_n = atoi(argv[2]);
    if ((MODE_DEC_HD <= g_param_dec.init_n) && (MODE_DEC_1_5SD >= g_param_dec.init_n)) {
        if (FALSE == enc_only) {
            printf("* Decoding mode (1: HD, 2: 2SD, 3: 3SD, 4: 1.5SD(x)): %d\n", g_param_dec.init_n);
        }
    }
    else {
        err = TRUE;
        Print_Input_Err_Code(2);
        return err;
    }
    /********************************************/
    g_param_tv_gen.TS_idx = atoi(argv[3]);
    if (FALSE == enc_only) {
        printf("* Test case (normal test ==> 1: HD, 2: 2SD, 3: 3SD, 4: 1.5SD(x))\n");
        printf("              (mass test   ==> 11: HD, 21: 2SD, 31: 3SD, 41: 1.5SD(x))\n");
        printf("              (other test cases: see header file.\n");
        printf("\t==> %d\n", g_param_tv_gen.TS_idx);
    }
    /********************************************/
    g_param_dec.BF_mode = MODE_BF_ON;
    //g_param_dec.BF_mode = MODE_BF_OFF;
    printf("* BF mode (0: off, 1: on): %d\n", g_param_dec.BF_mode);
    /********************************************/
    g_ecc_info.mode_all_one_cw = atoi(argv[4]);
    printf("* All one codeword mode (0: all zero codeword, 1: all one codeword): %d\n", g_ecc_info.mode_all_one_cw);
    /********************************************/
    // FULL CRC
#if defined (__FULL_CRC__)
    g_param_dec.CRC_Option_F_P = MODE_CRC_FULL;
#else
    g_param_dec.CRC_Option_F_P = MODE_CRC_PARTIAL_LAST_ONLY;
#endif
    //g_param_dec.CRC_Option_F_P = atoi(argv[5]);//QQQ
    printf("* CRC mode (0: full, 1: partial, 2: genie, 3: partial genie, 4: partial last only): %d\n", g_param_dec.CRC_Option_F_P);
    /********************************************/
    // 4KB mode
    g_param_tv_gen.mode_scenario = 0;
    //g_param_tv_gen.mode_scenario = atoi(argv[6]);
    printf("* mode_scenario mode : %d\n", g_param_tv_gen.mode_scenario);
    /********************************************/
    /********************************************/
    g_param_tv_gen.mode_rand = MODE_RANDOM_TYPE_XOR_25; /* Linux XOR_25 2021.07.
    g_param_tv_gen.mode_init_seed = MODE_SEED_INIT_FIXED;
    /********************************************/
    if ((MODE_SCENARIO_ENC_4KB_DEC_4KB == g_param_tv_gen.mode_scenario)) {
        Set_TV_Scenario_4KB();
    }
    if ((MODE_TV_CASE_HD_XOR25_SEED_FIXED == g_param_tv_gen.TS_idx) ||
        (MODE_TV_CASE_HD_XOR25_SEED_RBER == g_param_tv_gen.TS_idx) ||
        (MODE_TV_CASE_2SD_XOR25_SEED_RBER == g_param_tv_gen.TS_idx) ||
        (MODE_TV_CASE_2SD_XOR25_SEED_STRONG_ERROR == g_param_tv_gen.TS_idx) ||
        (MODE_TV_CASE_3SD_XOR25_SEED_RBER == g_param_tv_gen.TS_idx) ||
        (MODE_TV_CASE_1_5SD_XOR25_SEED_ERASURE == g_param_tv_gen.TS_idx)) {
        g_param_tv_gen.ch_type = atoi(argv[7]);
        g_param_tv_gen.RBER = atof(argv[8]);
        g_param_tv_gen.num_fixed_err = atoi(argv[9]);
        g_param_tv_gen.fixed_SCR = atof(argv[10]);
        g_param_tv_gen.fixed_SER = atof(argv[11]);
        g_param_tv_gen.fixed_erasure_ratio = atof(argv[12]);
    }
    Set_Ref_C_Iteration();
    return err;
}
//================================================
// Fixed H matrix file
// (U folder)
//================================================
void Set_H_Filename(char* buf_4KB, int matrix_sel)
{
    char str_folder1[LEN_FILENAME];
    char str_folder2[LEN_FILENAME];
    Init_Buf(str_folder1, LEN_FILENAME);
    Init_Buf(str_folder2, LEN_FILENAME);
#if defined(__WIN_OS__)
#ifdef __AUTO_LLR_OPT__
    sprintf(str_folder1, "H_Matrix\\");
    sprintf(str_folder2, "");
#else
    sprintf(str_folder1, "H_Matrix\\");
    sprintf(str_folder2, "");
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == matrix_sel) {
#ifdef __3_BLK_PUNCT__
        sprintf(str_folder2, "18_by_147_DvMax3\\");
#endif // __3_BLK_PUNCT__
    }
    else {
        printf("Check H matrix folder\n");
    }
#endif
#else
#ifdef __AUTO_LLR_OPT__
    sprintf(str_folder1, "./H_Matrix/");
    sprintf(str_folder2, "");
#else
    sprintf(str_folder1, "");
    sprintf(str_folder2, "");
#endif
#endif
    Init_Buf(buf_4KB, LEN_FILENAME);
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == matrix_sel) {
#if defined (__SHPUNC_PATTERN_1__)
    sprintf(buf_4KB, "%s%sH_4203_1.txt", str_folder1, str_folder2);
#elif defined (__SHPUNC_PATTERN_2__)
    sprintf(buf_4KB, "%s%sH_4203_2.txt", str_folder1, str_folder2);
#elif defined (__SHPUNC_PATTERN_3__)
    sprintf(buf_4KB, "%s%sH_4203_3.txt", str_folder1, str_folder2);
#elif defined (__SHPUNC_PATTERN_4__)
        sprintf(buf_4KB, "%s%sH_4203_4.txt", str_folder1, str_folder2);
#else
    //sprintf(buf_4KB, "%s%sH_4203.txt", str_folder1, str_folder2);
    sprintf(buf_4KB, "%s%sH_402091.txt", str_folder1, str_folder2);
#endif // __SHPUNC_PATTERN_1__
    }
}
void Get_H_Filename(char* buf_4KB, char* input_H_name) {
    char str_folder1[LEN_FILENAME];
    Init_Buf(str_folder1, LEN_FILENAME);
#if defined(__WIN_OS__)
#ifdef __AUTO_LLR_OPT__
    sprintf(str_folder1, "H_Matrix\\");
#else
    sprintf(str_folder1, "H_Matrix\\");
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == g_ecc_info.matrix_sel) {
#ifdef __3_BLK_PUNCT__
        sprintf(str_folder2, "18_by_147_DvMax3\\");
#endif // __3_BLK_PUNCT__
    else {
        printf("Check H matrix folder\n");
    }
#endif
#else
#ifdef __AUTO_LLR_OPT__
    sprintf(str_folder1, "./H_Matrix/");
#else
    sprintf(str_folder1, "");
#endif
#endif
    Init_Buf(buf_4KB, LEN_FILENAME);
    sprintf(buf_4KB, "%s%s.txt", str_folder1, input_H_name);
}
//================================================
// Layout puncturing, shortening bit
//
//================================================
void Set_Punctured_Shortened_Bits()
{
    // 4KB LDPC info
    g_ecc_info.shortened_bit_info = SHORTENED_BIT_PRIME_INFO_4KB;
    g_ecc_info.punctured_bit_info = PUNCTURED_BIT_PRIME_INFO_4KB;
    g_ecc_info.punctured_bit_parity = PUNCTURED_BIT_PRIME_PARITY_4KB;
    g_ecc_info.shortened_bit_info_offset_end = CRC_LEN; // 10B
}
//================================================
// Ref-C
//================================================
void Set_Ref_C_Result_Filename()
{
    char buf[LEN_FILENAME];
    Init_Buf(buf, LEN_FILENAME);
    if (MODE_CH_RBER == g_param_ref_c.ch_type) {
        sprintf(buf, "H_%d_CH_%d_E%.2e_init_n_%d_seed_%d", g_ecc_info.matrix_sel, g_param_ref_c.ch_type, g_param_ref_c.RBER, g_param_dec.init_n, g_param_ref_c.mode_init_seed);
    }
    else if (MODE_CH_FIXED_ERROR == g_param_ref_c.ch_type) {
        sprintf(buf, "H_%d_CH_%d_E%d_init_n_%d_seed_%d", g_ecc_info.matrix_sel, g_param_ref_c.ch_type, g_param_ref_c.num_fixed_err, g_param_dec.init_n, g_param_ref_c.mode_init_seed);
    }
    else if (MODE_CH_STRONG_ERROR == g_param_ref_c.ch_type) {
        sprintf(buf, "H_%d_CH_%d_E%d_SC_%.2f_SE_%.2f_init_n_%d_seed_%d",
            g_ecc_info.matrix_sel, g_param_ref_c.ch_type, g_param_ref_c.num_fixed_err, g_param_ref_c.fixed_SCR, g_param_ref_c.fixed_SER, g_param_dec.init_n, g_param_ref_c.mode_init_seed);
    }
    else if (MODE_CH_ERASURE == g_param_ref_c.ch_type) {
        sprintf(buf, "H_%d_CH_%d_E%d_Erasure_%.3f_init_n_%d", g_ecc_info.matrix_sel, g_param_ref_c.ch_type, g_param_ref_c.num_fixed_err, g_param_ref_c.fixed_erasure_ratio, g_param_dec.init_n, g_param_ref_c.mode_init_seed);
    }
    else if (MODE_CH_3SD_FIXED == g_param_ref_c.ch_type) {
        sprintf(buf, "H_%d_CH_%d_E%d_%.4f_%.4f_%.4f_%.4f_%.4f_%.4f_init_n_%d_seed_%d",
            g_ecc_info.matrix_sel, g_param_ref_c.ch_type, g_param_ref_c.num_fixed_err,
            g_param_ref_c.fixed_VSCR, g_param_ref_c.fixed_NSCR, g_param_ref_c.fixed_NWCR,
            g_param_ref_c.fixed_VSER, g_param_ref_c.fixed_NSER, g_param_ref_c.fixed_NWER,
            g_param_dec.init_n, g_param_ref_c.mode_init_seed);
    }
    sprintf(g_param_ref_c.str_result_name_4KB, "result_4KB_S_%d_%s.txt", g_param_ref_c.mode_scenario, buf);
}
//================================================
// Ref-C iteration
// main (2021.07.28)
//================================================
void Set_Ref_C_Iteration()
{
#ifndef __AUTO_LLR_OPT__
    if (MODE_ITER_DEFAULT == g_param_ref_c.mode_iter) {
        /* */
        if (MODE_DEC_HD == g_param_dec.init_n) {
            g_param_dec.MN_num = ITER_MAX_REF_C_HD_NUM;
            g_param_dec.MN = new int[g_param_dec.MN_num];
#if defined (__MAX_ITER_LIMITED__)
            g_param_dec.MN[0] = 0;
            g_param_dec.MN[1] = 0;
            g_param_dec.MN[2] = 0;
            g_param_dec.MN[3] = 0;
            g_param_dec.MN[4] = 40;
#else
            g_param_dec.MN[0] = ITER_MAX_HBF;
            g_param_dec.MN[1] = ITER_MAX_HD_1_PRIME;
            g_param_dec.MN[2] = ITER_MAX_HD_2_PRIME;
            g_param_dec.MN[3] = ITER_MAX_HD_3_PRIME;
            g_param_dec.MN[4] = ITER_MAX_HD_PRIME;
#endif
        }
        else if (MODE_DEC_2SD == g_param_dec.init_n) {
            g_param_dec.MN_num = ITER_MAX_REF_C_2SD_NUM;
            g_param_dec.MN = new int[g_param_dec.MN_num];
#if defined (__MAX_ITER_LIMITED__)
#else
            g_param_dec.MN[0] = ITER_MAX_2SD_1_PRIME;
            g_param_dec.MN[1] = ITER_MAX_2SD_2_PRIME;
            g_param_dec.MN[2] = ITER_MAX_2SD_3_PRIME;
            g_param_dec.MN[3] = ITER_MAX_2SD_4_PRIME;
            g_param_dec.MN[4] = ITER_MAX_2SD_5_PRIME;
            g_param_dec.MN[5] = ITER_MAX_2SD_6_PRIME;
            g_param_dec.MN[6] = ITER_MAX_2SD_7_PRIME;
            g_param_dec.MN[7] = ITER_MAX_2SD_8_PRIME;
            g_param_dec.MN[8] = ITER_MAX_2SD_PRIME;
#endif
        }
        else if (MODE_DEC_3SD == g_param_dec.init_n) {
            g_param_dec.MN_num = ITER_MAX_REF_C_3SD_NUM;
            g_param_dec.MN = new int[g_param_dec.MN_num];
#if defined (__MAX_ITER_LIMITED__)
            g_param_dec.MN[0] = 0;
            g_param_dec.MN[1] = 0;
            g_param_dec.MN[2] = 100;
#else
            /* ITER_MAX_REF_C_3SD_NUM == 2 */
            //g_param_dec.MN[0] = ITER_MAX_3SD_1_PRIME;
            //g_param_dec.MN[1] = ITER_MAX_3SD_PRIME;
            /* ITER_MAX_REF_C_3SD_NUM == 9 */
            g_param_dec.MN[0] = ITER_MAX_3SD_1_PRIME;
            g_param_dec.MN[4] = ITER_MAX_3SD_5_PRIME;
            g_param_dec.MN[5] = ITER_MAX_3SD_6_PRIME;
            g_param_dec.MN[6] = ITER_MAX_3SD_7_PRIME;
            g_param_dec.MN[7] = ITER_MAX_3SD_8_PRIME;
            g_param_dec.MN[8] = ITER_MAX_3SD_9_PRIME;
            g_param_dec.MN[9] = ITER_MAX_3SD_10_PRIME;
            g_param_dec.MN[10] = ITER_MAX_3SD_11_PRIME;
            g_param_dec.MN[11] = ITER_MAX_3SD_12_PRIME;
            g_param_dec.MN[12] = ITER_MAX_3SD_13_PRIME;
            g_param_dec.MN[13] = ITER_MAX_3SD_14_PRIME;
            g_param_dec.MN[14] = ITER_MAX_3SD_PRIME;
#endif
        }
        else if (MODE_DEC_1_5SD == g_param_dec.init_n) {
            g_param_dec.MN_num = ITER_MAX_REF_C_1_5SD_NUM;
            g_param_dec.MN = new int[g_param_dec.MN_num];
            g_param_dec.MN[0] = ITER_MAX_HD_PRIME;
        }
    }
    else {
        /* */
        g_param_dec.MN_num = 1;
        g_param_dec.MN = new int[g_param_dec.MN_num];
        g_param_dec.MN[0] = g_param_ref_c.mode_iter;
    }
#endif
}
//================================================
// TV (4KB)
//================================================
void Set_TV_Scenario_4KB()
{
    int mass_case = TV_MASS_CASE_FACTOR;
    int MN;
    int TV_test;
    int err_case = 1;
    int MN_default = 1;
    /* fixed iteration */
    g_param_dec.MN_num = 1;
    g_param_dec.MN = new int[g_param_dec.MN_num];
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF <= g_ecc_info.matrix_sel) {
        if (MODE_DEC_HD == g_param_dec.init_n) { MN_default = ITER_MAX_HD_PRIME; }
        else if (MODE_DEC_2SD == g_param_dec.init_n) { MN_default = ITER_MAX_2SD_PRIME; }
        else if (MODE_DEC_3SD == g_param_dec.init_n) { MN_default = ITER_MAX_3SD_PRIME; }
        else if (MODE_DEC_1_5SD == g_param_dec.init_n) { MN_default = ITER_MAX_HD_PRIME; }
        else { MN_default = 1; }
    }
    if ((MODE_TV_CASE_HD_NORMAL == g_param_tv_gen.TS_idx) || (MODE_TV_CASE_HD_MASS == g_param_tv_gen.TS_idx)) {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_RANDOM;
        err_case = TV_ERROR_PATTERN_SIZE_DEFAULT;
    }
    else if ((MODE_TV_CASE_HD_A == g_param_tv_gen.TS_idx) || (MODE_TV_CASE_HD_B == g_param_tv_gen.TS_idx)) {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_RANDOM;
        err_case = TV_ERROR_PATTERN_SIZE_HD_SPEACIAL;
    }
    else if ((MODE_TV_CASE_HD_C == g_param_tv_gen.TS_idx) || (MODE_TV_CASE_HD_D == g_param_tv_gen.TS_idx) || (MODE_TV_CASE_HD_E == g_param_tv_gen.TS_idx)) {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_FIXED;
        err_case = TV_ERROR_PATTERN_SIZE_HD_SPEACIAL;
    }
    else if ((MODE_TV_CASE_HD_POWER_0 <= g_param_tv_gen.TS_idx) && (MODE_TV_CASE_HD_POWER_500 >= g_param_tv_gen.TS_idx)) {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_RANDOM;
        err_case = TV_ERROR_PATTERN_SIZE_HD_SPEACIAL;
    }
    else if ((MODE_TV_CASE_2SD_NORMAL == g_param_tv_gen.TS_idx) || (MODE_TV_CASE_2SD_MASS == g_param_tv_gen.TS_idx)) {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_RANDOM;
        err_case = TV_ERROR_PATTERN_SIZE_DEFAULT;
    }
    else if (MODE_TV_CASE_2SD_A == g_param_tv_gen.TS_idx) {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_RANDOM;
        err_case = TV_ERROR_PATTERN_SIZE_DEFAULT;
    }
    else if ((MODE_TV_CASE_2SD_B == g_param_tv_gen.TS_idx) || (MODE_TV_CASE_2SD_C == g_param_tv_gen.TS_idx)) {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_FIXED;
        err_case = TV_ERROR_PATTERN_SIZE_2SD_SPEACIAL;
    }
    else if ((MODE_TV_CASE_3SD_NORMAL == g_param_tv_gen.TS_idx) || ((MODE_TV_CASE_3SD_MASS == g_param_tv_gen.TS_idx))) {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_RANDOM;
        err_case = TV_ERROR_PATTERN_SIZE_DEFAULT;
    }
    else if ((MODE_TV_CASE_3SD_A == g_param_tv_gen.TS_idx) || ((MODE_TV_CASE_3SD_B == g_param_tv_gen.TS_idx))) {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_RANDOM;
        err_case = TV_ERROR_PATTERN_SIZE_DEFAULT;
    }
    else if ((MODE_TV_CASE_3SD_C == g_param_tv_gen.TS_idx) || ((MODE_TV_CASE_3SD_D == g_param_tv_gen.TS_idx))) {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_FIXED;
        err_case = TV_ERROR_PATTERN_SIZE_3SD_SPEACIAL;
    }
    else if ((MODE_TV_CASE_1_5SD_NORMAL == g_param_tv_gen.TS_idx) || (MODE_TV_CASE_1_5SD_MASS == g_param_tv_gen.TS_idx)) {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_RANDOM;
        err_case = TV_ERROR_PATTERN_SIZE_DEFAULT;
    }
    else if ((MODE_TV_CASE_HD_FIXED_DIN == g_param_tv_gen.TS_idx) ||
        (MODE_TV_CASE_2SD_FIXED_DIN == g_param_tv_gen.TS_idx) ||
        (MODE_TV_CASE_3SD_FIXED_DIN == g_param_tv_gen.TS_idx) ||
        (MODE_TV_CASE_1_5SD_FIXED_DIN == g_param_tv_gen.TS_idx)) {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_FIXED;
        err_case = 1;
    }
    else {
        MN = MN_default;
        TV_test = MODE_TV_ERR_POS_FIXED;
        err_case = 1;
    }
    if ((MODE_TV_CASE_HD_MASS == g_param_tv_gen.TS_idx) ||
        (MODE_TV_CASE_2SD_MASS == g_param_tv_gen.TS_idx) ||
        (MODE_TV_CASE_3SD_MASS == g_param_tv_gen.TS_idx) ||
        (MODE_TV_CASE_1_5SD_MASS == g_param_tv_gen.TS_idx)) {
        err_case *= mass_case;
    }
#if defined (__ENC_TV_ONLY__)
    err_case = 1;
#endif
    g_param_dec.MN[0] = MN;
    g_param_tv_gen.mode_error_pos = TV_test;
    g_param_tv_gen.err_case = err_case;
    g_param_tv_gen.mass_case = mass_case;
}
//================================================
// Fix layout
//================================================
void Print_COH()
{
    if (g_myrank == ID_ROOT) {
        printf("1.  512B TLC VSS off            (11.95%%)\n");
        printf("2.  512B TLC VSS on             (11.09%%)\n");
        printf("11. 520B TLC VSS off            (10.24%%)\n");
        printf("12. 520B TLC VSS on             (9.40%%)\n");
        printf("\n");
        printf("100. Arbitrary H Matrix (Ref-C mode only)\n");
    }
}
//================================================
//
//
//================================================
void Print_Input_Err_Code(int code)
{
    if (code == 1) { printf("INPUT ERROR : H matrix\n"); }
    else if (code == 2) { printf("INPUT ERROR : decoding mode\n"); }
    else if (code == 3) { printf("INPUT ERROR : channel type\n"); }
}
//================================================
//
//================================================
void Usage()
{
    Print_COH();
}
void Print_Mode_Define()
{
#if defined (__PROGRAM_MODE_REF_C__)
    printf("__PROGRAM_MODE_REF_C__\tON\n");
#else
    printf("__PROGRAM_MODE_REF_C__\tOFF\n");
#endif
#if defined (__AUTO_LLR_OPT__)
    printf("__AUTO_LLR_OPT__\tON\n");
#else
    printf("__AUTO_LLR_OPT__\tOFF\n");
#endif
#if defined (__RUN_MPI__)
    printf("__RUN_MPI__\tON\n");
#else
    printf("__RUN_MPI__\tOFF\n");
#endif
#if defined (__12META__)
    printf("__12META__\tON\n");
#else
    printf("__12META__\tOFF\n");
#endif
#if defined (__WIN_OS__)
    printf("__WIN_OS__\tON\n");
#else
    printf("__WIN_OS__\tOFF\n");
#endif
#if defined (__CORNER_CHECKER__)
    printf("__CORNER_CHECKER__\tON\n");
#endif
#if defined (__ECC_TV_ITER__)
    printf("__ECC_TV_ITER__\tON\n");
#endif
#if defined (__ENC_TV_ONLY__)
    printf("__ENC_TV_ONLY__\tON\n");
#endif
#if defined (__FIXED_SECTOR_NUMBER__)
    printf("__FIXED_SECTOR_NUMBER__\tON\n");
#endif
    printf("\n");
}
void Print_Mode_Define_File_Auto(int n)
{
    char fn_auto_result[LEN_FILENAME];
    sprintf(fn_auto_result, "Ref_C_result_%d.txt", n);
    FILE* fp_auto_result = fopen(fn_auto_result, "w");
#if defined (__PROGRAM_MODE_REF_C__)
    fprintf(fp_auto_result, "__PROGRAM_MODE_REF_C__\tON\n");
#else
    fprintf(fp_auto_result, "__PROGRAM_MODE_REF_C__\tOFF\n");
#endif
#if defined (__AUTO_LLR_OPT__)
    fprintf(fp_auto_result, "__AUTO_LLR_OPT__\tON\n");
#else
    fprintf(fp_auto_result, "__AUTO_LLR_OPT__\tOFF\n");
#endif
#if defined (__RUN_MPI__)
    fprintf(fp_auto_result, "__RUN_MPI__\tON\n");
#else
    fprintf(fp_auto_result, "__RUN_MPI__\tOFF\n");
#endif
#if defined (__12META__)
    fprintf(fp_auto_result, "__12META__\tON\n");
#else
    fprintf(fp_auto_result, "__12META__\tOFF\n");
#endif
#if defined (__WIN_OS__)
    fprintf(fp_auto_result, "__WIN_OS__\tON\n");
#else
    fprintf(fp_auto_result, "__WIN_OS__\tOFF\n");
#endif
#if defined (__CORNER_CHECKER__)
    fprintf(fp_auto_result, "__CORNER_CHECKER__\tON\n");
#endif
#if defined (__ECC_TV_ITER__)
    fprintf(fp_auto_result, "__ECC_TV_ITER__\tON\n");
#endif
#if defined (__ENC_TV_ONLY__)
    fprintf(fp_auto_result, "__ENC_TV_ONLY__\tON\n");
#endif
#if defined (__FIXED_SECTOR_NUMBER__)
    fprintf(fp_auto_result, "__FIXED_SECTOR_NUMBER__\tON\n");
#endif
    fprintf(fp_auto_result, "\n");
    fclose(fp_auto_result);
}
