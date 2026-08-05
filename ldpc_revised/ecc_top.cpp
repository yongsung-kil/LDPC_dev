#include "ECC_Top.h"
using namespace std;
//================================================
// ??????
//================================================
ECC_Top::ECC_Top()
{
    m_ecc_info = NULL;
    m_param_dec = NULL;
    m_param_ref_c = NULL;
    m_param_tv_gen = NULL;
    m_msg = NULL;
    m_inv_msg = NULL;
    m_inv_cw = NULL;
    m_inv_cw_input = NULL;
    m_cw = NULL;
    m_cwt = NULL;
    m_cwr = NULL;
    m_err_position = NULL;
    m_err_position_noPS = NULL;
    m_HD_channel = NULL;
    m_SD_channel = NULL;
    m_CC_channel = NULL;
    m_CD_channel = NULL;
    m_HD_input = NULL;
    m_SD_input = NULL;
    m_CC_input = NULL;
    m_CD_input = NULL;
    m_dec_output = NULL;
    fp_uncor_seed = NULL;
#if defined(__ENC_TV_INTER_DEBUG__)
    m_Parity_inter = NULL;
#endif
}
//================================================
// ??????
//================================================
ECC_Top::~ECC_Top()
{
    /* buffer */
    delete[] m_HD_input;
    delete[] m_SD_input;
    delete[] m_CC_input;
    delete[] m_CD_input;
    delete[] m_dec_output;
    delete[] m_msg;
    delete[] m_inv_msg;
    delete[] m_inv_cw;
    delete[] m_inv_cw_input;
    delete[] m_cw;
    delete[] m_cwt;
    delete[] m_cwr;
    delete[] m_err_position;
    delete[] m_err_position_noPS;
    delete[] m_HD_channel;
    delete[] m_SD_channel;
    delete[] m_CC_channel;
    delete[] m_CD_channel;
#if defined(__ENC_TV_INTER_DEBUG__)
    for (int i = 0;i < m_PCM.M_b;i++) {
        delete[] m_Parity_inter[i];
    }
    delete[] m_Parity_inter;
#endif
    /* parity check matrix */
    Release_PCM(&m_PCM);
}
//================================================
// Parity check matrix ???? memory ????
//================================================
void ECC_Top::Release_PCM(PCM* pcm)
{
    delete[] pcm->RowW;
    delete[] pcm->ColW;
    for (int i = 0; i < pcm->M_b; i++) {
        delete[] pcm->PCM_b[i];
        delete[] pcm->PCM_b_enc[i];
        delete[] pcm->VtoC_ID[i];
    }
    delete[] pcm->PCM_b;
    delete[] pcm->PCM_b_enc;
    delete[] pcm->VtoC_ID;
#if defined(__RUN_PUNCT_RECOVERY__)
    delete[] pcm->punct_col_idx;
    delete[] pcm->punct_row_num;
    for (int i = 0; i < pcm->punct_col_num; i++) {
        //delete[] pcm->punct_row_idx[i];
        delete[] pcm->punct_vote[i];
        delete[] pcm->punct_vote_disjoint[i];
        for (int z = 0; z < pcm->z_sb; z++) {
            delete[] pcm->punct_vote_b[i][z];
        }
        delete[] pcm->punct_vote_b[i];
    }
    //delete[] pcm->punct_row_idx;
    delete[] pcm->punct_vote;
    delete[] pcm->punct_vote_disjoint;
    delete[] pcm->punct_vote_b;
    for (int i = 0; i < pcm->z_sb; i++) {
        for (int b1 = 0; b1 < 2; b1++) {
            delete[] pcm->punct_vote_joint[i][b1];
        }
        delete[] pcm->punct_vote_joint[i];
    }
    delete[] pcm->punct_vote_joint;
#endif
    for (int i = 0; i < pcm->N_b; i++) {
        delete[] pcm->V_net_b[i];
    }
    delete[] pcm->V_net_b;
    for (int i = 0; i < pcm->M; i++) {
        delete[] pcm->C_net[i];
    }
    delete[] pcm->C_net;
    Release_GT(pcm);
}
//================================================
// PCM pointer ????
//================================================
PCM* ECC_Top::Get_PCM()
{
    return &m_PCM;
}
//================================================
// Encoder pointer ????
//================================================
Encoder* ECC_Top::Get_Enc()
{
    return &m_enc;
}
//================================================
// PPE pointer ????
//================================================
Decoder* ECC_Top::Get_Dec()
{
    return &m_dec;
}
//================================================
// ECC Top?????? ?? ?????? buffer ??????
//================================================
void ECC_Top::Alloc_Buffer()
{
    int N = m_PCM.N;
    int M = m_PCM.M;
    int N_4KB = N;
    /* 4KB sector???? ???????? ???????? */
    m_msg = new int[N_4KB];
    m_inv_msg = new int[N_4KB];
    m_inv_cw = new int[N_4KB];
    m_cw = new int[N_4KB];
    m_cwt = new int[N_4KB];
    m_cwr = new double[N_4KB];
    m_err_position = new int[N_4KB];
    m_err_position_noPS = new int[N_4KB];
    m_HD_channel = new int[N_4KB];
    m_SD_channel = new int[N_4KB];
    m_CC_channel = new int[N_4KB];
    m_CD_channel = new int[N_4KB];
    /* Decoder???? ???????? ???? ???? ???????? ???????? ???????? */
    m_inv_cw_input = new int[N_4KB];
    m_HD_input = new int[N_4KB];
    m_SD_input = new int[N_4KB];
    m_CC_input = new int[N_4KB];
    m_CD_input = new int[N_4KB];
    m_dec_output = new int[N_4KB];
    for (int i = 0; i < N_4KB; i++) {
        m_msg[i] = 0;
        m_inv_msg[i] = 0;
        m_inv_cw[i] = 0;
        m_cw[i] = 0;
        m_cwt[i] = 0;
        m_cwr[i] = 0;
        m_err_position[i] = 0;
        m_err_position_noPS[i] = 0;
        m_HD_channel[i] = 0;
        m_SD_channel[i] = 0;
        m_CC_channel[i] = 0;
        m_CD_channel[i] = 0;
    }
    for (int i = 0; i < N_4KB; i++) {
        m_inv_cw_input[i] = 0;
        m_HD_input[i] = 0;
        m_SD_input[i] = 0;
        m_CC_input[i] = 0;
        m_CD_input[i] = 0;
        m_dec_output[i] = 0;
    }
#if defined(__ENC_TV_INTER_DEBUG__)
    m_Parity_inter = new int*[m_PCM.M_b];
    for (int i = 0;i < m_PCM.M_b;i++) m_Parity_inter[i] = new int[(m_PCM.N_b - m_PCM.M_b)*m_PCM.z_sb];
#endif
}
//================================================
// H matrix???? load?????? encoder????
// decoder???? ?????? ???????? ????????.
//================================================
void ECC_Top::Init_ECC_Top(ECC_INFO* info, PARAM_DEC* param_dec, int my_rank, int num_pro)
{
    m_ecc_info = info;
    m_param_dec = param_dec;
    m_my_rank = my_rank;
    m_num_process = num_pro;
    /* Load H matrix */
    Load_PCM(&m_PCM, m_ecc_info);
    /* Init Encoder */
    m_enc.Init_Enc(&m_PCM);
    /* Init Decoder */
    m_dec.Init_Dec(m_ecc_info, &m_PCM, m_param_dec,m_param_LLR,m_my_rank);
    m_dec.Init_Dec_Option();
}
//================================================
// H matrix???? load?????? encoder????
// decoder???? ?????? ???????? ????????.
// LLR_MATRIX???? ???????? ????????
//================================================
void ECC_Top::Init_ECC_Top(ECC_INFO* info, PARAM_DEC* param_dec, PARAM_LLR* param_LLR, int my_rank, int num_pro)
{
    m_ecc_info = info;
    m_param_dec = param_dec;
    m_my_rank = my_rank;
    m_num_process = num_pro;
    m_param_LLR = param_LLR;
    /* Load H matrix */
    Load_PCM(&m_PCM, m_ecc_info);
    /* Init Encoder */
    m_enc.Init_Enc(&m_PCM);
    /* Init Decoder */
    m_dec.Init_Dec(m_ecc_info, &m_PCM, m_param_dec, m_param_LLR, m_my_rank);
    m_dec.Init_Dec_Option();
}
//================================================
// H matrix???? load?????? encoder????
// decoder???? ?????? ???????? ????????.
// [????????] VSS_ECC_TOP program?????? ????????
//================================================
void ECC_Top::Init_ECC_Top(ECC_INFO* info, PARAM_DEC* param_dec)
{
    m_ecc_info = info;
    m_param_dec = param_dec;
    m_my_rank = 0;
    m_num_process = 1;
    /* Load H matrix */
    Load_PCM(&m_PCM, m_ecc_info);
    /* Init ECC */
    m_enc.Init_Enc(&m_PCM);
    m_dec.Init_Dec(m_ecc_info, &m_PCM, m_param_dec,m_my_rank);
}
//================================================
// Read parity check matrix from file
//================================================
void ECC_Top::Load_PCM(PCM *pcm, ECC_INFO* ecc_info)
{
    FILE * matrix_in = NULL;
    FILE * mux_matrix_in = NULL;
    int *    z_mem_shift = NULL;
    int err = FALSE;
    int i, j, p;
    int c, k, s;
    matrix_in = fopen(ecc_info->str_matrix_name, "r");
    if (NULL == matrix_in) {
        err = TRUE;
        printf("Cannot open H-matrix file.\n");
    }
    fscanf(matrix_in, "%d", &c);    pcm->N_b = c;
    fscanf(matrix_in, "%d", &c);    pcm->M_b = c;
    fscanf(matrix_in, "%d", &c);    pcm->J = c;
    fscanf(matrix_in, "%d", &c);    pcm->K = c;
    fscanf(matrix_in, "%d", &c);    pcm->z_sb = c;
    pcm->N = pcm->N_b * pcm->z_sb;
    pcm->M = pcm->M_b * pcm->z_sb;
    /* Memory allocation */
    pcm->PCM_b        = new int*[pcm->M_b];    for (i = 0; i < pcm->M_b; i++) pcm->PCM_b[i] = new int[pcm->N_b];
    pcm->PCM_b_enc    = new int*[pcm->M_b];    for (i = 0; i < pcm->M_b; i++) pcm->PCM_b_enc[i] = new int[pcm->N_b];
    pcm->RowW          = new int[pcm->M_b];
    pcm->ColW          = new int[pcm->N_b];
    pcm->V_net_b      = new int*[pcm->N_b];    for (j = 0; j < pcm->N_b; j++) pcm->V_net_b[j] = new int[pcm->J];
    pcm->VtoC_ID      = new int*[pcm->M_b];    for (i = 0; i < pcm->M_b; i++) pcm->VtoC_ID[i] = new int[pcm->N_b];
    pcm->C_net        = new int*[pcm->M];      for (i = 0; i < pcm->M; i++) pcm->C_net[i] = new int[pcm->K];
    z_mem_shift = new int[pcm->z_sb];
    /* edge connection */
    for (i = 0; i < pcm->M_b; i++) {
        k = 0;
        for (j = 0; j < pcm->N_b; j++) {
            fscanf(matrix_in, "%d", &c);
            pcm->PCM_b[i][j] = c;
            if (EMPTY != c) {
                k++;
                pcm->VtoC_ID[i][j] = k - 1;
            }
            else { pcm->VtoC_ID[i][j] = 0; }
        }
        pcm->RowW[i] = k;
    }
    for (j = 0; j < pcm->N_b; j++) {
        k = 0;
        for (i = 0; i < pcm->M_b; i++) {
            if (pcm->PCM_b[i][j] != -1) {
                k++;
                pcm->V_net_b[j][k - 1] = i;
            }
        }
        pcm->ColW[j] = k;
    }
    /* edge connection */
    for (i = 0; i < pcm->M_b; i++) {
        k = 0;
        for (j = 0; j < pcm->N_b; j++) {
            s = pcm->PCM_b[i][j];
            if (s >= 0) {
                k = k + 1;
                shift_mem(z_mem_shift, pcm->z_sb, s, 1);
                for (p = 0; p < pcm->z_sb; p++) {
                    pcm->C_net[i * pcm->z_sb + p][(k-1) * pcm->z_sb + z_mem_shift[p]] = j * pcm->z_sb + p;
                }
            }
        }
    }
    delete[] z_mem_shift;
    z_mem_shift = NULL;
#ifndef __VSS_ECC_TOP__
#if defined(__WIN_OS__)
#ifndef __AUTO_LLR_OPT__
    if (ID_ROOT == m_my_rank)
        printf("* PCM parameters : %d %d %d %d %d\n", pcm->N_b, pcm->M_b, pcm->J, pcm->K, pcm->z_sb);
#endif
#endif
#endif
#if defined(__RUN_PUNCT_RECOVERY__)
    pcm->punct_col_num = PUNCTURED_COL_NUM;
    pcm->punct_col_idx = new int[pcm->punct_col_num];
    for (int k = 0; k < pcm->punct_col_num; k++) {
        pcm->punct_col_idx[k] = pcm->N_b - pcm->M_b - pcm->punct_col_num + k;
    }
    pcm->punct_row_num = new int[pcm->punct_col_num];
    pcm->punct_vote = new int* [pcm->punct_col_num];
    pcm->punct_vote_disjoint = new int* [pcm->punct_col_num];
    pcm->punct_vote_b = new int** [pcm->punct_col_num];
    for (int k = 0; k < pcm->punct_col_num; k++) {
        pcm->punct_row_num[k] = 0;
        pcm->punct_vote[k] = new int[pcm->z_sb];
        pcm->punct_vote_disjoint[k] = new int[pcm->z_sb];
        pcm->punct_vote_b[k] = new int* [pcm->z_sb];
        for (int z = 0; z < pcm->z_sb; z++) {
            pcm->punct_vote_b[k][z] = new int[2];
            pcm->punct_vote_b[k][z][0] = 0;
            pcm->punct_vote_b[k][z][1] = 0;
        }
    }
    pcm->punct_vote_joint = new int** [pcm->z_sb];
    for (int z = 0; z < pcm->z_sb; z++) {
        pcm->punct_vote_joint[z] = new int* [2];
        for (int b1 = 0; b1 < 2; b1++) {
            pcm->punct_vote_joint[z][b1] = new int[2];
            for (int b2 = 0; b2 < 2; b2++) {
                pcm->punct_vote_joint[z][b1][b2] = 0;
            }
        }
    }
    for (int i = 0; i < pcm->M_b; i++) {
#if defined(__RUN_PREPROCESSING__)
        if (EMPTY != pcm->PCM_b[i][pcm->N_b - pcm->M_b - 3] && EMPTY == pcm->PCM_b[i][pcm->N_b - pcm->M_b - 2]) {
            pcm->punct_row_num[0]++;
        }
        else if (EMPTY != pcm->PCM_b[i][pcm->N_b - pcm->M_b - 3] && EMPTY != pcm->PCM_b[i][pcm->N_b - pcm->M_b - 2]) {
            pcm->punct_row_num[1]++;
        }
#else
        if (pcm->punct_col_num == 1) {
            if (EMPTY != pcm->PCM_b[i][0]) {
                pcm->punct_row_num[0]++;
            }
        }
        else if (pcm->punct_col_num == 2) {
#if defined(__HACRC_IKD_5B__)
            if (EMPTY != pcm->PCM_b[i][1] && EMPTY == pcm->PCM_b[i][2]) {
                pcm->punct_row_num[0]++;
            }
            else if (EMPTY == pcm->PCM_b[i][1] && EMPTY != pcm->PCM_b[i][2]) {
                pcm->punct_row_num[1]++;
            }
#else
            if (EMPTY != pcm->PCM_b[i][127] && EMPTY == pcm->PCM_b[i][128]) {
                pcm->punct_row_num[0]++;
            }
            /*else if (EMPTY != pcm->PCM_b[i][0] && EMPTY != pcm->PCM_b[i][1]) {
                pcm->punct_row_num[1]++;
            }*/
            else if (EMPTY == pcm->PCM_b[i][127] && EMPTY != pcm->PCM_b[i][128]) {
                pcm->punct_row_num[1]++;
            }
#endif
        }
        else if (pcm->punct_col_num == 3) {
            if (EMPTY != pcm->PCM_b[i][0] && EMPTY == pcm->PCM_b[i][1] && EMPTY == pcm->PCM_b[i][2]) {
                pcm->punct_row_num[0]++;
            }
            else if (EMPTY != pcm->PCM_b[i][0] && EMPTY != pcm->PCM_b[i][1] && EMPTY == pcm->PCM_b[i][2]) {
                pcm->punct_row_num[1]++;
            }
            else if (EMPTY != pcm->PCM_b[i][0] && EMPTY != pcm->PCM_b[i][1] && EMPTY != pcm->PCM_b[i][2]) {
                pcm->punct_row_num[2]++;
            }
        }
#endif
    }
    //pcm->punct_row_idx = new int* [pcm->punct_col_num];
    //for (int k = 0; k < pcm->punct_col_num; k++) {
    //  pcm->punct_row_idx[k] = new int[pcm->punct_row_num[k]];
    //}
    int cnt0 = 0;
    int cnt1 = 0;
    int cnt2 = 0;
    for (int i = 0; i < pcm->M_b; i++) {
#if defined(__RUN_PREPROCESSING__)
        if (EMPTY != pcm->PCM_b[i][pcm->N_b - pcm->M_b - 3] && EMPTY == pcm->PCM_b[i][pcm->N_b - pcm->M_b - 2]) {
            pcm->punct_row_idx[0][cnt0] = i;
            cnt0++;
        }
        else if (EMPTY != pcm->PCM_b[i][pcm->N_b - pcm->M_b - 3] && EMPTY != pcm->PCM_b[i][pcm->N_b - pcm->M_b - 2]) {
            pcm->punct_row_idx[1][cnt1] = i;
            cnt1++;
        }
#else
        /*
        if (pcm->punct_col_num == 1) {
            if (EMPTY != pcm->PCM_b[i][0]) {
                pcm->punct_row_idx[0][cnt0] = i;
                cnt0++;
            }
        }
        else if (pcm->punct_col_num == 2) {
#if defined(__HACRC_IKD_5B__)
            if (EMPTY != pcm->PCM_b[i][1] && EMPTY == pcm->PCM_b[i][2]) {
                pcm->punct_row_idx[0][cnt0] = i;
                cnt0++;
            }
            else if (EMPTY == pcm->PCM_b[i][1] && EMPTY != pcm->PCM_b[i][2]) {
                pcm->punct_row_idx[1][cnt1] = i;
                cnt1++;
            }
#else
            if (EMPTY != pcm->PCM_b[i][127] && EMPTY == pcm->PCM_b[i][128]) {
                pcm->punct_row_idx[0][cnt0] = i;
                cnt0++;
            }
            else if (EMPTY == pcm->PCM_b[i][127] && EMPTY != pcm->PCM_b[i][128]) {
                pcm->punct_row_idx[1][cnt1] = i;
                cnt1++;
            }
#endif
        }
        else if (pcm->punct_col_num == 3) {
            if (EMPTY != pcm->PCM_b[i][0] && EMPTY == pcm->PCM_b[i][1] && EMPTY == pcm->PCM_b[i][2]) {
                pcm->punct_row_idx[0][cnt0] = i;
                cnt0++;
            }
            else if (EMPTY != pcm->PCM_b[i][0] && EMPTY != pcm->PCM_b[i][1] && EMPTY == pcm->PCM_b[i][2]) {
                pcm->punct_row_idx[1][cnt1] = i;
                cnt1++;
            }
            else if (EMPTY != pcm->PCM_b[i][0] && EMPTY != pcm->PCM_b[i][1] && EMPTY != pcm->PCM_b[i][2]) {
                pcm->punct_row_idx[2][cnt2] = i;
                cnt2++;
            }
        }
        */
#endif
    }
    //printf("cnt0=%d, cnt1=%d\n",cnt0,cnt1);
#endif
    Make_GT_HW(matrix_in, pcm);
    fclose(matrix_in);
    matrix_in = NULL;
}
//================================================
// Ref-C mode???? ????????????.
//================================================
void ECC_Top::Run_ECC_Top_Ref_C(PARAM_REF_C * p_ref_c)
{
    /* ?????? ???????? */
    int          err;
    time_t       tt;
    /* ???????? ?????? ???????? */
    int          seed;
    m_gaussian_var = 1;
    m_gaussian_dev = 1;
    m_param_ref_c = p_ref_c;
    /* Set AWGN for given RBER */
    if (MODE_CH_RBER == m_param_ref_c->ch_type) {
        m_gaussian_dev = dev_from_RBER(m_param_ref_c->RBER);
        m_gaussian_var = m_gaussian_dev * m_gaussian_dev;
        Set_R_Offset(m_param_dec->init_n);
        Set_LLR_Th(m_gaussian_var);
    }
    /* Set random generator */
#ifdef __AUTO_LLR_OPT__
    time(&tt);
    if (m_param_ref_c->mode_init_seed == MODE_SEED_INIT_FIXED2)
        seed = 1464149941;
    else
        seed = (unsigned)tt + m_param_ref_c->mode_init_seed * 60 * 60 * 24 * 365;
#else
    if ((MODE_SEED_INIT_FIXED == m_param_ref_c->mode_init_seed)|| (MODE_SEED_INIT_FIXED2 == m_param_ref_c->mode_init_seed)) {
        seed = 1464149941;
    }
    else if (MODE_SEED_INIT_TIME == m_param_ref_c->mode_init_seed) {
        time(&tt);
        seed = (unsigned)tt;
    }
    else {
        seed = m_param_ref_c->mode_init_seed;
    }
    seed += m_my_rank * 60 * 60 * 24 * 365;
#endif
#ifdef __RUN_MPI__
    MPI_Bcast(&seed, 1, MPI_INT, ID_ROOT, MPI_COMM_WORLD);
    seed += m_my_rank;
#endif
    //printf("%d\t%d\n", m_my_rank, seed);
    Set_Random_Seed_xor25(seed);
    /* memory allocation */
    Alloc_Buffer();
    /* Random seed */
    if ((MODE_SEED_SAVE_UNCOR_SEED == m_param_ref_c->mode_seed) ||
        (MODE_SEED_SAVE_COR_SEED == m_param_ref_c->mode_seed) ||
        (MODE_SEED_SAVE_CORNER_SEED == m_param_ref_c->mode_seed) ||
        (MODE_SEED_LOAD_UNCOR_SEED == m_param_ref_c->mode_seed) ||
        (MODE_SEED_LOAD_UNCOR_VECTOR == m_param_ref_c->mode_seed) ||
        (MODE_SEED_SAVE_ALL_SEED == m_param_ref_c->mode_seed) ||
        (MODE_SEED_SAVE_UNCOR_SEED_LOAD_INIT_SEED == m_param_ref_c->mode_seed) ||
        (MODE_SEED_LOAD_UNCOR_SEED_SAVE_UNCOR_SEED == m_param_ref_c->mode_seed)) {
#ifdef __AUTO_LLR_OPT__
        if (MODE_SEED_LOAD_UNCOR_VECTOR == m_param_ref_c->mode_seed) {
            if (MODE_CH_RBER == m_param_ref_c->ch_type) {
                sprintf(filename_uncor_seed, "uncor_vector_H_%d_CH_%d_E%.2e_init_n_%d_%d.dat", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->RBER, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
            }
            else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) {
                sprintf(filename_uncor_seed, "uncor_vector_H_%d_CH_%d_E%d_init_n_%d_%d.dat", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
            }
            else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
                sprintf(filename_uncor_seed, "uncor_vector_H_%d_CH_%d_E%d_SC_%.2f_SE_%.2f_init_n_%d_%d.dat", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_SCR, m_param_ref_c->fixed_SER, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
            }
            else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
                sprintf(filename_uncor_seed, "uncor_vector_H_%d_CH_%d_E%d_E_%.3f_init_n_%d_%d.dat", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_erasure_ratio, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
            }
        }
        else {
            if (MODE_CH_RBER == m_param_ref_c->ch_type) {
                sprintf(filename_uncor_seed, "uncor_seed_H_%d_CH_%d_E%.2e_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->RBER, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
            }
            else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) {
                sprintf(filename_uncor_seed, "uncor_seed_H_%d_CH_%d_E%d_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
            }
            else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
                sprintf(filename_uncor_seed, "uncor_seed_H_%d_CH_%d_E%d_SC_%.2f_SE_%.2f_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_SCR, m_param_ref_c->fixed_SER, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
            }
            else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
                sprintf(filename_uncor_seed, "uncor_seed_H_%d_CH_%d_E_%.3f_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_erasure_ratio, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
            }
            if (MODE_SEED_LOAD_UNCOR_SEED_SAVE_UNCOR_SEED == m_param_ref_c->mode_seed) {
                if (MODE_CH_RBER == m_param_ref_c->ch_type) {
                    sprintf(filename_uncor_seed_2nd_decode, "redecode_uncor_seed_H_%d_CH_%d_E%.2e_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->RBER, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
                }
                else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) {
                    sprintf(filename_uncor_seed_2nd_decode, "redecode_uncor_seed_H_%d_CH_%d_E%d_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
                }
                else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
                    sprintf(filename_uncor_seed_2nd_decode, "redecode_uncor_seed_H_%d_CH_%d_E%d_SC_%.2f_SE_%.2f_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_SCR, m_param_ref_c->fixed_SER, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
                }
                else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
                    sprintf(filename_uncor_seed_2nd_decode, "redecode_uncor_seed_H_%d_CH_%d_E_%.3f_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_erasure_ratio, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
                }
            }
        }
#else
        if (MODE_SEED_LOAD_UNCOR_VECTOR == m_param_ref_c->mode_seed) {
            sprintf(filename_uncor_seed, "uncor_seed_S_%d_H_%d_init_n_%d_%d.dat", m_param_ref_c->mode_scenario, m_ecc_info->matrix_sel, m_param_dec->init_n, m_my_rank);    // MPI 210818
        }
        else {
            if (MODE_CH_RBER == m_param_ref_c->ch_type) {
                sprintf(filename_uncor_seed, "uncor_seed_H_%d_CH_%d_E%.2e_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->RBER, m_param_dec->init_n, m_my_rank);
            }
            else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) {
                sprintf(filename_uncor_seed, "uncor_seed_H_%d_CH_%d_E%d_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_dec->init_n, m_my_rank);
            }
            else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
                sprintf(filename_uncor_seed, "uncor_seed_H_%d_CH_%d_E%d_SC_%.2f_SE_%.2f_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_SCR, m_param_ref_c->fixed_SER, m_param_dec->init_n, m_my_rank);
            }
            else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
                sprintf(filename_uncor_seed, "uncor_seed_H_%d_CH_%d_E_%.3f_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_erasure_ratio, m_param_dec->init_n, m_my_rank);
            }
        }
#endif
    }
#ifdef __AUTO_LLR_OPT__
        if ((MODE_SEED_DEFAULT_LOAD_INIT_SEED == m_param_ref_c->mode_seed) ||
            (MODE_SEED_SAVE_UNCOR_SEED_LOAD_INIT_SEED == m_param_ref_c->mode_seed)) {
            /* Init seed fn */
            if (MODE_CH_RBER == m_param_ref_c->ch_type) {
                sprintf(filename_init_seed, "init_seed_H_%d_CH_%d_E%.2e_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->RBER, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
            }
            else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) {
                sprintf(filename_init_seed, "init_seed_H_%d_CH_%d_E%d_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
            }
            else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
                sprintf(filename_init_seed, "init_seed_H_%d_CH_%d_E%d_SC_%.2f_SE_%.2f_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_SCR, m_param_ref_c->fixed_SER, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
            }
            else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
                sprintf(filename_init_seed, "init_seed_H_%d_CH_%d_E_%.3f_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_ref_c->ch_type, m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_erasure_ratio, m_param_dec->init_n, m_param_ref_c->mode_init_seed);
            }
        }
#endif
        if ((MODE_SEED_LOAD_UNCOR_SEED == m_param_ref_c->mode_seed) ||
            (MODE_SEED_LOAD_UNCOR_VECTOR == m_param_ref_c->mode_seed)) {
            fp_uncor_seed = fopen(filename_uncor_seed, "rt");
            if (NULL == fp_uncor_seed) {
                err = TRUE;
                printf("Cannot open seed file.\n");
            }
            else {
                Load_ECC_Input(fp_uncor_seed, filename_uncor_seed);
            }
        }
#ifdef __AUTO_LLR_OPT__
        else if (MODE_SEED_LOAD_UNCOR_SEED_SAVE_UNCOR_SEED == m_param_ref_c->mode_seed) {
            fp_uncor_seed = fopen(filename_uncor_seed, "rt");
            if (NULL == fp_uncor_seed) {
                err = TRUE;
                printf("Cannot open seed file.(%s)\n", filename_uncor_seed);
            }
            else {
                Load_ECC_Input(fp_uncor_seed, filename_uncor_seed);
            }
        }
#endif
        /* Initialize */
        rn = 1;
        fr_4KB = new int[m_param_dec->MN_num];
        for (int n = 0; n < m_param_dec->MN_num; n++) {
            fr_4KB[n] = 0;
        }
        fr_over_fly = 0;
        iter_sum = 0;
        clk_sum = 0;
        clk_sum_throughput = 0;
#if defined (__RUN_MPI__)
        tot_rn = 0;
        tot_fr = new double[m_param_dec->MN_num];
        for (n = 0; n < m_param_dec->MN_num; n++)    tot_fr[n] = 0;
        tot_iter_sum = 0;
#else
#ifdef __AUTO_LLR_OPT__
        Print_Result_Part1_Auto();
#else
        if ((MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_ref_c->mode_scenario)) {
            Print_Result_Part1(FALSE);
        }
        else {
            Print_Result_Part1(TRUE);
        }
#endif
#endif
        m_time_start = time(NULL);
        m_param_ref_c->FER_local = new double[m_param_dec->MN_num];
        m_param_ref_c->FER_MPI = new double[m_param_dec->MN_num];
        if ((MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_ref_c->mode_scenario)) {
            Run_Ref_C_Scenario_4KB();
        }
        m_time_end = time(NULL);
        rn = rn - 1;
        /* print final result */
#if defined (__RUN_MPI__)
        if ((MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_ref_c->mode_scenario)) {
            Gather_Result_MPI(TRUE, rn, iter_sum, clk_sum, fr_4KB, fr_over_fly, m_param_dec->MN_num);
            p_ref_c->frame_sum = tot_rn;
            p_ref_c->frame_err_num = tot_fr[m_param_dec->MN_num - 1];
            p_ref_c->iter_sum = tot_iter_sum;
        }
#else
#ifdef __AUTO_LLR_OPT__
#if defined (__WIN_OS__)
        Print_Result_Part2_Memory_Opt(FALSE, rn, fr_4KB, iter_sum, clk_sum, clk_sum_throughput, TRUE, m_param_ref_c->FER_local);
#endif
        Print_Result_Part2_Memory_Opt(TRUE, rn, fr_4KB, iter_sum, clk_sum, clk_sum_throughput, TRUE, m_param_ref_c->FER_local);
#else
        Print_Result_Part2_Memory_Opt(FALSE, rn, fr_4KB, iter_sum, clk_sum, clk_sum_throughput, TRUE, m_param_ref_c->FER_local);
        Print_Result_Part2_Memory_Opt(TRUE, rn, fr_4KB, iter_sum, clk_sum, clk_sum_throughput, TRUE, m_param_ref_c->FER_local);
#endif
        p_ref_c->frame_sum = rn;
        p_ref_c->frame_err_num = fr_4KB[m_param_dec->MN_num - 1];
        p_ref_c->iter_sum = iter_sum;
#endif
        /* release  */
        delete[] fr_4KB;
        fr_4KB = NULL;
        if ((MODE_SEED_LOAD_UNCOR_SEED == m_param_ref_c->mode_seed) || (MODE_SEED_LOAD_UNCOR_VECTOR == m_param_ref_c->mode_seed)) {
            fclose(fp_uncor_seed);
        }
#ifdef __AUTO_LLR_OPT__
        else if (MODE_SEED_LOAD_UNCOR_SEED_SAVE_UNCOR_SEED == m_param_ref_c->mode_seed) {
            fclose(fp_uncor_seed);
        }
#endif
    }
//================================================
// Test Vector mode
//================================================
void ECC_Top::Run_ECC_Top_TV_Gen(PARAM_TV_GEN * p_tv_gen)
{
    time_t  tt;
    int seed;
    m_param_tv_gen = p_tv_gen;
    /* Set random generator */
    time(&tt);
    seed = (unsigned)tt;
    if (MODE_SEED_INIT_FIXED == m_param_tv_gen->mode_init_seed) {
        seed = 1464149941;
    }
    seed = seed + m_my_rank;
    Set_Random_Seed_xor25(seed);    // xor25
    srand(1);    // c library
    /* memory allocation */
    Alloc_Buffer();
    /* TV setting */
    Make_TV_Folder();
    m_tv_enc.Set_Param(m_ecc_info, &m_PCM);
    m_tv_dec.Set_Param(m_ecc_info, &m_PCM, m_param_dec);
    if ((MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_tv_gen->mode_scenario)) {
        if ((MODE_TV_CASE_HD_XOR25_SEED_FIXED == m_param_tv_gen->TS_idx) ||
            (MODE_TV_CASE_HD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
            (MODE_TV_CASE_2SD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
            (MODE_TV_CASE_2SD_XOR25_SEED_STRONG_ERROR == m_param_tv_gen->TS_idx) ||
            (MODE_TV_CASE_3SD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
            (MODE_TV_CASE_1_5SD_XOR25_SEED_ERASURE == m_param_tv_gen->TS_idx)) {
            Run_TV_Gen_Scenario_4KB_XOR25_Seed_File();
        }
        else if ((MODE_TV_CASE_HD_FIXED_DIN == m_param_tv_gen->TS_idx) ||
            (MODE_TV_CASE_2SD_FIXED_DIN == m_param_tv_gen->TS_idx) ||
            (MODE_TV_CASE_3SD_FIXED_DIN == m_param_tv_gen->TS_idx) ||
            (MODE_TV_CASE_1_5SD_FIXED_DIN == m_param_tv_gen->TS_idx)) {
            Run_TV_Gen_Scenario_4KB_DIN_File();
        }
        else {
            Run_TV_Gen_Scenario_4KB();
        }
    }
}
//================================================
// Sector scenario
// i)  4KB
//================================================
void ECC_Top::Run_Ref_C_Scenario_4KB()
{
    int N = 0;
    int M = 0;
    int N_b = 0;
    int M_b = 0;
    int crc_shortened_bits = CRC_LOGIC_SHORTENED;
    int len_noPS = 0;
    if (MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_ref_c->mode_scenario) {
        N = m_PCM.N;
        M = m_PCM.M;
        N_b = m_PCM.N_b;
        M_b = m_PCM.M_b;
        len_noPS = N - (m_ecc_info->shortened_bit_info + m_ecc_info->punctured_bit_info + m_ecc_info->punctured_bit_parity);
    }
    Set_Bit_Pos();
    Alloc_Log_Data();
    Open_Log_Files();
    Set_Corner_Checker();
    while ((fr_4KB[m_param_dec->MN_num - 1] != m_param_ref_c->fn) && (rn != m_param_ref_c->max_num_test + 1)) {
        /* Set random seed  */
        if ((MODE_SEED_SAVE_UNCOR_SEED == m_param_ref_c->mode_seed) ||
            (MODE_SEED_SAVE_COR_SEED == m_param_ref_c->mode_seed) ||
            (MODE_SEED_SAVE_CORNER_SEED == m_param_ref_c->mode_seed) ||
            (MODE_SEED_SAVE_ALL_SEED == m_param_ref_c->mode_seed)){
            Get_Random_Seed(current_seed);
        }
        else if (MODE_SEED_LOAD_UNCOR_SEED == m_param_ref_c->mode_seed) {
            Read_Seed(fp_uncor_seed, current_seed);
            Set_Random_Seed(current_seed);
        }
#ifdef __AUTO_LLR_OPT__
        else if (MODE_SEED_SAVE_UNCOR_SEED_LOAD_INIT_SEED == m_param_ref_c->mode_seed ||
            MODE_SEED_DEFAULT_LOAD_INIT_SEED == m_param_ref_c->mode_seed) {
            if (rn == 1) {
                fp_init_seed = fopen(filename_init_seed, "rt");
                if (NULL != fp_init_seed) {
                    Read_Seed(fp_init_seed, current_seed);
                    Set_Random_Seed(current_seed);
                    fclose(fp_init_seed);
                }
                else {
                    Get_Random_Seed(current_seed);
                }
            }
            else {
                Get_Random_Seed(current_seed);
            }
        }
        else if (MODE_SEED_LOAD_UNCOR_SEED_SAVE_UNCOR_SEED == m_param_ref_c->mode_seed) {
            Read_Seed(fp_uncor_seed, current_seed);
            Set_Random_Seed(current_seed);
        }
#endif
        /* Generate message */
        if (MODE_INPUT_PATTERN_RANDOM == m_param_ref_c->mode_data_input) {
            rand_msg_xor25(m_msg, N - M);
        }
        else if (MODE_INPUT_PATTERN_ALL_ZERO == m_param_ref_c->mode_data_input) {
            for (int n = 0; n < N - M; n++) { m_msg[n] = 0; }
        }
        else if (MODE_INPUT_PATTERN_ALL_ONE == m_param_ref_c->mode_data_input) {
            for (int n = 0; n < N - M; n++) { m_msg[n] = 1; }
        }
        /* Invert or copy message */
        if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
            for (int n = 0; n < N - M; n++) { m_inv_msg[n] = m_msg[n] ^ 1; }
        }
        else if (MODE_ALL_ZERO_CODEWORD == m_ecc_info->mode_all_one_cw) {
            memcpy(m_inv_msg, m_msg, (N - M) * sizeof(int));
        }
        /* Information Shortening */
        for (int n = m_ecc_info->bit_pos.info_sh_start; n < m_ecc_info->bit_pos.info_sh_end; n++) {
            m_inv_msg[n] = 0;
        }
        /* CRC encoding */
        CRC_encoder(m_inv_msg, N_b - M_b, crc_shortened_bits);
        /* LDPC encoding */
        m_enc.LDPC_encoder_4KB(m_inv_cw, m_inv_msg);
        /* Re-invert or copy codeword */
        if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
            for (int n = 0; n < N; n++) { m_cw[n] = m_inv_cw[n] ^ 1; }
        }
        else if (MODE_ALL_ZERO_CODEWORD == m_ecc_info->mode_all_one_cw) {
            memcpy(m_cw, m_inv_cw, N * sizeof(int));
        }
        /* Make LDPC decoder input*/
        if (MODE_SEED_LOAD_UNCOR_VECTOR == m_param_ref_c->mode_seed) {
            Load_Dec_Input_Vector_Format(N, len_noPS);
        }
        else {
            if (MODE_CH_RBER == m_param_ref_c->ch_type) {
                Make_Dec_Input_AWGN(N, m_cw, m_cwt, m_cwr, m_gaussian_dev, m_gaussian_var, m_HD_channel, m_SD_channel, m_CC_channel, m_CD_channel);
            }
            else {
                Make_Dec_Input_Ref_C_Fixed_4KB(m_cw, m_HD_channel, m_SD_channel, m_CC_channel, m_CD_channel);
            }
        }
        /* Copy buffer */
        memcpy(m_HD_input, m_HD_channel, N * sizeof(int));
        memcpy(m_SD_input, m_SD_channel, N * sizeof(int));
        memcpy(m_CC_input, m_CC_channel, N * sizeof(int));
        memcpy(m_CD_input, m_CD_channel, N * sizeof(int));
        memcpy(m_inv_cw_input, m_inv_cw, N * sizeof(int));
        Clear_Corner_Checker();
        /* LDPC decoding */
        m_dec.LDPC_Decoder(m_HD_input, m_SD_input, m_CC_input, m_CD_input, m_param_dec->init_n, m_inv_cw_input,
            rn - 1, EMPTY,
            &o_iter_num, &o_CRC_flag, &o_n_error, &o_str_n_error, &o_1_counter, &o_0_1_flip_counter, m_dec_output, &o_BF_on, &o_overall_clk, &o_weak_n_cor,
            &m_corner_checker);
#if defined (__CORNER_CHECKER__)
        flag_update_corner_check = FLAG_LOW;
        flag_update_corner_check = Update_Corner_Checker_Total();
#endif
#if defined (__SHOW_RBER_DIST__)
        static FILE * fp_rber_dist = NULL;    // 매 프레임 open/close 대신 핸들 유지 (파일 내용 동일)
        if (fp_rber_dist == NULL) fp_rber_dist = fopen("rber_dist.dat", "a");
        fprintf(fp_rber_dist, "%d\n", o_CRC_flag);
        fflush(fp_rber_dist);
#endif
        /* Result */
        if (FLAG_HIGH == o_CRC_flag) {
            fr_4KB[m_param_dec->MN_num - 1]++;
        }
        for (int n = 0; n < m_param_dec->MN_num - 1; n++) {
            if (o_iter_num > m_param_dec->MN[n]) {
                fr_4KB[n]++;
            }
        }
        if (MODE_DEC_HD == m_param_dec->init_n) {
            if (o_overall_clk > MAX_THROUGHPUT_CLOCK) {
                fr_over_fly++;
            }
        }
        iter_effective = (double)o_iter_num;
        if (FLAG_LOW == o_CRC_flag) {
            if (MODE_DEC_HD == m_param_dec->init_n) {
                iter_temp = 0;
                /* partial CRC */
                if (MODE_CRC_PARTIAL == m_param_dec->CRC_Option_F_P || MODE_PCRC_GENIE == m_param_dec->CRC_Option_F_P) {
                    if (o_str_n_error == 0) iter_temp = 0.75;
                    else if (o_str_n_error == 1)    iter_temp = 0.5;
                    else if (o_str_n_error == 2)    iter_temp = 0.25;
                }
                iter_effective -= iter_temp;
            }
        }
        iter_sum += iter_effective;
        clk_temp = (double)o_overall_clk;
        clk_sum += clk_temp;
        if (MAX_THROUGHPUT_CLOCK > clk_temp) {
            clk_sum_throughput += MAX_THROUGHPUT_CLOCK;
        }
        else {
            clk_sum_throughput += clk_temp;
        }
        if (MODE_SEED_SAVE_UNCOR_SEED == m_param_ref_c->mode_seed) {
            if (FLAG_HIGH == o_CRC_flag) {
                Print_Seed(fp_uncor_seed, 0, filename_uncor_seed, current_seed);
            }
        }
        else if (MODE_SEED_SAVE_COR_SEED == m_param_ref_c->mode_seed) {
            if (FLAG_LOW == o_CRC_flag) {
                Print_Seed(fp_uncor_seed, 0, filename_uncor_seed, current_seed);
            }
        }
        else if (MODE_SEED_SAVE_CORNER_SEED == m_param_ref_c->mode_seed) {
            if (FLAG_HIGH == flag_update_corner_check) {
                Print_Seed(fp_uncor_seed, 0, filename_uncor_seed, current_seed);
            }
        }
        else if (MODE_SEED_SAVE_ALL_SEED == m_param_ref_c->mode_seed) {
            Print_Seed(fp_uncor_seed, 0, filename_uncor_seed, current_seed);
        }
#ifdef __AUTO_LLR_OPT__
        if (MODE_SEED_LOAD_UNCOR_SEED_SAVE_UNCOR_SEED == m_param_ref_c->mode_seed) {
            if (FLAG_HIGH == o_CRC_flag) {
                Print_Seed(fp_uncor_seed, 0, filename_uncor_seed_2nd_decode, current_seed);
            }
        }
#endif
        /* print intermediate result */
#if defined (__RUN_MPI__)
        if ((rn % DISPLAY_UNIT_MPI) == 0) {
            if (Gather_Result_MPI(FALSE, rn, iter_sum, clk_sum, fr_4KB, fr_over_fly, m_param_dec->MN_num)) {
                rn++;
                break;
            }
        }
#else
        if ((rn % DISPLAY_UNIT) == 0) {
#ifdef __AUTO_LLR_OPT__
#if defined (__WIN_OS__)
            Print_Result_Part2_Memory_Opt_Auto(FALSE, rn, fr_4KB, iter_sum, clk_sum, clk_sum_throughput, FALSE, m_param_ref_c->FER_local);
#endif // __WIN_OS__
#else
            Print_Result_Part2_Memory_Opt(FALSE, rn, fr_4KB, iter_sum, clk_sum, clk_sum_throughput, FALSE, m_param_ref_c->FER_local);
#endif // __AUTO_LLR_OPT__
        }
#endif
        Update_Log_Data();
        if (MODE_DEC_HD == m_param_dec->init_n) {
            if (FLAG_LOW == o_CRC_flag) {
                Update_Log_Iter_Histogram(o_iter_num, o_str_n_error);
            }
            else {
                Update_Log_Iter_Histogram(o_iter_num, 3);
            }
        }
        /* increase frame counter */
        rn++;
    }// end while
#ifdef __AUTO_LLR_OPT__
    if (MODE_SEED_SAVE_UNCOR_SEED_LOAD_INIT_SEED == m_param_ref_c->mode_seed || MODE_SEED_DEFAULT_LOAD_INIT_SEED == m_param_ref_c->mode_seed) {
        xor_r25_u32(current_seed);    // 반환값 미사용 (상태 전진만) — 나눗셈 생략, 상태 갱신 동일
        Print_Init_Seed(fp_init_seed, 0, filename_init_seed, current_seed);
    }
#endif
    Print_Log_Data();
    Release_Log_Data();
    Print_Corner_Checker_Total();
}

//================================================
// Sector TV
//================================================
void ECC_Top::Run_TV_Gen_Scenario_4KB()
{
    int input_msg_type_num;
    int input_idx;
    int err_idx;
    int TV_idx;
    int N;
    int M;
    int N_b;
    int M_b;
    int crc_shortened_bits = CRC_LOGIC_SHORTENED;
    FILE * fp_tv_report;

    if (MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_tv_gen->mode_scenario) {
        N = m_PCM.N;
        M = m_PCM.M;
        N_b = m_PCM.N_b;
        M_b = m_PCM.M_b;
    }

    Set_Bit_Pos();

#if defined (__ENC_TV_ONLY__)
    input_msg_type_num = TV_INPUT_PATTERN_SIZE_ENC_ONLY;
#else
    input_msg_type_num = TV_INPUT_PATTERN_SIZE;
#endif
    
    if ((MODE_TV_CASE_HD_POWER_0 <= m_param_tv_gen->TS_idx) && (MODE_TV_CASE_HD_POWER_500 >= m_param_tv_gen->TS_idx)){
        input_msg_type_num = 1;
    }

#if defined(__ENC_TV_ONLY_SINGLE_FILE__)
    m_tv_enc.Set_TV_idx(EMPTY); //
    m_tv_enc.Open();
#endif

    fp_tv_report = fopen("c_tv_report.txt", "w");
    if ((MODE_TV_CASE_HD_MASS == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_2SD_MASS == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_3SD_MASS == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_1_5SD_MASS == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_HD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_HD_XOR25_SEED_FIXED == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_2SD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_3SD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx)
        ) {
        m_dec.Set_TV_Cycle_Based_On(FALSE);
    }

    for (input_idx = 0; input_idx < input_msg_type_num; input_idx++) {

        for (err_idx = 0; err_idx < m_param_tv_gen->err_case; err_idx++) {
            TV_idx = (m_param_tv_gen->err_case * input_idx) + err_idx;

            printf("TV_idx : %d\n", TV_idx);
            /* Generate message */
            if (TV_idx > 0) {
                fprintf(fp_tv_report, "\n");
            }
            fprintf(fp_tv_report, "TV_idx : %04d\n", TV_idx);

#if defined (__TV_LOG_FIFO_POWER_STOPPING__)
            Print_TV_Log_FIFO(TV_idx);
            Print_TV_Log_Power_Stopping(TV_idx);
#endif
            /* Generate message */
            Make_Msg_TV(m_msg, N - M, input_idx, m_param_tv_gen->mode_rand);

            /* Invert or copy message */
            if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
                for (int n = 0; n < N - M; n++) { m_inv_msg[n] = m_msg[n] ^ 1; }
            }
            else if (MODE_ALL_ZERO_CODEWORD == m_ecc_info->mode_all_one_cw) {
                memcpy(m_inv_msg, m_msg, (N - M) * sizeof(int));
            }

            /* Information Shortening */
            for (int n = m_ecc_info->bit_pos.info_sh_start; n < m_ecc_info->bit_pos.info_sh_end; n++) {
                m_inv_msg[n] = 0;
            }

            /* CRC encoding */
            CRC_encoder(m_inv_msg, N_b - M_b, crc_shortened_bits);    //
            /* LDPC encoding */

#if defined(__ENC_TV_INTER_DEBUG__)
            m_enc.LDPC_encoder_4KB(m_inv_cw, m_inv_msg, m_Parity_inter);
#else
            m_enc.LDPC_encoder_4KB(m_inv_cw, m_inv_msg);
#endif
            /* Re-invert or copy codeword*/
            if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
                for (int n = 0; n<N; n++) { m_cw[n] = (m_inv_cw[n] + 1)%2; }
            }
            else if (MODE_ALL_ZERO_CODEWORD == m_ecc_info->mode_all_one_cw) {
                for (int n = 0; n<N; n++) { m_cw[n] = m_inv_cw[n]; }
            }
            if (err_idx == 0) {
#ifndef __ENC_TV_ONLY_SINGLE_FILE__
                m_tv_enc.Set_TV_idx(input_idx);
                m_tv_enc.Open();
#endif
                m_tv_enc.Print_TV_Enc_In(m_msg);
                m_tv_enc.Print_TV_Enc_Out(m_cw, TRUE, TRUE);
                m_tv_enc.Print_Empty_Line(TRUE, TRUE, TRUE);
#if defined(__ENC_TV_INTER_DEBUG__)
                m_tv_enc.Print_TV_Enc_Inter(m_Parity_inter);
#endif
#ifndef __ENC_TV_ONLY_SINGLE_FILE__
                m_tv_enc.Close();
#endif
            }
#ifndef __ENC_TV_ONLY__
            /* Make decoder input */
            Make_TV_Fixed_Err_Case_4KB(err_idx);
            Make_Dec_Input_TV_Fixed_4KB(m_cw, m_HD_channel, m_SD_channel, m_CC_channel, m_CD_channel, fp_tv_report);
            /* Copy buffer */
            memcpy(m_HD_input, m_HD_channel, N * sizeof(int));
            memcpy(m_SD_input, m_SD_channel, N * sizeof(int));
            memcpy(m_CC_input, m_CC_channel, N * sizeof(int));
            memcpy(m_CD_input, m_CD_channel, N * sizeof(int));
            memcpy(m_inv_cw_input, m_inv_cw, N * sizeof(int));
#if defined (__FIXED_SECTOR_NUMBER__)
            if (TV_idx == 0) {
                Intentional_Blank();
            }
            else {
                continue;
            }
#endif
            m_tv_dec.Set_TV_idx(TV_idx, EMPTY);
            m_tv_dec.Open();
            /* LDPC decoding */
            m_dec.LDPC_Decoder(m_HD_input, m_SD_input, m_CC_input, m_CD_input, m_param_dec->init_n, m_inv_cw_input,
                TV_idx, EMPTY,
                &o_iter_num, &o_CRC_flag, &o_n_error, &o_str_n_error, &o_1_counter, &o_0_1_flip_counter, m_dec_output, &o_BF_on, &o_overall_clk, &o_weak_n_cor);
            fprintf(fp_tv_report, "===> o_CRC_flag : %d,\to_n_error : %d,\to_iter_num : %d\n\n", o_CRC_flag, o_n_error, o_iter_num);
            m_tv_dec.Print_TV_Dec_In(m_HD_input, m_SD_input, m_CC_input, m_CD_input, TRUE, TRUE);
            m_tv_dec.Print_TV_Dec_Out(m_dec_output, m_HD_input, o_CRC_flag, TRUE, TRUE, TRUE);
            m_tv_dec.Close();
#endif
        }// end for loop (err_idx)
    } // end for loop (input_idx)
#if defined(__ENC_TV_ONLY_SINGLE_FILE__)
    m_tv_enc.Close();
#endif
    fclose(fp_tv_report);
}
void ECC_Top::Run_TV_Gen_Scenario_4KB_XOR25_Seed_File()
{
    int TV_idx;
    int N;
    int M;
    int N_b;
    int M_b;
    int crc_shortened_bits = CRC_LOGIC_SHORTENED;
    FILE * fp_tv_report = NULL;
    int TV_num;
    if (MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_tv_gen->mode_scenario) {
        N = m_PCM.N;
        M = m_PCM.M;
        N_b = m_PCM.N_b;
        M_b = m_PCM.M_b;
    }
    if ((MODE_TV_CASE_HD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_HD_XOR25_SEED_FIXED == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_2SD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_2SD_XOR25_SEED_STRONG_ERROR == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_3SD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_1_5SD_XOR25_SEED_ERASURE == m_param_tv_gen->TS_idx)) {
    m_dec.Set_TV_Cycle_Based_On(FALSE);
    }
    Set_Bit_Pos();
    m_tv_enc.Set_TV_idx(EMPTY); // @@ @@ file@@ @@@
    m_tv_enc.Open();
    fp_tv_report = fopen("c_tv_report.txt", "w");
    //======================================
    // @@@@ @@@ parameter @t@
    //======================================
    if (MODE_CH_RBER == m_param_tv_gen->ch_type) {
        sprintf(filename_uncor_seed, "uncor_seed_H_%d_CH_%d_E%.2e_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_tv_gen->ch_type, m_param_tv_gen->RBER, m_param_dec->init_n, m_my_rank);
    }
    else if (MODE_CH_FIXED_ERROR == m_param_tv_gen->ch_type) {
        sprintf(filename_uncor_seed, "uncor_seed_H_%d_CH_%d_E%d_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_tv_gen->ch_type, m_param_tv_gen->num_fixed_err, m_param_dec->init_n, m_my_rank);
    }
    else if (MODE_CH_STRONG_ERROR == m_param_tv_gen->ch_type) {
        sprintf(filename_uncor_seed, "uncor_seed_H_%d_CH_%d_E%d_SC_%.2f_SE_%.2f_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_tv_gen->ch_type, m_param_tv_gen->num_fixed_err, m_param_tv_gen->fixed_SCR, m_param_tv_gen->fixed_SER, m_param_dec->init_n, m_my_rank);
    }
    else if (MODE_CH_ERASURE == m_param_tv_gen->ch_type) {
        sprintf(filename_uncor_seed, "uncor_seed_H_%d_CH_%d_E%d_E_%.3f_init_n_%d_%d.txt", m_ecc_info->matrix_sel, m_param_tv_gen->ch_type, m_param_tv_gen->num_fixed_err, m_param_tv_gen->fixed_erasure_ratio, m_param_dec->init_n, m_my_rank);
    }
    else {
        sprintf(filename_uncor_seed, "uncor_seed_S_%d_H_%d_init_n_%d_%d.txt", m_param_tv_gen->mode_scenario, m_ecc_info->matrix_sel, m_param_dec->init_n);
    }
    printf("seed filename: %s\n", filename_uncor_seed);
    fp_uncor_seed = fopen(filename_uncor_seed, "rt");
    Load_ECC_Input_TV(fp_uncor_seed, filename_uncor_seed, &TV_num);
    for (TV_idx = 0; TV_idx < TV_num; TV_idx++) {
        printf("TV_idx : %d\n", TV_idx);
        if (TV_idx > 0) {
            fprintf(fp_tv_report, "\n");
        }
        fprintf(fp_tv_report, "TV_idx : %04d\n", TV_idx);
#if defined (__TV_LOG_FIFO_POWER_STOPPING__)
        Print_TV_Log_FIFO(TV_idx);
        Print_TV_Log_Power_Stopping(TV_idx);
#endif
        Read_Seed(fp_uncor_seed, current_seed);
        Set_Random_Seed(current_seed);
        /* Generate message */
        rand_msg_xor25(m_msg, N - M);
        /* Invert or copy message */
        if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
            for (int n = 0; n < N - M; n++) { m_inv_msg[n] = m_msg[n] ^ 1; }
        }
        else if (MODE_ALL_ZERO_CODEWORD == m_ecc_info->mode_all_one_cw) {
            memcpy(m_inv_msg, m_msg, (N - M) * sizeof(int));
        }
        /* Information Shortening */
        for (int n = m_ecc_info->bit_pos.info_sh_start; n < m_ecc_info->bit_pos.info_sh_end; n++) {
            m_inv_msg[n] = 0;
        }
        /* CRC encoding */
        CRC_encoder(m_inv_msg, N_b - M_b, crc_shortened_bits);
        /* LDPC encoding */
        m_enc.LDPC_encoder_4KB(m_inv_cw, m_inv_msg);
        /* Re-invert or copy codeword */
        if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
            for (int n = 0; n < N; n++) { m_cw[n] = m_inv_cw[n] ^ 1; }
        }
        else if (MODE_ALL_ZERO_CODEWORD == m_ecc_info->mode_all_one_cw) {
            memcpy(m_cw, m_inv_cw, N * sizeof(int));
        }
#if defined(__NAND_IO_DELIVERY__)
#else
        m_tv_enc.Print_TV_Enc_In(m_msg);
        m_tv_enc.Print_TV_Enc_Out(m_cw, TRUE, TRUE);
        m_tv_enc.Print_Empty_Line(TRUE, TRUE, TRUE);
#endif
        /* Make decoder input */
        //======================================
        // @@@@ @@@ parameter @t@
        //======================================
        if ((MODE_TV_CASE_HD_XOR25_SEED_FIXED == m_param_tv_gen->TS_idx) ||
            (MODE_TV_CASE_2SD_XOR25_SEED_STRONG_ERROR == m_param_tv_gen->TS_idx) ||
            (MODE_TV_CASE_1_5SD_XOR25_SEED_ERASURE== m_param_tv_gen->TS_idx)){
            Make_Dec_Input_TV_Gen_Fixed_4KB(m_cw, m_HD_channel, m_SD_channel, m_CC_channel, m_CD_channel);
        }
        else if ((MODE_TV_CASE_HD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
            (MODE_TV_CASE_2SD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
            (MODE_TV_CASE_3SD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx)){
            Make_Dec_Input_TV_Gen_AWGN(N, m_cw, m_cwt, m_cwr, m_HD_channel, m_SD_channel, m_CC_channel, m_CD_channel);
        }
        /* Copy buffer */
        memcpy(m_HD_input, m_HD_channel, N * sizeof(int));
        memcpy(m_SD_input, m_SD_channel, N * sizeof(int));
        memcpy(m_CC_input, m_CC_channel, N * sizeof(int));
        memcpy(m_CD_input, m_CD_channel, N * sizeof(int));
        memcpy(m_inv_cw_input, m_inv_cw, N * sizeof(int));
        m_tv_dec.Set_TV_idx(TV_idx, EMPTY);
        m_tv_dec.Open();
        /* LDPC decoding */
        m_dec.LDPC_Decoder(m_HD_input, m_SD_input, m_CC_input, m_CD_input, m_param_dec->init_n, m_inv_cw_input,
            TV_idx, EMPTY,
            &o_iter_num, &o_CRC_flag, &o_n_error, &o_str_n_error, &o_1_counter, &o_0_1_flip_counter, m_dec_output, &o_BF_on, &o_overall_clk, &o_weak_n_cor);
        fprintf(fp_tv_report, "===> o_CRC_flag : %d,\to_n_error : %d,\to_iter_num : %d\n\n", o_CRC_flag, o_n_error, o_iter_num);
        m_tv_dec.Print_TV_Dec_In(m_HD_input, m_SD_input, m_CC_input, m_CD_input, TRUE, TRUE);
        m_tv_dec.Print_TV_Dec_Out(m_dec_output, m_HD_input, o_CRC_flag, TRUE, TRUE, TRUE);
        m_tv_dec.Close();
    }
    m_tv_enc.Close();
    fclose(fp_tv_report);
    fclose(fp_uncor_seed);
}
void ECC_Top::Run_TV_Gen_Scenario_4KB_DIN_File()
{
    int TV_idx = 0;
    int N = 0;
    int M = 0;
    int N_b = 0;
    int M_b = 0;
    int crc_shortened_bits = CRC_LOGIC_SHORTENED;
    FILE * fp_tv_report = NULL;
    int TV_num;
    int len_noPS;
    if (MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_tv_gen->mode_scenario) {
        N = m_PCM.N;
        M = m_PCM.M;
        N_b = m_PCM.N_b;
        M_b = m_PCM.M_b;
        len_noPS = m_PCM.N - (m_ecc_info->shortened_bit_info + m_ecc_info->punctured_bit_info + m_ecc_info->punctured_bit_parity);
    }
    Set_Bit_Pos();
    fp_tv_report = fopen("c_tv_report.txt", "w");
    //======================================
    // @@@@ @@@ parameter @t@
    //======================================
    sprintf(filename_uncor_seed, "uncor_seed_S_%d_H_%d_init_n_%d.dat", m_param_tv_gen->mode_scenario, m_ecc_info->matrix_sel, m_param_dec->init_n);
    printf("seed filename: %s\n", filename_uncor_seed);
    fp_uncor_seed = fopen(filename_uncor_seed, "rt");
    Load_ECC_Input_TV(fp_uncor_seed, filename_uncor_seed, &TV_num);
    for (TV_idx = 0; TV_idx < TV_num; TV_idx++) {
        printf("TV_idx : %d\n", TV_idx);
        if (TV_idx > 0) {
            fprintf(fp_tv_report, "\n");
        }
        fprintf(fp_tv_report, "TV_idx : %04d\n", TV_idx);
#if defined (__TV_LOG_FIFO_POWER_STOPPING__)
        Print_TV_Log_FIFO(TV_idx);
        Print_TV_Log_Power_Stopping(TV_idx);
#endif

        rand_msg_xor25(m_msg, N - M);

        /* Invert or copy message */
        if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
            for (int n = 0; n < N - M; n++) { m_inv_msg[n] = m_msg[n] ^ 1; }
        }
        else if (MODE_ALL_ZERO_CODEWORD == m_ecc_info->mode_all_one_cw) {
            memcpy(m_inv_msg, m_msg, (N - M) * sizeof(int));
        }
        /* Information Shortening */
        for (int n = m_ecc_info->bit_pos.info_sh_start; n < m_ecc_info->bit_pos.info_sh_end; n++) {
            m_inv_msg[n] = 0;
        }
        /* CRC encoding */
        CRC_encoder(m_inv_msg, N_b - M_b, crc_shortened_bits);
        /* LDPC encoding */
        m_enc.LDPC_encoder_4KB(m_inv_cw, m_inv_msg);
        /* Re-invert or copy codeword */
        if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
            for (int n = 0; n < N; n++) { m_cw[n] = m_inv_cw[n] ^ 1; }
        }
        else if (MODE_ALL_ZERO_CODEWORD == m_ecc_info->mode_all_one_cw) {
            memcpy(m_cw, m_inv_cw, N * sizeof(int));
        }
        /* Make decoder input */
        //======================================
        // @@@@ @@@ parameter @t@
        //======================================
        Load_Dec_Input_Vector_Format(N, len_noPS);
        /* Copy buffer */
        memcpy(m_HD_input, m_HD_channel, N * sizeof(int));
        memcpy(m_SD_input, m_SD_channel, N * sizeof(int));
        memcpy(m_CC_input, m_CC_channel, N * sizeof(int));
        memcpy(m_CD_input, m_CD_channel, N * sizeof(int));
        memcpy(m_inv_cw_input, m_inv_cw, N * sizeof(int));
        m_tv_dec.Set_TV_idx(TV_idx, EMPTY);
        m_tv_dec.Open();
        /* LDPC decoding */
        m_dec.LDPC_Decoder(m_HD_input, m_SD_input, m_CC_input, m_CD_input, m_param_dec->init_n, m_inv_cw_input,
            TV_idx, EMPTY,
            &o_iter_num, &o_CRC_flag, &o_n_error, &o_str_n_error, &o_1_counter, &o_0_1_flip_counter, m_dec_output, &o_BF_on, &o_overall_clk, &o_weak_n_cor);
        fprintf(fp_tv_report, "===> o_CRC_flag : %d,\to_n_error : %d,\to_iter_num : %d\n\n", o_CRC_flag, o_n_error, o_iter_num);
        m_tv_dec.Print_TV_Dec_In(m_HD_input, m_SD_input, m_CC_input, m_CD_input, TRUE, TRUE);
        m_tv_dec.Print_TV_Dec_Out(m_dec_output, m_HD_input, o_CRC_flag, TRUE, TRUE, TRUE);
        m_tv_dec.Close();
    }
    fclose(fp_tv_report);
    fclose(fp_uncor_seed);
}
//================================================
// TV@@ @@@@@ folder@@ @@@@@V@.
//================================================
void ECC_Top::Make_TV_Folder()
{
    char output_foldername[LEN_FILENAME];
    sprintf(output_foldername, "output");
#if defined (__WIN_OS__)
    if (_mkdir(output_foldername) == 1) {
        printf("Directory '%s' is successfully created\n", output_foldername);
    }
#else
    if (mkdir(output_foldername, 0777) == 0) {
        printf("Directory '%s' is successfully created\n", output_foldername);
    }
#endif
}
//================================================
// TV@@@@ @@@G@ error @@@@ @@@@@V@.
//================================================
void ECC_Top::Make_TV_Fixed_Err_Case_4KB(int e)
{
    int c4, c3, c2, c1; // very strong correct, normal strong correct,  normal weak correct,     very weak correct
    int e4, e3, e2, e1; // very strong error,    normal strong error,    normal weak error,       very weak error
    int e_pos, e_step;
    int temp;
    int len_noPS;
    if (MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_tv_gen->mode_scenario) {
        len_noPS = m_PCM.N - m_ecc_info->shortened_bit_info - m_ecc_info->punctured_bit_info - m_ecc_info->punctured_bit_parity;
    }
    c1 = 0; c2 = 0; c3 = 0; c4 = 0;
    e1 = 0; e2 = 0; e3 = 0; e4 = 0;
    e_pos = 0; e_step = 0;
    if (MODE_TV_CASE_HD_NORMAL == m_param_tv_gen->TS_idx) {
        if (e == 0) e1 = 37;
        else if (e == 1) e1 = 37 * 2;
        else if (e == 2) e1 = 37 * 3;
        else if (e == 3) e1 = 37 * 5;
        else if (e == 4) e1 = 37 * 7;
        else if (e == 5) e1 = 37 * 10;
        else if (e == 6) e1 = 37 * 20;
        else if (e == 7) e1 = 256 * 72;
        else e1 = 37 * 8;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_A == m_param_tv_gen->TS_idx) {
        e1 = 200 + (10 * e);
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_B == m_param_tv_gen->TS_idx) {
        e1 = 233 + (4 * e);
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_C == m_param_tv_gen->TS_idx) {
        e1 = 1000 + (1000 * e);
        c1 = len_noPS - e1;
        e_step = 1;
        e_pos = e;
    }
    else if (MODE_TV_CASE_HD_D == m_param_tv_gen->TS_idx) {
        e1 = 32;
        c1 = len_noPS - e1;
        e_step = 2;
        e_pos = e;
    }
    else if (MODE_TV_CASE_HD_E == m_param_tv_gen->TS_idx) {
        e1 = 131;
        c1 = len_noPS - e1;
        e_step = 64;
        e_pos = 0;
    }
    else if (MODE_TV_CASE_HD_POWER_0 == m_param_tv_gen->TS_idx) {
        e1 = 0;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_POWER_50 == m_param_tv_gen->TS_idx) {
        e1 = 50;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_POWER_100 == m_param_tv_gen->TS_idx) {
        e1 = 100;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_POWER_150 == m_param_tv_gen->TS_idx) {
        e1 = 150;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_POWER_155 == m_param_tv_gen->TS_idx) {
        e1 = 155;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_POWER_165 == m_param_tv_gen->TS_idx) {
        e1 = 165;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_POWER_200 == m_param_tv_gen->TS_idx) {
        e1 = 200;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_POWER_250 == m_param_tv_gen->TS_idx) {
        e1 = 250;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_POWER_300 == m_param_tv_gen->TS_idx) {
        e1 = 300;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_POWER_350 == m_param_tv_gen->TS_idx) {
        e1 = 350;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_POWER_400 == m_param_tv_gen->TS_idx) {
        e1 = 400;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_POWER_450 == m_param_tv_gen->TS_idx) {
        e1 = 450;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_HD_POWER_500 == m_param_tv_gen->TS_idx) {
        e1 = 500;
        c1 = len_noPS - e1;
    }
    else if (MODE_TV_CASE_2SD_NORMAL == m_param_tv_gen->TS_idx) {
        if (e == 0) { e2 = 20;      e1 = 20;     c1 = 1600; }
        else if (e == 1) { e2 = 30;      e1 = 40;     c1 = 1600; }
        else if (e == 2) { e2 = 40;      e1 = 10;     c1 = 1600; }
        else if (e == 3) { e2 = 50;      e1 = 50;     c1 = 10000; }
        else if (e == 4) { e2 = 15;      e1 = 100;    c1 = 600; }
        else if (e == 5) { e2 = 100;     e1 = 300;    c1 = 5000; }
        else if (e == 6) { e2 = 200;     e1 = 200;    c1 = 25600; }
        else if (e == 7) { e2 = 16000;   e1 = 1000;   c1 = 1600; }
        else { e2 = 200;     e1 = 400;    c1 = 2000; }
        c2 = len_noPS - (c1 + e1 + e2);
    }
    else if (MODE_TV_CASE_2SD_A == m_param_tv_gen->TS_idx) {
        e1 = 100 + (100 * e);
        e2 = 30;
        c1 = 1000;
        c2 = len_noPS - (c1 + e1 + e2);
    }
    else if (MODE_TV_CASE_2SD_B == m_param_tv_gen->TS_idx) {
        e2 = 10;
        e1 = 54;
        c1 = 0;
        c2 = len_noPS - (c1 + e1 + e2);
        e_step = 1;
        e_pos = e;
    }
    else if (MODE_TV_CASE_2SD_C == m_param_tv_gen->TS_idx) {
        e2 = 10;
        e1 = 121;
        c1 = 1000;
        c2 = len_noPS - (c1 + e1 + e2);
        e_step = 1;
        e_pos = 0;
    }
    else if (MODE_TV_CASE_3SD_NORMAL == m_param_tv_gen->TS_idx) {
        if (e == 0) { e4 = 20;      e3 = 20;     e2 = 10;     e1 = 10;     c1 = 400;    c2 = 400;    c3 = 400; }
        else if (e == 1) { e4 = 30;      e3 = 30;     e2 = 20;     e1 = 10;     c1 = 400;    c2 = 400;    c3 = 400; }
        else if (e == 2) { e4 = 50;      e3 = 10;     e2 = 10;     e1 = 10;     c1 = 400;    c2 = 400;    c3 = 400; }
        else if (e == 3) { e4 = 30;      e3 = 30;     e2 = 50;     e1 = 0;      c1 = 400;    c2 = 400;    c3 = 400; }
        else if (e == 4) { e4 = 40;      e3 = 10;     e2 = 10;     e1 = 150;    c1 = 400;    c2 = 400;    c3 = 400; }
        else if (e == 5) { e4 = 50;      e3 = 150;    e2 = 150;    e1 = 200;    c1 = 400;    c2 = 400;    c3 = 400; }
        else if (e == 6) { e4 = 50;      e3 = 50;     e2 = 50;     e1 = 16000;  c1 = 400;    c2 = 400;    c3 = 400; }
        else if (e == 7) { e4 = 5000;    e3 = 5000;   e2 = 5000;   e1 = 5000;   c1 = 400;    c2 = 400;    c3 = 400; }
        else { e4 = 50;      e3 = 100;    e2 = 150;    e1 = 400;    c1 = 400;    c2 = 800;    c3 = 1600; }
        c4 = len_noPS - (c3 + c2 + c1 + e1 + e2 + e3 + e4);
    }
    else if (MODE_TV_CASE_3SD_A == m_param_tv_gen->TS_idx) {
        e4 = 200 + (200 * e);
        e3 = 100;
        e2 = 100;
        e1 = 100;
        c1 = 100;
        c2 = 100;
        c3 = 100;
        c4 = len_noPS - (c3 + c2 + c1 + e1 + e2 + e3 + e4);
    }
    else if (MODE_TV_CASE_3SD_B == m_param_tv_gen->TS_idx) {
        e4 = 20 + (20 * e);
        e3 = 1000;
        e2 = 1000;
        e1 = 1000;
        c1 = 1000;
        c2 = 1000;
        c3 = 1000;
        c4 = len_noPS - (c3 + c2 + c1 + e1 + e2 + e3 + e4);
    }
    else if (MODE_TV_CASE_3SD_C == m_param_tv_gen->TS_idx) {
        e4 = 10;
        e3 = 10;
        e2 = 10;
        e1 = 10;
        c1 = 10;
        c2 = 10;
        c3 = 10;
        c4 = len_noPS - (c3 + c2 + c1 + e1 + e2 + e3 + e4);
        e_step = 1;
        e_pos = e;
    }
    else if (MODE_TV_CASE_3SD_D == m_param_tv_gen->TS_idx) {
        e4 = 100;
        e3 = 100;
        e2 = 100;
        e1 = 101;
        c1 = 100;
        c2 = 100;
        c3 = 100;
        c4 = len_noPS - (c3 + c2 + c1 + e1 + e2 + e3 + e4);
        e_step = 1;
        e_pos = e;
    }
    else if (MODE_TV_CASE_1_5SD_NORMAL == m_param_tv_gen->TS_idx) {
        if (e == 0) e1 = 50;
        else if (e == 1) e1 = 50 * 2;
        else if (e == 2) e1 = 50 * 3;
        else if (e == 3) e1 = 50 * 5;
        else if (e == 4) e1 = 50 * 7;
        else if (e == 5) e1 = 50 * 10;
        else if (e == 6) e1 = 50 * 20;
        else if (e == 7) e1 = 50 * 72;
        else e1 = 50 * 8;

        e2 = e1 / 4;
        c1 = len_noPS - (e1 + e2);
    }

    /* copy */
    m_dec_in_status[0].len_noPS = len_noPS;
    m_dec_in_status[0].c1 = c1;
    m_dec_in_status[0].c2 = c2;
    m_dec_in_status[0].c3 = c3;
    m_dec_in_status[0].c4 = c4;
    m_dec_in_status[0].e1 = e1;
    m_dec_in_status[0].e2 = e2;
    m_dec_in_status[0].e3 = e3;
    m_dec_in_status[0].e4 = e4;
    m_param_tv_gen->e_pos = e_pos;
    m_param_tv_gen->e_step = e_step;
}
//=============================================
// @@C@@@@@ @@g@@ error@@ @@@@@V@.
//=============================================
void ECC_Top::Gen_Regular_Err(int * err_pos, int len_max, int e_num, int e_pos_col, int e_step)
{
    int i;
    int tmp;
    for (i = 0; i < e_num; i++) {
        tmp = (m_PCM.z_sb * e_pos_col) + (e_step * i);
        err_pos[i] = tmp % len_max;
    }
}
//=============================================
// TV@@ decoder input@@ @o@@@@@@@ @@@@
// @@@@ (4KB)
//=============================================
void ECC_Top::Make_Dec_Input_TV_Fixed_4KB(int * cw, int *HD_input, int * SD_input, int *CC_input, int * CD_input, FILE * fp)
{
    int N;
    int sel_pos_num;
    int len_noPS;
    int all_one_masking;
    int c1, c2, c3, c4;
    int e1, e2, e3, e4;
    if (MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_tv_gen->mode_scenario) {
        N = m_PCM.N;
    }
    if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
        all_one_masking = 1;
    }
    else {
        all_one_masking = 0;
    }
    /* Copy */
    for (int n = 0; n < N; n++) {
        HD_input[n] = cw[n];
        SD_input[n] = 1;
        CC_input[n] = 1;
        CD_input[n] = cw[n];
    }
    len_noPS = m_dec_in_status[0].len_noPS;
    e1 = m_dec_in_status[0].e1;
    e2 = m_dec_in_status[0].e2;
    e3 = m_dec_in_status[0].e3;
    e4 = m_dec_in_status[0].e4;
    c1 = m_dec_in_status[0].c1;
    c2 = m_dec_in_status[0].c2;
    c3 = m_dec_in_status[0].c3;
    c4 = m_dec_in_status[0].c4;
    /* Error injection */
    if (MODE_DEC_HD == m_param_dec->init_n) {
        sel_pos_num = e1;
        if (MODE_TV_ERR_POS_RANDOM == m_param_tv_gen->mode_error_pos) {
            rand_sel_ep(m_err_position_noPS, len_noPS, sel_pos_num, m_param_tv_gen->mode_rand);
        }
        else if (MODE_TV_ERR_POS_FIXED == m_param_tv_gen->mode_error_pos) {
            Gen_Regular_Err(m_err_position_noPS, len_noPS, sel_pos_num, m_param_tv_gen->e_pos, m_param_tv_gen->e_step);
        }
        Set_Real_Err_Pos_4KB(sel_pos_num);
    }
    else if (MODE_DEC_2SD == m_param_dec->init_n) {
        sel_pos_num = e2 + e1 + c1;
        if (MODE_TV_ERR_POS_RANDOM == m_param_tv_gen->mode_error_pos) {
            rand_sel_ep(m_err_position_noPS, len_noPS, sel_pos_num, m_param_tv_gen->mode_rand);
        }
        else if (MODE_TV_ERR_POS_FIXED == m_param_tv_gen->mode_error_pos) {
            Gen_Regular_Err(m_err_position_noPS, len_noPS, sel_pos_num, m_param_tv_gen->e_pos, m_param_tv_gen->e_step);
        }
        Set_Real_Err_Pos_4KB(sel_pos_num);
    }
    else if (MODE_DEC_3SD == m_param_dec->init_n) {
        sel_pos_num = e4 + e3 + e2 + e1 + c1 + c2 + c3;
        if (MODE_TV_ERR_POS_RANDOM == m_param_tv_gen->mode_error_pos) {
            rand_sel_ep(m_err_position_noPS, len_noPS, sel_pos_num, m_param_tv_gen->mode_rand);
        }
        else if (MODE_TV_ERR_POS_FIXED == m_param_tv_gen->mode_error_pos) {
            Gen_Regular_Err(m_err_position_noPS, len_noPS, sel_pos_num, m_param_tv_gen->e_pos, m_param_tv_gen->e_step);
        }
        Set_Real_Err_Pos_4KB(sel_pos_num);
    }
    else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
        sel_pos_num = e2 + e1;
        if (MODE_TV_ERR_POS_RANDOM == m_param_tv_gen->mode_error_pos) {
            rand_sel_ep(m_err_position_noPS, len_noPS, sel_pos_num, m_param_tv_gen->mode_rand);
        }
        else if (MODE_TV_ERR_POS_FIXED == m_param_tv_gen->mode_error_pos) {
            Gen_Regular_Err(m_err_position_noPS, len_noPS, sel_pos_num, m_param_tv_gen->e_pos, m_param_tv_gen->e_step);
        }
        Set_Real_Err_Pos_4KB(sel_pos_num);
    }
    if (fp != NULL) {
        fprintf(fp, "(c1, c2, c3, c4) = (%5d, %5d, %5d, %5d)\n", c1, c2, c3, c4);
        fprintf(fp, "(e1, e2, e3, e4) = (%5d, %5d, %5d, %5d)\n", e1, e2, e3, e4);
    }
    Make_Dec_Input_Fixed_4KB(HD_input, SD_input, CC_input, CD_input, all_one_masking, c1, c2, c3, c4, e1, e2, e3, e4, fp);
}
//=============================================
// Fixed error@@ @@@@@V@. (4KB)
//=============================================
void ECC_Top::Make_Dec_Input_Fixed_4KB(int * HD_input, int * SD_input, int * CC_input, int * CD_input,
    int all_one_masking, int c1, int c2, int c3, int c4, int e1, int e2, int e3, int e4, FILE * fp)
{
    int start_pos;
    int end_pos;
    //int ctrl_info_len = (m_PCM.N - m_PCM.M) - m_ecc_info->shortened_bit_info_offset_end - m_ecc_info->shortened_bit_info; // TBE
    int ctrl_info_len = (m_PCM.N - m_PCM.M) - m_ecc_info->shortened_bit_info_offset_end;    // TBE
    int info_err_cnt = 0;
    /* Error injection */
    if (MODE_DEC_HD == m_param_dec->init_n) {
        /* flip */
        start_pos = 0;
        end_pos = e1;
        for (int n = start_pos; n < end_pos; n++) {
            HD_input[m_err_position[n]] ^= 1;
            if (m_err_position[n] < ctrl_info_len) {
                info_err_cnt++;
            }
        }
    }
    else if (MODE_DEC_2SD == m_param_dec->init_n) {
        /* flip */
        start_pos = 0;
        end_pos = start_pos + e2 + e1;
        for (int n = 0; n < end_pos; n++) {
            HD_input[m_err_position[n]] ^= 1;
            if (m_err_position[n] < ctrl_info_len) {
                info_err_cnt++;
            }
        }
        /* weak */
        start_pos = e2;
        end_pos = start_pos + e1 + c1;
        for (int n = start_pos; n < end_pos; n++) {
            SD_input[m_err_position[n]] = 0;
        }
    }
    else if (MODE_DEC_3SD == m_param_dec->init_n) {
        /* flip */
        start_pos = 0;
        end_pos = start_pos + e4 + e3 + e2 + e1;
        for (int n = start_pos; n < end_pos; n++) {
            HD_input[m_err_position[n]] ^= 1;
            if (m_err_position[n] < ctrl_info_len) {
                info_err_cnt++;
            }
        }
        /* weak */
        start_pos = e4 + e3;
        end_pos = start_pos + e2 + e1 + c1 + c2;
        for (int n = start_pos; n < end_pos; n++) {
            SD_input[m_err_position[n]] = 0;
        }
        /* very */
        start_pos = e4;
        end_pos = start_pos + e3 + e2;
        for (int n = start_pos; n < end_pos; n++) {
            CC_input[m_err_position[n]] = 0;
        }
        start_pos = e4 + e3 + e2 + e1 + c1;
        end_pos = start_pos + c2 + c3;
        for (int n = start_pos; n < end_pos; n++) {
            CC_input[m_err_position[n]] = 0;
        }
    }
    else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
        /* flip */
        start_pos = 0;
        end_pos = start_pos + e2 + e1;
        for (int n = start_pos; n < end_pos; n++) {
            HD_input[m_err_position[n]] ^= 1;
            if (m_err_position[n] < ctrl_info_len) {
                info_err_cnt++;
            }
        }
        /* erasure */
        start_pos = e2;
        end_pos = start_pos + e1;
        for (int n = start_pos; n < end_pos; n++) {
            CD_input[m_err_position[n]] ^= 1;
        }
    }
    /* puncturing, shortening */
    for (int n = m_ecc_info->bit_pos.info_sh_start; n < m_ecc_info->bit_pos.info_sh_end; n++) {
        HD_input[n] = all_one_masking;
        CD_input[n] = all_one_masking;
    }
    for (int n = m_ecc_info->bit_pos.info_punc_start1; n < m_ecc_info->bit_pos.info_punc_end1; n++) {
        HD_input[n] = all_one_masking;
        CD_input[n] = all_one_masking;
    }
    for (int n = m_ecc_info->bit_pos.info_punc_start2; n < m_ecc_info->bit_pos.info_punc_end2; n++) {
        HD_input[n] = all_one_masking;
        CD_input[n] = all_one_masking;
    }
    /* BCH parity puncturing */
    for (int n = m_ecc_info->bit_pos.parity_punc_start; n < m_ecc_info->bit_pos.parity_punc_end; n++) {
        HD_input[n] = all_one_masking;
        CD_input[n] = all_one_masking;
    }
    if (fp != NULL) {
        //fprintf(fp, "input error num (info only) : %d\n", info_err_cnt);
    }
}
//=============================================
// AWGN @@ @@ SD offset@@ @@@@
// quantize@V@.
//=============================================
void ECC_Top::Make_Dec_Input_AWGN_Quantize(int N, double * cwr, double var, int *HD_input, int *SD_input, int *CC_input, int * CD_input)
{
    double Lq_ini;
    double Lq_ini_m;
    int hd;
    int sd;
    int cc;
    // init_n은 루프 불변 — bit당 모드 분기 체인을 모드별 전용 루프로 분리 (연산 순서·결과 동일)
    if (MODE_DEC_2SD == m_param_dec->init_n) {
        for (int n = 0; n < N; n++) {
            Lq_ini = (2.0 * cwr[n]) / var;
            Lq_ini_m = fabs(Lq_ini);
            if (cwr[n] >= 0)        HD_input[n] = 0;
            else                    HD_input[n] = 1;
            Get_Mag_2SD(Lq_ini_m, &sd);
            SD_input[n] = sd;
        }
    }
    else if (MODE_DEC_3SD == m_param_dec->init_n) {
        for (int n = 0; n < N; n++) {
            Lq_ini = (2.0 * cwr[n]) / var;
            Lq_ini_m = fabs(Lq_ini);
            if (cwr[n] >= 0)        HD_input[n] = 0;
            else                    HD_input[n] = 1;
            Get_Mag_3SD(Lq_ini_m, &sd, &cc);
            SD_input[n] = sd;
            CC_input[n] = cc;
        }
    }
    else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
        for (int n = 0; n < N; n++) {
            Lq_ini = (2.0 * cwr[n]) / var;
            if (cwr[n] >= 0)        HD_input[n] = 0;
            else                    HD_input[n] = 1;
            Get_Mag_1_5SD(Lq_ini, &hd, &sd);
            HD_input[n] = hd;
            CD_input[n] = (hd + sd) & 1;
        }
    }
    else {
        /* HD 모드: SD/CC/CD 출력 없음 */
        for (int n = 0; n < N; n++) {
            if (cwr[n] >= 0)        HD_input[n] = 0;
            else                    HD_input[n] = 1;
        }
    }
}
//=============================================
// Fixed error channel@@@@ decoder
// input@@ @@@@@V@.
// e4 == e3 == e2 == e1 == c1 == c2 == c3 == c4
//=============================================
void ECC_Top::Make_Dec_Input_Ref_C_Fixed_4KB(int * cw, int *HD_input, int * SD_input, int *CC_input, int * CD_input)
{
    int N;
    int err_pos_len;
    int len_noPS;
    int all_one_masking;
    int c1, c2, c3, c4;
    int e1, e2, e3, e4;
    double  temp_d;
    if (MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_ref_c->mode_scenario) {
        N = m_PCM.N;
        len_noPS = N - m_ecc_info->shortened_bit_info - m_ecc_info->punctured_bit_info - m_ecc_info->punctured_bit_parity;
    }
    if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
        all_one_masking = 1;
    }
    else {
        all_one_masking = 0;
    }
    /* Copy */
    for (int n = 0; n < N; n++) {
        HD_input[n] = cw[n];
        SD_input[n] = 1;
        CC_input[n] = 1;
        CD_input[n] = cw[n];
    }
    if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) {
        e1 = m_param_ref_c->num_fixed_err;
        e2 = 0;
        e3 = 0;
        e4 = 0;
        c1 = len_noPS - e1;
        c2 = 0;
        c3 = 0;
        c4 = 0;
        err_pos_len = e1;
        rand_sel_ep(m_err_position_noPS, len_noPS, err_pos_len, MODE_RANDOM_TYPE_XOR_25);
        Set_Real_Err_Pos_4KB(err_pos_len);
    }
    else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
        temp_d = (double)m_param_ref_c->num_fixed_err * m_param_ref_c->fixed_SER;
        e2 = (int)floor(temp_d + 0.5);    // round
        e1 = m_param_ref_c->num_fixed_err - e2;
        e3 = 0;
        e4 = 0;
        temp_d = (double)(len_noPS - e2 - e1) * m_param_ref_c->fixed_SCR;
        c2 = (int)floor(temp_d + 0.5);    // round
        c1 = len_noPS - e2 - e1 - c2;
        c3 = 0;
        c4 = 0;
        err_pos_len = e2 + e1 + c1;
        rand_sel_ep(m_err_position_noPS, len_noPS, err_pos_len, MODE_RANDOM_TYPE_XOR_25);
        Set_Real_Err_Pos_4KB(err_pos_len);
    }
    else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
        e2 = m_param_ref_c->num_fixed_err;
        temp_d = (double)(len_noPS - e2) * m_param_ref_c->fixed_erasure_ratio;
        e1 = (int)floor(temp_d + 0.5);    // round
        e3 = 0;
        e4 = 0;
        c1 = len_noPS - e2 - e1;
        c2 = 0;
        c3 = 0;
        c4 = 0;
        err_pos_len = e2 + e1;
        rand_sel_ep(m_err_position_noPS, len_noPS, err_pos_len, MODE_RANDOM_TYPE_XOR_25);
        Set_Real_Err_Pos_4KB(err_pos_len);
    }
    else if (MODE_CH_3SD_FIXED == m_param_ref_c->ch_type) {
        int E = 0;
        int C = 0;
        E = m_param_ref_c->num_fixed_err;
        C = len_noPS - E;
        temp_d = (double)E * m_param_ref_c->fixed_VSER;
        e4 = (int)floor(temp_d + 0.5);    // round
        temp_d = (double)E * m_param_ref_c->fixed_NSER;
        e3 = (int)floor(temp_d + 0.5);    // round
        temp_d = (double)E * m_param_ref_c->fixed_NWER;
        e2 = (int)floor(temp_d + 0.5);    // round
        e1 = E - (e2 + e3 + e4);
        temp_d = (double)C * m_param_ref_c->fixed_VSCR;
        c4 = (int)floor(temp_d + 0.5);    // round
        temp_d = (double)C * m_param_ref_c->fixed_NSCR;
        c3 = (int)floor(temp_d + 0.5);    // round
        temp_d = (double)C * m_param_ref_c->fixed_NWCR;
        c2 = (int)floor(temp_d + 0.5);    // round
        c1 = C - (c2 + c3 + c4);
        err_pos_len = e4 + e3 + e2 + e1 + c1 + c2 + c3;
        rand_sel_ep(m_err_position_noPS, len_noPS, err_pos_len, MODE_RANDOM_TYPE_XOR_25);
        Set_Real_Err_Pos_4KB(err_pos_len);
    }
    Make_Dec_Input_Fixed_4KB(HD_input, SD_input, CC_input, CD_input, all_one_masking, c1, c2, c3, c4, e1, e2, e3, e4, NULL);
}
//=============================================
// Fixed error channel@@@@ decoder
// input@@ @@@@@V@.
// e4 == e3 == e2 == e1 == c1 == c2 == c3 == c4
//=============================================
void ECC_Top::Make_Dec_Input_TV_Gen_Fixed_4KB(int * cw, int *HD_input, int * SD_input, int *CC_input, int * CD_input)
{
    int N;
    int err_pos_len;
    int len_noPS;
    int all_one_masking;
    int c1, c2, c3, c4;
    int e1, e2, e3, e4;
    int num_fixed_err = m_param_tv_gen->num_fixed_err;
    // SE Channel @@ (220118 KS)
    double  temp_d;
    double fixed_SCR = m_param_tv_gen->fixed_SCR;
    double fixed_SER = m_param_tv_gen->fixed_SER;
    double fixed_erasure_ratio = m_param_tv_gen->fixed_erasure_ratio;
    if (MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_tv_gen->mode_scenario) {
        N = m_PCM.N;
        len_noPS = N - m_ecc_info->shortened_bit_info - m_ecc_info->punctured_bit_info - m_ecc_info->punctured_bit_parity;
    }
    if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
        all_one_masking = 1;
    }
    else {
        all_one_masking = 0;
    }
    /* Copy */
    for (int n = 0; n < N; n++) {
        HD_input[n] = cw[n];
        SD_input[n] = 1;
        CC_input[n] = 1;
        CD_input[n] = cw[n];
    }
    if (MODE_DEC_HD == m_param_dec->init_n){
        //========================================
        // @@@@ @u@ parameter @t@
        //========================================
        e1 = num_fixed_err;
        e2 = 0;
        e3 = 0;
        e4 = 0;
        c1 = len_noPS - e1;
        c2 = 0;
        c3 = 0;
        c4 = 0;
        err_pos_len = e1;
        rand_sel_ep(m_err_position_noPS, len_noPS, err_pos_len, MODE_RANDOM_TYPE_XOR_25);
        Set_Real_Err_Pos_4KB(err_pos_len);
    }
    else if (MODE_DEC_2SD == m_param_dec->init_n) {
        temp_d = (double)num_fixed_err * fixed_SER;
        e2 = (int)floor(temp_d + 0.5);    // round
        e1 = num_fixed_err - e2;
        e3 = 0;
        e4 = 0;
        temp_d = (double)(len_noPS - e2 - e1) * fixed_SCR;
        c2 = (int)floor(temp_d + 0.5);    // round
        c1 = len_noPS - e2 - e1 - c2;
        c3 = 0;
        c4 = 0;
        err_pos_len = e2 + e1 + c1;
        rand_sel_ep(m_err_position_noPS, len_noPS, err_pos_len, MODE_RANDOM_TYPE_XOR_25);
        Set_Real_Err_Pos_4KB(err_pos_len);
    }
    else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
        e2 = num_fixed_err;
        temp_d = (double)(len_noPS - e2) * fixed_erasure_ratio;
        e1 = (int)floor(temp_d + 0.5);    // round
        e3 = 0;
        e4 = 0;
        c1 = len_noPS - e2 - e1;
        c2 = 0;
        c3 = 0;
        c4 = 0;
        err_pos_len = e2 + e1;
        rand_sel_ep(m_err_position_noPS, len_noPS, err_pos_len, MODE_RANDOM_TYPE_XOR_25);
        Set_Real_Err_Pos_4KB(err_pos_len);
    }
    Make_Dec_Input_Fixed_4KB(HD_input, SD_input, CC_input, CD_input, all_one_masking, c1, c2, c3, c4, e1, e2, e3, e4, NULL);
}
//=============================================
// Ref-C @@@ (o@@)
//=============================================
void ECC_Top::Print_Result_Part1(int Flag_16KB)
{
    int tmp;
    printf("********************************************************************************************\n");
    if (MODE_CH_RBER == m_param_ref_c->ch_type)             printf("RBER       ");
    else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) printf("Error      ");
    else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type)    printf("Error  SCR  SER    ");
    else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) printf("Error  Erasure_ratio   ");
    else if (MODE_CH_3SD_FIXED == m_param_ref_c->ch_type)   printf("Error VSCR  NSCR  NWCR  VWCR  VSER  NSER  NWER  VWER  ");
    printf("# frames  ");
    if (FALSE == Flag_16KB) {
        printf("Avg Iter    ");
        printf("FER (");
        for (int n = 0; n < m_param_dec->MN_num; n++) {
            if (n > 0) printf(" ");
            tmp = m_param_dec->MN[n];
            printf("%d", tmp);
        }
        printf(")");
        if (MODE_DEC_HD == m_param_dec->init_n) {
            printf("\t\tPr(Over_fly)");
        }
        printf("\n");
    }
}
//=============================================
// Ref-C @@@ (o@@)
//=============================================
void ECC_Top::Print_Result_Part1_Auto()
{
    int tmp;
    char fn_auto_result[LEN_FILENAME];
    sprintf(fn_auto_result, "Ref_C_result_%d.txt", m_param_ref_c->mode_init_seed);
    FILE* fp_auto_result;
    fp_auto_result = fopen(fn_auto_result, "a");
    fprintf(fp_auto_result, "********************************************************************************************\n");
    if (MODE_CH_RBER == m_param_ref_c->ch_type)                fprintf(fp_auto_result, "RBER\t");
    else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) fprintf(fp_auto_result, "Error\t");
    else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type)    fprintf(fp_auto_result, "Error\tSCR\tSER\t");
    else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) fprintf(fp_auto_result, "Error  Erasure_ratio   ");
    else if (MODE_CH_3SD_FIXED == m_param_ref_c->ch_type)   fprintf(fp_auto_result, "Error VSCR  NSCR  NWCR  VWCR  VSER  NSER  NWER  VWER  ");
    fprintf(fp_auto_result, "# frames\t");
    fprintf(fp_auto_result, "# errors\t");
    fprintf(fp_auto_result, "Avg Iter    ");
    fprintf(fp_auto_result, "FER (");
    for (int n = 0; n < m_param_dec->MN_num; n++) {
        if (n > 0) fprintf(fp_auto_result, " ");
        tmp = m_param_dec->MN[n];
        fprintf(fp_auto_result, "%d", tmp);
    }
    fprintf(fp_auto_result, ")");
    fprintf(fp_auto_result, "\n");
    fclose(fp_auto_result);
}
//=============================================
// Ref-C @@@ (o@@, @@@@)
//=============================================
void ECC_Top::Print_Result_Part2(int bFile, int rn, int* fr, double iter_sum, double clk_sum, double clk_sum_throughput, int bEnd, int Flag_16KB)
{
    double* FER = NULL;
    double  Pr_over_fly;
    double  temp_d;
    double  avg_iter;
    double  avg_clk;
    double  avg_clk_throughput;
    FILE* fp = NULL;
    int     MN_num = 1;
    if (FALSE == Flag_16KB) {
        MN_num = m_param_dec->MN_num;
    }
    FER = new double[MN_num];
    for (int i = 0; i < MN_num; i++) {
        temp_d = (double)fr[i] / rn;
        FER[i] = temp_d;
    }
    if (MODE_DEC_HD == m_param_dec->init_n) {
        Pr_over_fly = (double)fr_over_fly / rn;
    }
    avg_iter = iter_sum / rn;
    avg_clk = clk_sum / rn;
    avg_clk_throughput = clk_sum_throughput / rn;
    if (TRUE == bFile) {
        if (FALSE == Flag_16KB)
            fp = fopen(m_param_ref_c->str_result_name_4KB, "a");
    }
    else {
        fp = stdout;
    }
    if (MODE_CH_RBER == m_param_ref_c->ch_type)
        fprintf(fp, "%.2e\t", m_param_ref_c->RBER);
    else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type)
        fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
    else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
        fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
        fprintf(fp, "%.2f\t", m_param_ref_c->fixed_SCR);
        fprintf(fp, "%.2f\t", m_param_ref_c->fixed_SER);
    }
    else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
        fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
        fprintf(fp, "%.3f\t", m_param_ref_c->fixed_erasure_ratio);
    }
    else if (MODE_CH_3SD_FIXED == m_param_ref_c->ch_type) {
        fprintf(fp, "%-5d ", m_param_ref_c->num_fixed_err);
        fprintf(fp, "%.3f ", m_param_ref_c->fixed_VSCR);
        fprintf(fp, "%.3f ", m_param_ref_c->fixed_NSCR);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_NWCR);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_VWCR);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_VSER);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_NSER);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_NWER);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_VWER);
}
fprintf(fp, "%d\t", rn);
fprintf(fp, "%d\t", fr[m_param_dec->MN_num - 1]);
if (FALSE == Flag_16KB) {
	fprintf(fp, "%4.3f\t", avg_iter);
	for (int i = 0; i < m_param_dec->MN_num; i++) {
		fprintf(fp, "%.1e ", FER[i]);
	}
	//if (MODE_DEC_HD == m_param_dec->init_n) {
	//  fprintf(fp, "%.3e\t", Pr_over_fly);
	//}
	fprintf(fp, "%d\t", (int)avg_clk);
	fprintf(fp, "%d\t", (int)avg_clk_throughput);
}
if (TRUE == bFile) {
	Print_Excuting_Time(fp, TRUE, m_time_start, m_time_end);
	fclose(fp);
	fp = NULL;
}
else {
	if (TRUE == bEnd) {
		printf("\n");
	}
}
printf("\n");
delete[] FER;
FER = NULL;
}
//=============================================
// Ref-C 출력 (출력, 메모리옵션)
//=============================================
void ECC_Top::Print_Result_Part2_Memory_Opt(int bFile, int rn, int* fr, double iter_sum, double clk_sum, double clk_sum_throughput, int bEnd, double* FER)
{
	double Pr_over_fly;
	double avg_iter = iter_sum / rn;
	double avg_clk = clk_sum / rn;
	double avg_clk_throughput = clk_sum_throughput / rn;
	FILE* fp;
	for (int i = 0; i < m_param_dec->MN_num; i++) {
		FER[i] = (double)fr[i] / rn;
	}
	if (MODE_DEC_HD == m_param_dec->init_n) {
		Pr_over_fly = (double)fr_over_fly / rn;
	}
	if (TRUE == bFile) {
		fp = fopen(m_param_ref_c->str_result_name_4KB, "a");
	}
	else {
#ifdef __AUTO_LLR_OPT__
		char fn_auto_result[LEN_FILENAME];
		sprintf(fn_auto_result, "Ref_C_result_%d.txt", m_param_ref_c->mode_init_seed);
		fp = fopen(fn_auto_result, "a");
#else
		fp = stdout;
#endif
	}
	if (MODE_CH_RBER == m_param_ref_c->ch_type) {
	fprintf(fp, "%.2e\t", m_param_ref_c->RBER);
}
else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) {
	fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
}
else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
	fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
	fprintf(fp, "%.2f\t", m_param_ref_c->fixed_SCR);
	fprintf(fp, "%.2f\t", m_param_ref_c->fixed_SER);
}
else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
	fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
	fprintf(fp, "%.3f\t", m_param_ref_c->fixed_erasure_ratio);
}
else if (MODE_CH_3SD_FIXED == m_param_ref_c->ch_type) {
	fprintf(fp, "%-5d ", m_param_ref_c->num_fixed_err);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_VSCR);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_NSCR);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_NWCR);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_VWCR);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_VSER);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_NSER);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_NWER);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_VWER);
}
fprintf(fp, "%d\t", rn);
fprintf(fp, "%d\t", fr[m_param_dec->MN_num - 1]);
fprintf(fp, "%4.3f\t", avg_iter);
for (int i = 0; i < m_param_dec->MN_num; i++) {
	fprintf(fp, "%.1e ", FER[i]);
}
//if (MODE_DEC_HD == m_param_dec->init_n) {
//  fprintf(fp, "%.3e\t", Pr_over_fly);
//}
fprintf(fp, "%d\t", (int)avg_clk);
fprintf(fp, "%d\t", (int)avg_clk_throughput);
if (TRUE == bFile) {
	Print_Excuting_Time(fp, TRUE, m_time_start, m_time_end);
	fclose(fp);
}
else {
	if (TRUE == bEnd) {
		fprintf(fp, "\n");
	}
#ifdef __AUTO_LLR_OPT__
	fclose(fp);
#endif
	}
}
void ECC_Top::Print_Result_Part2_Memory_Opt_Auto(int bFile, int rn, int* fr, double iter_sum, double clk_sum, double clk_sum_throughput, int bEnd, double* FER)
{
	double Pr_over_fly;
	double avg_iter = iter_sum / rn;
	double avg_clk = clk_sum / rn;
	double avg_clk_throughput = clk_sum_throughput / rn;
	FILE* fp;
	for (int i = 0; i < m_param_dec->MN_num; i++) {
	FER[i] = (double)fr[i] / rn;
}
if (MODE_DEC_HD == m_param_dec->init_n) {
	Pr_over_fly = (double)fr_over_fly / rn;
}
if (TRUE == bFile) {
	fp = fopen(m_param_ref_c->str_result_name_4KB, "a");
}
else {
	char fn_auto_result[LEN_FILENAME];
	sprintf(fn_auto_result, "Ref_C_result_%d.txt", m_param_ref_c->mode_init_seed);
	fp = fopen(fn_auto_result, "a");
}
if (MODE_CH_RBER == m_param_ref_c->ch_type) {
	fprintf(fp, "%.2e\t", m_param_ref_c->RBER);
}
else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type){
	fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
}
else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
	fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
	fprintf(fp, "%.2f\t", m_param_ref_c->fixed_SCR);
	fprintf(fp, "%.2f\t", m_param_ref_c->fixed_SER);
}
else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
	fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
	fprintf(fp, "%.3f\t", m_param_ref_c->fixed_erasure_ratio);
}
else if (MODE_CH_3SD_FIXED == m_param_ref_c->ch_type) {
	fprintf(fp, "%-5d ", m_param_ref_c->num_fixed_err);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_VSCR);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_NSCR);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_NWCR);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_VWCR);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_VSER);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_NSER);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_NWER);
	fprintf(fp, "%.3f ", m_param_ref_c->fixed_VWER);
}
fprintf(fp, "%d\t", rn);
fprintf(fp, "%d\t", fr[m_param_dec->MN_num - 1]);
fprintf(fp, "%4.3f\t", avg_iter);
for (int i = 0; i < m_param_dec->MN_num; i++) {
	fprintf(fp, "%.1e\t", FER[i]);
}
//if (MODE_DEC_HD == m_param_dec->init_n) {
//  fprintf(fp, "%.3e\t", Pr_over_fly);
//}
fprintf(fp, "%d\t", (int)avg_clk);
fprintf(fp, "%d\t", (int)avg_clk_throughput);
if (TRUE == bFile) {
	Print_Excuting_Time(fp, TRUE, m_time_start, m_time_end);
}
else {
	fprintf(fp, "\n");
}
fclose(fp);
}
#if defined (__RUN_MPI__)
//=============================================
// MPI 결과 출력함수
//=============================================
void ECC_Top::Print_Result_MPI(int mode, int FER_num)
{
	int i;
	FILE * fp;
	char filename[LEN_FILENAME];
	double * FER = NULL;
	FER = new double[FER_num];
	double Pr_over_fly;
	double avg_iter;
	double avg_clk;
	int seed_idx;
	seed_idx = m_param_ref_c->mode_init_seed;
	if (MODE_CH_RBER == m_param_ref_c->ch_type) {
	sprintf(filename, "MPI_S_%d_H_%d_CH_%d_E%.2e_init_n_%d_seed_%d.txt",
		m_param_ref_c->mode_scenario,
		m_ecc_info->H_mat_idx, m_param_ref_c->ch_type,
		m_param_ref_c->RBER, m_param_dec->init_n,
		seed_idx);
}
else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) {
#ifndef __PCM_INPUT__
	sprintf(filename, "MPI_S_%d_H_%d_CH_%d_E%d_init_n_%d_seed_%d.txt",
		m_param_ref_c->mode_scenario,
		m_ecc_info->H_mat_idx, m_param_ref_c->ch_type,
		m_param_ref_c->num_fixed_err, m_param_dec->init_n,
		seed_idx);
#else
	sprintf(filename, "MPI_S_%d_H_%s_CH_%d_E%d_init_n_%d_seed_%d.txt",
		m_param_ref_c->mode_scenario,
		m_ecc_info->str_matrix_name, m_param_ref_c->ch_type,
		m_param_ref_c->num_fixed_err, m_param_dec->init_n,
		seed_idx);
#endif
}
else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
#ifdef __PCM_INPUT__
	sprintf(filename, "MPI_S_%d_H_%d_CH_%d_E%d_SC_%.2f_SE_%.2f_init_n_%d_seed_%d.txt",
		m_param_ref_c->mode_scenario,
		m_ecc_info->H_mat_idx, m_param_ref_c->ch_type,
		m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_SCR, m_param_ref_c->fixed_SER, m_param_dec->init_n,
		seed_idx);
