#include "Local_Opt.h"
using namespace std;
LOCAL_OPT::LOCAL_OPT()
{
    g_pECC = NULL;
    m_ref_c = NULL;
    m_ecc_info = NULL;
    m_param_dec = NULL;
}
LOCAL_OPT::~LOCAL_OPT()
{
    delete[] m_param_LLR.dv_from;
    delete[] m_param_LLR.dv_to;
    delete[] m_param_LLR.num_set_each_group;
    delete[] m_param_LLR.type_each_group;
    delete[] m_param_LLR.restart_iter;
    delete[] m_param_LLR.max_value;
    delete[] m_param_LLR.min_value;
    delete[] m_param_LLR.CSW_thr;
    delete[] m_param_LLR.iter_start;
    delete[] m_param_LLR.iter_end;
    for (int i = 0; i < m_param_LLR.num_row; i++) {
        delete[] m_param_LLR.LLR_MATRIX[i];
    }
    delete[] m_param_LLR.LLR_MATRIX;
}
void LOCAL_OPT::Run_Local_Opt(PARAM_REF_C* p_ref_c, ECC_INFO* ecc_info, PARAM_DEC* param_dec, int myrank, int num_process, int signal) {
    m_my_rank = myrank;
    m_num_process = num_process;
    m_ref_c = p_ref_c;
    m_ecc_info = ecc_info;
    m_param_dec = param_dec;
    m_param_OPT.matrix_idx = p_ref_c->LLR_MAT_idx;
    Read_LLR_info_Auto(&m_param_LLR, &m_param_OPT);
    Run_Simu_Curr_LLR();
}
void LOCAL_OPT::Run_Simu_Curr_LLR() {
#if defined(__RUN_MPI__)
    for (int i = 0; i < m_param_LLR.num_row; i++) {
        MPI_Barrier(MPI_COMM_WORLD);
        MPI_Bcast(&m_param_LLR.LLR_MATRIX[i][0], m_param_LLR.num_col, MPI_INT, 0, MPI_COMM_WORLD);
    }
    MPI_Bcast(&m_param_LLR.CSW_thr[0], m_param_LLR.num_row, MPI_INT, 0, MPI_COMM_WORLD);
#endif
    g_pECC = new ECC_Top();
    g_pECC->Init_ECC_Top(m_ecc_info, m_param_dec, &m_param_LLR, m_my_rank, m_num_process);
    g_pECC->Run_ECC_Top_Ref_C(m_ref_c);
    delete g_pECC;
    m_param_OPT.curr_FER = (double)(m_ref_c->frame_err_num) / (double)(m_ref_c->frame_sum);
    m_param_OPT.curr_Avit = (double)(m_ref_c->iter_sum) / (double)(m_ref_c->frame_sum);
}
void LOCAL_OPT::Read_LLR_info_Auto(PARAM_LLR* LLR_info, PARAM_OPT* OPT_info)
{
    char filename[255];
    FILE* matrix_in = NULL;
    int err = FALSE;
    int i;
    int c;
    sprintf(filename, "LLR_MATRIX_%d.txt", OPT_info->matrix_idx);
    matrix_in = fopen(filename, "r");
    fscanf(matrix_in, "%d", &c);     LLR_info->num_para_each_set = c;
    fscanf(matrix_in, "%d", &c);     LLR_info->num_dv = c;
    LLR_info->num_col = LLR_info->num_para_each_set * LLR_info->num_dv;
    LLR_info->dv_from = new int[LLR_info->num_dv];   LLR_info->dv_to = new int[LLR_info->num_dv];
    for (i = 0; i < LLR_info->num_dv; i++) {
        fscanf(matrix_in, "%d", &c);
        LLR_info->dv_from[i] = c;
    }
    for (i = 0; i < LLR_info->num_dv; i++) {
        fscanf(matrix_in, "%d", &c);
        LLR_info->dv_to[i] = c;
    }
    fscanf(matrix_in, "%d", &c);     LLR_info->num_group = c;
    LLR_info->num_set_each_group = new int[LLR_info->num_group];     LLR_info->type_each_group = new int[LLR_info->num_group];
    LLR_info->num_row = 0;
    for (i = 0; i < LLR_info->num_group; i++) {
        fscanf(matrix_in, "%d", &c);
        LLR_info->num_set_each_group[i] = c;
        LLR_info->num_row += LLR_info->num_set_each_group[i];
    }
    for (i = 0; i < LLR_info->num_group; i++) {
        fscanf(matrix_in, "%d", &c);
        LLR_info->type_each_group[i] = c;
    }
    fscanf(matrix_in, "%d", &c);     LLR_info->restart_num = c;
    LLR_info->restart_iter = new int[LLR_info->restart_num];
    for (i = 0; i < LLR_info->restart_num; i++) {
        fscanf(matrix_in, "%d", &c);
        LLR_info->restart_iter[i] = c;
    }
    LLR_info->max_value = new int[LLR_info->num_para_each_set];
    LLR_info->min_value = new int[LLR_info->num_para_each_set];
    for (i = 0; i < LLR_info->num_para_each_set; i++) {
        fscanf(matrix_in, "%d", &c);
        LLR_info->max_value[i] = c;
    }
    for (i = 0; i < LLR_info->num_para_each_set; i++) {
        fscanf(matrix_in, "%d", &c);
        LLR_info->min_value[i] = c;
    }
    LLR_info->LLR_MATRIX = new int* [LLR_info->num_row];     for (i = 0; i < LLR_info->num_row; i++) LLR_info->LLR_MATRIX[i] = new int[LLR_info->num_col];
    LLR_info->CSW_thr = new int[LLR_info->num_row];
    LLR_info->iter_start = new int[LLR_info->num_row];
    LLR_info->iter_end = new int[LLR_info->num_row];
    LLR_info->floor_flag = new int[LLR_info->num_row];
    for (i = 0; i < LLR_info->num_row; i++) {
        for (int j = 0; j < LLR_info->num_col; j++) {
            fscanf(matrix_in, "%d", &c);
            LLR_info->LLR_MATRIX[i][j] = c;
        }
        fscanf(matrix_in, "%d", &c); LLR_info->CSW_thr[i] = c;
        fscanf(matrix_in, "%d", &c); LLR_info->iter_start[i] = c;
        fscanf(matrix_in, "%d", &c); LLR_info->iter_end[i] = c;
        fscanf(matrix_in, "%d", &c); LLR_info->floor_flag[i] = c;
    }
    m_param_dec->MN_num = LLR_info->iter_end[LLR_info->num_row - 1];
    m_param_dec->MN = new int[m_param_dec->MN_num];
    for (i = 0; i < m_param_dec->MN_num; i++) {
        if (i == m_param_dec->MN_num - 1)
            m_param_dec->MN[i] = LLR_info->iter_end[LLR_info->num_row - 1];
        else
            m_param_dec->MN[i] = i;
    }
    if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_SSD == m_param_dec->init_n)) {
        for (i = 0; i < m_param_dec->MN_num; i++) {
            m_param_dec->MN[i] -= ITER_MAX_HBF;
        }
        if (m_param_dec->MN_num > 1) {
            m_param_dec->MN[0] = ITER_MAX_HBF;
        }
    }
    fclose(matrix_in);
    if (ID_ROOT == m_my_rank) {
        char fn_auto_result[LEN_FILENAME];
        sprintf(fn_auto_result, "Ref_C_result_%d.txt", m_ref_c->mode_init_seed);
        FILE* fp_auto_result;
        fp_auto_result = fopen(fn_auto_result, "a");
        fprintf(fp_auto_result, "* LLR_MATRIX_%d.txt\n", OPT_info->matrix_idx);
        if (NULL == matrix_in) {
            err = TRUE;
            fprintf(fp_auto_result, "Cannot open LLR_info file %s.\n", filename);
        }
        fprintf(fp_auto_result, "* num_para_each_set: %d\n", LLR_info->num_para_each_set);
        fprintf(fp_auto_result, "* num_dv: %d\n", LLR_info->num_dv);
        fprintf(fp_auto_result, "* num_group: %d\n", LLR_info->num_group);
        fprintf(fp_auto_result, "* num_set_each_group: ");
        for (i = 0; i < LLR_info->num_group; i++) {
            fprintf(fp_auto_result, "%d ", LLR_info->num_set_each_group[i]);
        }
        fprintf(fp_auto_result, "\n");
        fprintf(fp_auto_result, "* type_each_group: ");
        for (i = 0; i < LLR_info->num_group; i++) {
            fprintf(fp_auto_result, "%d ", LLR_info->type_each_group[i]);
        }
        fprintf(fp_auto_result, "\n");
        fprintf(fp_auto_result, "* restart_num: %d\n", LLR_info->restart_num);
        for (i = 0; i < LLR_info->restart_num; i++) {
            if (i == 0) {
                fprintf(fp_auto_result, "* ");
            }
            fprintf(fp_auto_result, "%d ", LLR_info->restart_iter[i]);
        }
        fprintf(fp_auto_result, "\n");
        fprintf(fp_auto_result, "* min~max_value: ");
        for (i = 0; i < LLR_info->num_para_each_set; i++) {
            fprintf(fp_auto_result, "[%d~%d] ", LLR_info->min_value[i], LLR_info->max_value[i]);
        }
        fprintf(fp_auto_result, "\n");
        fprintf(fp_auto_result, "* LLR_MATRIX\n");
        for (i = 0; i < LLR_info->num_row; i++) {
            fprintf(fp_auto_result, "* ");
            for (int j = 0; j < LLR_info->num_col; j++) {
                fprintf(fp_auto_result, "%2d ", LLR_info->LLR_MATRIX[i][j]);
            }
            fprintf(fp_auto_result, "%4d ", LLR_info->CSW_thr[i]);
            fprintf(fp_auto_result, "%3d ", LLR_info->iter_start[i]);
            fprintf(fp_auto_result, "%3d ", LLR_info->iter_end[i]);
            fprintf(fp_auto_result, "%2d ", LLR_info->floor_flag[i]);
            fprintf(fp_auto_result, "\n");
        }
        fprintf(fp_auto_result, "\n");
        fclose(fp_auto_result);
    }
}