#else
	sprintf(filename, "MPI_S_%d_H_%s_CH_%d_E%d_SC_%.2f_SE_%.2f_init_n_%d_seed_%d.txt",
		m_param_ref_c->mode_scenario,
		m_ecc_info->str_matrix_name, m_param_ref_c->ch_type,
		m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_SCR, m_param_ref_c->fixed_SER, m_param_dec->init_n,
		seed_idx);
#endif
}
else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
	sprintf(filename, "MPI_S_%d_H_%d_CH_%d_E%d_Erasure_%.2f_init_n_%d_seed_%d.txt",
		m_param_ref_c->mode_scenario,
		m_ecc_info->H_mat_idx, m_param_ref_c->ch_type,
		m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_erasure_ratio, m_param_dec->init_n,
		seed_idx);
}
else if (MODE_CH_3SD_FIXED == m_param_ref_c->ch_type) {
	sprintf(filename, "MPI_S_%d_H_%d_CH_%d_E_%d_%.3f_%.3f_%.3f_%.3f_%.3f_%.3f_%.3f_init_n_%d_seed_%d",
		m_param_ref_c->mode_scenario,
		m_ecc_info->H_mat_idx,
		m_param_ref_c->ch_type,
		m_param_ref_c->num_fixed_err,
		m_param_ref_c->fixed_VSCR,
		m_param_ref_c->fixed_NSCR,
		m_param_ref_c->fixed_NWCR,
		m_param_ref_c->fixed_VSER,
		m_param_ref_c->fixed_NSER,
		m_param_ref_c->fixed_NWER,
		m_param_dec->init_n,
		seed_idx);
}
fp = fopen(filename, "a");
if (MPI_PRINT_MODE_START == mode) {
	fprintf(fp, "Simulation starts...\n");
	fprintf(fp, "------------------------------------------------------------------------------------------------------\n");
}
else {
	for (int n; n < FER_num; n++) { FER[n] = tot_fr[n] / tot_rn; }
	if (MODE_DEC_HD == m_param_dec->init_n) {
		Pr_over_fly = (double)tot_fr_fly / tot_rn;
	}
	avg_iter = (double)tot_iter_sum / tot_rn;
	avg_clk = (double)tot_clk_sum / tot_rn;;
	if (MPI_PRINT_MODE_END == mode) {
		fprintf(fp, "------------------------------------------------------------------------------------------------------\n");
	}
	if (MODE_CH_RBER == m_param_ref_c->ch_type)		fprintf(fp, "%.2e\t", m_param_ref_c->RBER);
	else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
	else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
		fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
		fprintf(fp, "%.2f\t", m_param_ref_c->fixed_SCR);
		fprintf(fp, "%.2f\t", m_param_ref_c->fixed_SER);
	}
	else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
		fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
		fprintf(fp, "%.2f\t", m_param_ref_c->fixed_erasure_ratio);
	}
	else if (MODE_CH_3SD_FIXED == m_param_ref_c->ch_type) {
		fprintf(fp, "%-d\t", m_param_ref_c->num_fixed_err);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_VSCR);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_NSCR);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_NWCR);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_VWCR);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_VSER);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_NSER);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_NWER);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_VWER);
	}
	fprintf(fp, "%.0f\t", tot_rn);
	fprintf(fp, "%.0f\t", tot_fr[FER_num - 1]);
	fprintf(fp, "%3.3f\t", avg_iter);
	fprintf(fp, "%d\t", (int) avg_clk);
	for (i = 0; i < FER_num; i++) {
		fprintf(fp, "%.4e\t", FER[i]);
	}
	//if (MODE_DEC_HD == m_param_dec->init_n) {
	//  fprintf(fp, "%.4e\t", Pr_over_fly);
	//}
	if (MPI_PRINT_MODE_END == mode) {
		Print_Excuting_Time(fp, TRUE, m_time_start, m_time_end);
	}
	else {
		fprintf(fp, "\n");
	}
}
fclose(fp);
if (MPI_PRINT_MODE_END == mode) {
	sprintf(filename, "MPI_S_%d_H_%d_CH_%d_init_n_%d.txt",
		m_param_ref_c->mode_scenario,
		m_ecc_info->H_mat_idx, m_param_ref_c->ch_type,
		m_param_dec->init_n);
	fp = fopen(filename, "a");
	fprintf(fp, "%5d\t", seed_idx);
	if (MODE_CH_RBER == m_param_ref_c->ch_type)		fprintf(fp, "%.2e\t", m_param_ref_c->RBER);
	else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
	else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
		fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
		fprintf(fp, "%.2f\t", m_param_ref_c->fixed_SCR);
		fprintf(fp, "%.2f\t", m_param_ref_c->fixed_SER);
	}
	else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
		fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
		fprintf(fp, "%.2f\t", m_param_ref_c->fixed_erasure_ratio);
	}
	else if (MODE_CH_3SD_FIXED == m_param_ref_c->ch_type) {
		fprintf(fp, "%-d\t", m_param_ref_c->num_fixed_err);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_VSCR);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_NSCR);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_NWCR);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_VWCR);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_VSER);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_NSER);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_NWER);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_VWER);
	}
	fprintf(fp, "%.0f\t", tot_rn);
	fprintf(fp, "%.0f\t", tot_fr[FER_num - 1]);
	fprintf(fp, "%3.3f\t", avg_iter);
	fprintf(fp, "%d\t", (int)avg_clk);
	for (i = 0; i < FER_num; i++) {
		fprintf(fp, "%.4e\t", FER[i]);
	}
	fprintf(fp, "\n");
	fclose(fp);
	// 2nd file print (OTF)
	/*if (MODE_CH_RBER == m_param_ref_c->ch_type) {
		sprintf(filename, "MPI_S_%d_H_%d_CH_%d_E%d_init_n_%d.txt",
			m_param_ref_c->mode_scenario,
			m_ecc_info->matrix_sel, m_param_ref_c->ch_type,
			m_param_ref_c->RBER, m_param_dec->init_n);
	}
	else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) {
		sprintf(filename, "MPI_S_%d_H_%d_CH_%d_E%d_init_n_%d.txt",
			m_param_ref_c->mode_scenario,
			m_ecc_info->matrix_sel, m_param_ref_c->ch_type,
			m_param_ref_c->num_fixed_err, m_param_dec->init_n);
	)
	else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
		sprintf(filename, "MPI_S_%d_H_%d_CH_%d_E%d_SC_%.2f_SE_%.2f_init_n_%d.txt",
			m_param_ref_c->mode_scenario,
			m_ecc_info->matrix_sel, m_param_ref_c->ch_type,
			m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_SCR, m_param_ref_c->fixed_SER, m_param_dec->init_n);
	}
	else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
		sprintf(filename, "MPI_S_%d_H_%d_CH_%d_E%d_Erasure_%.2f_init_n_%d.txt",
			m_param_ref_c->mode_scenario,
			m_ecc_info->matrix_sel, m_param_ref_c->ch_type,
			m_param_ref_c->num_fixed_err, m_param_ref_c->fixed_erasure_ratio, m_param_dec->init_n);
	}
	fp = fopen(filename, "a");
	fprintf(fp, "%5d\t", seed_idx);
	if (MODE_CH_RBER == m_param_ref_c->ch_type)		fprintf(fp, "%.2e\t", m_param_ref_c->RBER);
	else if (MODE_CH_FIXED_ERROR == m_param_ref_c->ch_type) fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
	else if (MODE_CH_STRONG_ERROR == m_param_ref_c->ch_type) {
		fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
		fprintf(fp, "%.2f\t", m_param_ref_c->fixed_SCR);
		fprintf(fp, "%.2f\t", m_param_ref_c->fixed_SER);
	}
	else if (MODE_CH_ERASURE == m_param_ref_c->ch_type) {
		fprintf(fp, "%5d\t", m_param_ref_c->num_fixed_err);
		fprintf(fp, "%.2f\t", m_param_ref_c->fixed_erasure_ratio);
	}
	else if (MODE_CH_3SD_FIXED == m_param_ref_c->ch_type) {
		fprintf(fp, "%-d\t", m_param_ref_c->num_fixed_err);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_VSCR);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_NSCR);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_NWCR);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_VWCR);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_VSER);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_NSER);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_NWER);
		fprintf(fp, "%.3f\t", m_param_ref_c->fixed_VWER);
	}
	fprintf(fp, "%.0f\t", tot_rn);
	fprintf(fp, "%.0f\t", tot_fr[FER_num - 1]);
	fprintf(fp, "%3.3f\t", avg_iter);
	fprintf(fp, "%d\t", (int)avg_clk);
	for (i = 0; i < FER_num; i++) {
		fprintf(fp, "%.4e\t", FER[i]);
	}
	fprintf(fp, "\n");
	fclose(fp);
	*/
}
fp = NULL;
delete[] FER;
FER = NULL;
}
//=============================================
// MPI결과 수집결과를 합쳐서 root에서 결과를 출력하는
// 함수임에도.
//=============================================
        else if (n >= m_ecc_info->bit_pos.parity_punc_start && n < m_ecc_info->bit_pos.parity_punc_end) {
            HV_input[n] = default_value;
        }
    }
}
//=============================================
// e-mail xxxxxxxxx xxxxxxx xxxxxxx xxxx xxxx xxx
// 1) xxxxxxxPKxxx XOR25 Seedxx xoxx xxxxx xxx
// 2) IPTGxxxxx xxxxxx TV xxxxxxx
//     Decoder inputxx xox xxxxx xxx
//=============================================
void ECC_Top::Load_ECC_Input(FILE* fp, char * filename)
{
    int num = 0;
    int len_noPS = 0;
    int * buf = NULL;
    if (MODE_SEED_LOAD_UNCOR_SEED == m_param_ref_c->mode_seed) {
        while (Read_Uncor_Seed_Format(fp)) { num++; }
    }
    else if (MODE_SEED_LOAD_UNCOR_VECTOR == m_param_ref_c->mode_seed) {
        if (MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_ref_c->mode_scenario) {
            len_noPS = m_PCM.N - (m_ecc_info->shortened_bit_info + m_ecc_info->punctured_bit_info + m_ecc_info->punctured_bit_parity);
        }
        buf = new int[len_noPS];
        while (Read_Uncor_Vector_Format(len_noPS, fp, buf)) { num++; }
        delete[] buf;
        if (MODE_DEC_2SD == m_param_dec->init_n) {
            num = num / 2;
        }
        else if (MODE_DEC_3SD == m_param_dec->init_n) {
            num = num / 3;
        }
        else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
            num = num / 2;
        }
    }
#ifdef __AUTO_LLR_OPT__
    else if (MODE_SEED_LOAD_UNCOR_SEED_SAVE_UNCOR_SEED == m_param_ref_c->mode_seed) {
        while (Read_Uncor_Seed_Format(fp)) { num++; }
    }
#endif
#ifdef __AUTO_LLR_OPT__
    if (m_my_rank == ID_ROOT) {
        char fn_auto_result[LEN_FILENAME];
        sprintf(fn_auto_result, "Ref_C_result_%d.txt", m_param_ref_c->mode_init_seed);
        FILE* fp_auto_result = fopen(fn_auto_result, "a");
        fprintf(fp_auto_result, "* Number of Uncor Patterns: %d\n", num);
        fclose(fp_auto_result);
    }
#else
    if (m_my_rank == ID_ROOT) {
        printf("* Number of Uncor Patterns: %d\n", num);
    }
#endif
    fclose(fp);
    fp = fopen(filename, "rt"); // re-open
    m_param_ref_c->fn = num;
    m_param_ref_c->max_num_test = num;
}
void ECC_Top::Load_ECC_Input_TV(FILE* fp, char * filename, int * num_sector)
{
    int num = 0;
    int len_noPS = 0;
    int * buf = NULL;
    if ((MODE_TV_CASE_HD_XOR25_SEED_FIXED == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_HD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_2SD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_2SD_XOR25_SEED_STRONG_ERROR == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_3SD_XOR25_SEED_RBER == m_param_tv_gen->TS_idx) ||
        (MODE_TV_CASE_1_5SD_XOR25_SEED_ERASURE == m_param_tv_gen->TS_idx)) {
        while (Read_Uncor_Seed_Format(fp)) { num++; }
    }
    else {
        if (MODE_SCENARIO_ENC_4KB_DEC_4KB == m_param_tv_gen->mode_scenario) {
            len_noPS = m_PCM.N - (m_ecc_info->shortened_bit_info + m_ecc_info->punctured_bit_info + m_ecc_info->punctured_bit_parity);
        }
        buf = new int[len_noPS];
        while (Read_Uncor_Vector_Format(len_noPS, fp, buf)) { num++; }
        delete[] buf;
        if (MODE_DEC_2SD == m_param_dec->init_n) {
            num = num / 2;
        }
        else if (MODE_DEC_3SD == m_param_dec->init_n) {
            num = num / 3;
        }
        else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
            num = num / 2;
        }
    }
    if (m_my_rank == ID_ROOT) {
        printf("* Number of Uncor Patterns: %d\n", num);
    }
    fclose(fp);
    fp = fopen(filename, "rt"); // re-open
    *num_sector = num;
}
//=============================================
// Layoutxx xxx typexx bit xxxxx xxxxxxxx.
//=============================================
void ECC_Top::Set_Bit_Pos()
{
    int N;
    int M;
    N = m_PCM.N;
    M = m_PCM.M;
#if defined(__RUN_PREPROCESSING__)
    m_ecc_info->bit_pos.info_no_punc_start = 0;
    m_ecc_info->bit_pos.info_no_punc_end = N - M - (BCH_PAR_BLK_NUM * 256) - m_ecc_info->shortened_bit_info - m_ecc_info->punctured_bit_info;    // (N - M) - 32B - 4B - 59.5B
    /****************************************/
    m_ecc_info->bit_pos.info_sh_start = m_ecc_info->bit_pos.info_no_punc_end;
    m_ecc_info->bit_pos.info_sh_end = m_ecc_info->bit_pos.info_sh_start + m_ecc_info->shortened_bit_info;	// (N - M) - 32B - 4B - 59.5B
    /****************************************/
    m_ecc_info->bit_pos.info_punc_start = m_ecc_info->bit_pos.info_sh_end;	// (N - M) - 32B - 59.5B
    m_ecc_info->bit_pos.info_punc_end = m_ecc_info->bit_pos.info_punc_start + m_ecc_info->punctured_bit_info;	// (N - M) - 32B
    /****************************************/
    m_ecc_info->bit_pos.info_start = 0;	// 0
    m_ecc_info->bit_pos.info_end = N - M - m_ecc_info->shortened_bit_info_offset_end;	// (N - M) - (10B + 12B)
    /****************************************/
    m_ecc_info->bit_pos.scn_no_sh_start = m_ecc_info->bit_pos.info_punc_end;	// (N - M) - 32B
    m_ecc_info->bit_pos.scn_no_sh_end = m_ecc_info->bit_pos.scn_no_sh_start + BCH_TOT_PAR_LEN;	// (N - M) - 32B + 31.5B
    /****************************************/
    m_ecc_info->bit_pos.scn_sh_start = m_ecc_info->bit_pos.scn_no_sh_end;	// (N - M) - 32B + 31.5B
    m_ecc_info->bit_pos.scn_sh_end = N - M;	// (N - M)
    /****************************************/
    m_ecc_info->bit_pos.parity_no_punc_start = N - M;	// (N - M)
    m_ecc_info->bit_pos.parity_no_punc_end = N - m_ecc_info->punctured_bit_parity;	// N
    /****************************************/
    m_ecc_info->bit_pos.parity_punc_start = m_ecc_info->bit_pos.parity_no_punc_end;	// N
    m_ecc_info->bit_pos.parity_punc_end = N;	// N
    /****************************************/
    m_ecc_info->bit_pos.xcp_no_punc_start = N;	// N
    m_ecc_info->bit_pos.xcp_no_punc_end = N - m_ecc_info->punctured_bit_XCP;	// N
    /****************************************/
    m_ecc_info->bit_pos.xcp_punc_start = N - m_ecc_info->punctured_bit_XCP;	// N
    m_ecc_info->bit_pos.xcp_punc_end = N;	// N
#else
    ///////////////////////////////////////////////////////////////////////////
    /*
    // Col Blk 0, 1 Puncturingxx
    m_ecc_info->bit_pos.info_sh_start = 0;	// 0
    m_ecc_info->bit_pos.info_sh_end = m_ecc_info->shortened_bit_info;	// 4B
    m_ecc_info->bit_pos.info_punc_start = m_ecc_info->bit_pos.info_sh_end;	// 4B
    m_ecc_info->bit_pos.info_punc_end = m_ecc_info->bit_pos.info_punc_start + m_ecc_info->punctured_bit_info;	// 4B + 47B
    m_ecc_info->bit_pos.info_no_punc_start = m_ecc_info->bit_pos.info_punc_end;	// 4B + 47B
    m_ecc_info->bit_pos.info_no_punc_end = N - M;	// (N - M)
    m_ecc_info->bit_pos.info_end = N - M - m_ecc_info->shortened_bit_info_offset_end;	// (N - M) - 10B
    m_ecc_info->bit_pos.parity_no_punc_start = N - M;	// (N - M)
    m_ecc_info->bit_pos.parity_no_punc_end = N - m_ecc_info->punctured_bit_parity;	// N
    m_ecc_info->bit_pos.parity_punc_start = m_ecc_info->bit_pos.parity_no_punc_end;	// N
    m_ecc_info->bit_pos.parity_punc_end = N;	// N
    */
    ///////////////////////////////////////////////////////////////////////////
    ///////////////////////////////////////////////////////////////////////////
    // Col Blk 127, 128 Puncturingxx
    ///////////////////////////////////////////////////////////////////////////
    m_ecc_info->bit_pos.info_no_punc_start = 0;	// 0
    m_ecc_info->bit_pos.info_no_punc_end = N - M - m_ecc_info->shortened_bit_info - m_ecc_info->punctured_bit_info;	// (N - M) - 4B - 60B
    m_ecc_info->bit_pos.info_punc_start1 = m_ecc_info->bit_pos.info_no_punc_end;	// (N - M) - 4B - 60B
    m_ecc_info->bit_pos.info_punc_end1 = m_ecc_info->bit_pos.info_punc_start1 + PUNCTURED_BIT_PRIME_INFO_4KB_SEPERATE;	// (N - M) - 4B - 10B
    m_ecc_info->bit_pos.info_sh_start = m_ecc_info->bit_pos.info_punc_end1;	// (N - M) - 4B - 10B
    m_ecc_info->bit_pos.info_sh_end = m_ecc_info->bit_pos.info_sh_start + m_ecc_info->shortened_bit_info;	// (N - M) - 10B
    m_ecc_info->bit_pos.info_punc_start2 = m_ecc_info->bit_pos.info_sh_end;	// (N - M) - 10B
    m_ecc_info->bit_pos.info_punc_end2 = m_ecc_info->bit_pos.info_punc_start2 + (m_ecc_info->punctured_bit_info - PUNCTURED_BIT_PRIME_INFO_4KB_SEPERATE);	// (N - M)
    m_ecc_info->bit_pos.info_end = N - M - m_ecc_info->shortened_bit_info_offset_end;	// (N - M) - 10B
    m_ecc_info->bit_pos.parity_no_punc_start = N - M;	// (N - M)
    m_ecc_info->bit_pos.parity_no_punc_end = N - m_ecc_info->punctured_bit_parity;	// N
    m_ecc_info->bit_pos.parity_punc_start = m_ecc_info->bit_pos.parity_no_punc_end;	// N
    m_ecc_info->bit_pos.parity_punc_end = N;	// N
    ///////////////////////////////////////////////////////////////////////////
#endif // defined(__RUN_PREPROCESSING__)
}
//=============================================
// 4KB xxx shorteningxx puncturingxx xxxxxxx
// NANDxx xxxxxxx xxxxxxx channelxx xxxxx.
//=============================================
void ECC_Top::Set_Real_Err_Pos_4KB(int err_pos_num)
{
    int n;
    int tmp_pos;
    for (n = 0; n < err_pos_num; n++) {
        tmp_pos = m_err_position_noPS[n];
        if (tmp_pos >= m_ecc_info->bit_pos.info_punc_start1) {
            tmp_pos = tmp_pos + PUNCTURED_BIT_PRIME_INFO_4KB_SEPERATE;
            if (tmp_pos >= m_ecc_info->bit_pos.info_sh_start) {
                tmp_pos = tmp_pos + m_ecc_info->shortened_bit_info;
                if (tmp_pos >= m_ecc_info->bit_pos.info_punc_start2) {
                    tmp_pos = tmp_pos + (m_ecc_info->punctured_bit_info - PUNCTURED_BIT_PRIME_INFO_4KB_SEPERATE);
                    if (tmp_pos >= m_ecc_info->bit_pos.parity_punc_start) {
                        tmp_pos = tmp_pos + m_ecc_info->punctured_bit_parity;
                    }
                }
            }
        }
        m_err_position[n] = tmp_pos;
    }
    /*
    for (n = 0; n < err_pos_num; n++) {
        tmp_pos = m_err_position_noPS[n];
        if (tmp_pos >= m_ecc_info->bit_pos.info_sh_start) {
            tmp_pos = tmp_pos + m_ecc_info->shortened_bit_info;
            if (tmp_pos >= m_ecc_info->bit_pos.info_punc_start) {
                tmp_pos = tmp_pos + m_ecc_info->punctured_bit_info;
                if (tmp_pos >= m_ecc_info->bit_pos.parity_punc_start) {
                    tmp_pos = tmp_pos + m_ecc_info->punctured_bit_parity;
                }
            }
        }
        m_err_position[n] = tmp_pos;
    }*/
}
void ECC_Top::Init_Log_Data()
{
    int MN = m_param_dec->MN[m_param_dec->MN_num - 1] + 2;
    int N_b = m_PCM.N_b;
    int M_b = m_PCM.M_b;
    int size_histogram = m_param_dec->MN[m_param_dec->MN_num - 1] * 4;
    for (int i = 0; i < MN; i++) {
        for (int j = 0; j < N_b; j++) {
            m_log_bit_err_column_tot[i][j] = 0;
        }
        for (int j = 0; j < M_b; j++) {
            m_log_min1_tot[i][j] = 0;
        }
        m_log_checksum_weight_tot[i] = 0;
    }
    for (int i = 0; i < size_histogram; i++) {
        m_log_iter_histogram_tot[i] = 0;
    }
}
void ECC_Top::Alloc_Log_Data()
{
    int MN = m_param_dec->MN[m_param_dec->MN_num - 1] + 2;
    int N_b = m_PCM.N_b;
    int M_b = m_PCM.M_b;
    int size_histogram = m_param_dec->MN[m_param_dec->MN_num - 1] * 4;
    m_log_bit_err_column_tot = new int*[MN];
    m_log_min1_tot = new int*[MN];
    m_log_checksum_weight_tot = new int[MN];
    m_log_iter_histogram_tot = new int[size_histogram];
    for (int i = 0; i < MN; i++) {
        m_log_bit_err_column_tot[i] = new int[N_b];
        m_log_min1_tot[i] = new int[M_b];
    }
    Init_Log_Data();
    m_tested_num = 0;
}
void ECC_Top::Release_Log_Data()
{
    int MN = m_param_dec->MN[m_param_dec->MN_num - 1] + 2;
    for (int i = 0; i < MN; i++) {
        delete[] m_log_bit_err_column_tot[i];
        delete[] m_log_min1_tot[i];
    }
    delete[] m_log_bit_err_column_tot;
    delete[] m_log_min1_tot;
    delete[] m_log_checksum_weight_tot;
    delete[] m_log_iter_histogram_tot;
}
void ECC_Top::Update_Log_Data()
{
#if defined (__PRINT_LOG_DATA__)
    int ** sector_log_bit_err_col = m_dec.Get_Log_Bit_Err_Col();
    int ** sector_log_min1 = m_dec.Get_Log_Min1();
    int * sector_log_checksum_weight = m_dec.Get_Log_Checksum_Weight();
    int MN = m_param_dec->MN[m_param_dec->MN_num - 1] + 1;
    int N_b = m_PCM.N_b;
    int M_b = m_PCM.M_b;
    for (int i = 0; i < MN; i++) {
        for (int j = 0; j < N_b; j++) {
            m_log_bit_err_column_tot[i][j] += sector_log_bit_err_col[i][j];
        }
        for (int j = 0; j < M_b; j++) {
            m_log_min1_tot[i][j] += sector_log_min1[i][j];
        }
        m_log_checksum_weight_tot[i] += sector_log_checksum_weight[i];
    }
    m_tested_num++;
#endif
}
void ECC_Top::Update_Log_Iter_Histogram(int iter, int pcrc)
{
#if defined (__PRINT_LOG_DATA__)
    int idx = (iter - 1) * 4 + pcrc;
    m_log_iter_histogram_tot[idx]++;
#endif
}
void ECC_Top::Print_Log_Data()
{
#if defined (__PRINT_LOG_DATA__)
    int MN = m_param_dec->MN[m_param_dec->MN_num - 1] + 2;
    int N_b = m_PCM.N_b;
    int M_b = m_PCM.M_b;
    int z_sb = m_PCM.z_sb;
    int size_histogram = m_param_dec->MN[m_param_dec->MN_num - 1] * 4;
    FILE * fp_ber_col = fopen("log_ber_col.dat", "w");
    FILE * fp_min = fopen("log_min.dat", "w");
    FILE * fp_csw = fopen("log_csw2.dat", "w");
    FILE * fp_iter_histogram = fopen("log_iter_histogram.dat", "w");
    double tmp;
    for (int i = 0; i < MN; i++) {
        fprintf(fp_ber_col, "%d\t", i);
        for (int j = 0; j < N_b; j++) {
            tmp = (double)m_log_bit_err_column_tot[i][j] / m_tested_num;
            tmp = tmp / z_sb;
            fprintf(fp_ber_col, "%.3e\t", tmp);
        }
        fprintf(fp_ber_col, "\n");
        fprintf(fp_min, "%d\t", i);
        for (int j = 0; j < M_b; j++) {
            tmp = (double)m_log_min1_tot[i][j] / m_tested_num;
            tmp = tmp / z_sb;
            fprintf(fp_min, "%.3e\t", tmp);
        }
        fprintf(fp_min, "\n");
        tmp = (double)m_log_checksum_weight_tot[i] / m_tested_num;
        fprintf(fp_csw, "%d\t%.3e\n", i, tmp);
    }
    for (int i = 0; i < size_histogram; i++) {
        fprintf(fp_iter_histogram, "%d\t", m_log_iter_histogram_tot[i]);
    }
    fclose(fp_ber_col);
    fclose(fp_min);
    fclose(fp_csw);
    fclose(fp_iter_histogram);
#endif
}
void ECC_Top::Open_Log_Files()
{
#if defined (__LOG_DECODING_STATUS__)
    FILE * fp;
    fp = fopen("log_bit_err_column.dat", "w");	fclose(fp);
    fp = fopen("log_bit_err.dat", "w");	fclose(fp);
    fp = fopen("log_SW.dat", "w");	fclose(fp);
    fp = fopen("log_CSW.dat", "w");	fclose(fp);
    //fp = fopen("log_min1_sum.dat", "w");	fclose(fp);
    //fp = fopen("log_min2_sum.dat", "w");	fclose(fp);
    fp = fopen("log_punc.dat", "w");	fclose(fp);
    fp = fopen("log_LLR_idx.dat", "w");	fclose(fp);
#endif
}
void ECC_Top::Load_Dec_Input_Vector_Format(int N, int len_noPS)
{
    // 해당 모드에서 프레임당 호출 — 버퍼는 최초 1회 할당 후 재사용 (길이가 늘면 재할당)
    static int * tmp_buf_HD = NULL;
    static int * tmp_buf_SD = NULL;
    static int * tmp_buf_CC = NULL;
    static int * tmp_buf_CD = NULL;
    static int tmp_buf_len = 0;
    if (tmp_buf_len < len_noPS) {
        delete[] tmp_buf_HD; delete[] tmp_buf_SD; delete[] tmp_buf_CC; delete[] tmp_buf_CD;
        tmp_buf_HD = new int[len_noPS];
        tmp_buf_SD = new int[len_noPS];
        tmp_buf_CC = new int[len_noPS];
        tmp_buf_CD = new int[len_noPS];
        tmp_buf_len = len_noPS;
    }
    int bit_pos;
    int bCopy;
    /* init */
    for (int n = 0; n < N; n++) {
        m_HD_channel[n] = 1;
        m_SD_channel[n] = 1;
        m_CC_channel[n] = 1;
        m_CD_channel[n] = 1;
    }
    if (MODE_DEC_HD == m_param_dec->init_n) {
        Read_Uncor_Vector_Format(len_noPS, fp_uncor_seed, tmp_buf_HD);
    }
    else if (MODE_DEC_2SD == m_param_dec->init_n) {
        Read_Uncor_Vector_Format(len_noPS, fp_uncor_seed, tmp_buf_HD);
        Read_Uncor_Vector_Format(len_noPS, fp_uncor_seed, tmp_buf_SD);
    }
    else if (MODE_DEC_3SD == m_param_dec->init_n) {
        Read_Uncor_Vector_Format(len_noPS, fp_uncor_seed, tmp_buf_HD);
        Read_Uncor_Vector_Format(len_noPS, fp_uncor_seed, tmp_buf_SD);
        Read_Uncor_Vector_Format(len_noPS, fp_uncor_seed, tmp_buf_CC);
    }
    else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
        Read_Uncor_Vector_Format(len_noPS, fp_uncor_seed, tmp_buf_HD);
        Read_Uncor_Vector_Format(len_noPS, fp_uncor_seed, tmp_buf_CD);
    }
    /* shortened, punctured bits */
    bit_pos = 0;
    for (int t = 0; t < N; t++) {
        bCopy = FALSE;
        if (t >= m_ecc_info->bit_pos.info_sh_start && t < m_ecc_info->bit_pos.info_sh_end) {
            Intentional_Blank();
        }
        else if (t >= m_ecc_info->bit_pos.info_punc_start1 && t < m_ecc_info->bit_pos.info_punc_end1) {
            Intentional_Blank();
        }
        else if (t >= m_ecc_info->bit_pos.info_punc_start2 && t < m_ecc_info->bit_pos.info_punc_end2) {
            Intentional_Blank();
        }
        else {
            bCopy = TRUE;
        }
        if (TRUE == bCopy) {
            m_HD_channel[t] = tmp_buf_HD[bit_pos];
            m_SD_channel[t] = tmp_buf_SD[bit_pos];
            m_CC_channel[t] = tmp_buf_CC[bit_pos];
            m_CD_channel[t] = tmp_buf_CD[bit_pos];
            bit_pos++;
        }
    }
}
void ECC_Top::Set_Corner_Checker()
{
#if defined(__CORNER_CHECKER__)
    m_corner_checker.Set_Param(m_ecc_info, m_param_dec, m_param_ref_c->mode_scenario);
    m_corner_checker_total.Set_Param(m_ecc_info, m_param_dec, m_param_ref_c->mode_scenario);
#endif
}
void ECC_Top::Print_Corner_Checker_Total()
{
#if defined (__CORNER_CHECKER__)
    char buf[LEN_FILENAME];
#ifndef __RUN_MPI__
    sprintf(buf, "merge.txt");
#else
    sprintf(buf, "merge_%d.txt", m_my_rank);
#endif
    m_corner_checker_total.Open_File(buf);
    m_corner_checker_total.Print_Head(FALSE);
    m_corner_checker_total.Print(FALSE, filename_uncor_seed);
    m_corner_checker_total.Close_File();
#endif
}
#if defined (__CORNER_CHECKER__)
int ECC_Top::Update_Corner_Checker_Total()
{
    int first = 0;
    char buf[LEN_FILENAME];
    int flag_update_corner_checker = 0;
    /* sector xxxxxxx xxxxxxxx xxxxx xxx xx oxx x x */
    // xx oxx xxxx
//  if (MODE_SEED_LOAD_UNCOR_SEED == m_param_ref_c->mode_seed) {
//      sprintf(buf, "sector_%s.txt", filename_uncor_seed);
//  }
//  else {
//      sprintf(buf, "sector.txt");
//  }
//
//#if defined (__RUN_MPI__)
//  sprintf(buf, "%d.txt", m_my_rank);
//#endif
//
//  first = m_corner_checker.Open_File(buf);
//  if (first == TRUE) {
//      m_corner_checker.Print_Head(TRUE);
//  }
//  m_corner_checker.Print(TRUE, NULL);
//  m_corner_checker.Close_File();
    // xx oxx xx
    flag_update_corner_checker = m_corner_checker_total.Update(&m_corner_checker);
    return flag_update_corner_checker;
}
#endif
void ECC_Top::Clear_Corner_Checker()
{
#if defined (__CORNER_CHECKER__)
    m_corner_checker.Clear(FALSE);
#endif
}
void ECC_Top::Load_Msg_Vector(FILE * fp, int *msg, int msglen)
{
    Read_Uncor_Vector_Format(msglen, fp, msg);
}
