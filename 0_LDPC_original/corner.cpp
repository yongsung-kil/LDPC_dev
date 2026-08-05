#include "Corner.h"
CornerChecker::CornerChecker()
{
    m_input = NULL;
    m_dec_i = NULL;
    m_result = NULL;
    m_flag = NULL;
    m_llr = NULL;
    m_power_stopping_col_idx = NULL;
}
CornerChecker::~CornerChecker()
{
    if (m_input != NULL) {
        delete[] m_input;
        delete[] m_dec_i;
        delete[] m_result;
        delete[] m_flag;
        delete[] m_llr;
        delete[] m_power_stopping_col_idx;
    }
}
void CornerChecker::Init() {
    /*
    NOTE: LLR table ????????? ???????? ???'???
    */
    //220103
    if (m_ecc_info->matrix_sel == LAYOUT_PRIME_512B_TLC_VSS_OFF) { // QLC ?? LLR set ???? 22.01.01 ?a?)
        if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
            //IDX_LLR_LEN = PRIME_HD_LLR_TABLE_IDX_ITER_101_120_F;
        }
        else if (MODE_DEC_2SD == m_param_dec->init_n) {
            //IDX_LLR_LEN = PRIME_2SD_LLR_TABLE_IDX_ITER_302_401_D;
        }
        else if (MODE_DEC_3SD == m_param_dec->init_n) {
            //IDX_LLR_LEN = PRIME_3SD_LLR_TABLE_IDX_ITER_758_857_D;
        }
        IDX_LLR_LEN = IDX_LLR_LEN + 1;
        IDX_POWER_STOPPING_COL_IDX_LEN = PCRC_TERMINATION_POINT_PRIME_512B_4 + 1;
        if (m_input == NULL) {
            m_input = new int[IDX_I_LEN];
            m_dec_i = new int[IDX_DEC_I_LEN];
            m_result = new int[IDX_RESULT_LEN];
            m_flag = new int[IDX_FLAG_LEN];
            m_llr = new int[IDX_LLR_LEN];
            m_power_stopping_col_idx = new int[IDX_POWER_STOPPING_COL_IDX_LEN];
        }
    }
}
void CornerChecker::Set_Param(ECC_INFO* ecc_info, PARAM_DEC* param, int scenario)
{
    m_ecc_info = ecc_info;
    m_param_dec = param;
    m_scenario = scenario;
    Init();
    Clear(TRUE);
    Set_Parameters();
}
void CornerChecker::Clear(int all)
{
    if (all == TRUE) {
        for (int i = 0; i < IDX_I_LEN; i++) {
            m_input[i] = 0;
        }
        for (int i = 0; i < IDX_DEC_I_LEN; i++) {
            m_dec_i[i] = 0;
        }
    }
    for (int i = 0; i < IDX_RESULT_LEN; i++) {
        m_result[i] = 0;
    }
    for (int i = 0; i < IDX_FLAG_LEN; i++) {
        m_flag[i] = FLAG_LOW;
    }
    for (int i = 0; i < IDX_LLR_LEN; i++) {
        m_llr[i] = FLAG_LOW;
    }
    for (int i = 0; i < IDX_POWER_STOPPING_COL_IDX_LEN; i++) {
        m_power_stopping_col_idx[i] = FLAG_LOW;
    }
}
void CornerChecker::Set_Parameters()
{
    m_input[IDX_I_CODE_RATE] = m_ecc_info->matrix_sel;
#if defined( __12META__)
    m_input[IDX_I_META] = 12;
#else
    m_input[IDX_I_META] = 16;
#endif
    if (MODE_ALL_ONE_CODEWORD == m_ecc_info->mode_all_one_cw) {
        m_input[IDX_I_MSG_INVERT] = 0;
    }
    else {
        m_input[IDX_I_MSG_INVERT] = 1;
    }
    /********************************************/
    if (MODE_SCENARIO_ENC_4KB_DEC_4KB == m_scenario) {
        m_dec_i[IDX_DEC_I_PRIME_MODE] = 0;
    }
    else {
        m_dec_i[IDX_DEC_I_PRIME_MODE] = 1;
    }
    m_dec_i[IDX_DEC_I_DEC_MODE] = m_param_dec->init_n;
    m_dec_i[IDX_DEC_I_MAX_ITR] = m_param_dec->MN[m_param_dec->MN_num - 1];
    if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
        m_dec_i[IDX_DEC_I_HD_STOP_IDX] = m_param_dec->diverse_th;
        m_dec_i[IDX_DEC_I_SD_STOP_IDX] = 0;
    }
    else {
        m_dec_i[IDX_DEC_I_HD_STOP_IDX] = 0;
        m_dec_i[IDX_DEC_I_SD_STOP_IDX] = m_param_dec->diverse_th;
    }
    if (MODE_CRC_PARTIAL == m_param_dec->CRC_Option_F_P) {
        m_dec_i[IDX_DEC_I_CRC_SEL] = 0;
    }
    else if ((MODE_CRC_PARTIAL_LAST_ONLY == m_param_dec->CRC_Option_F_P) || (MODE_CRC_FULL == m_param_dec->CRC_Option_F_P)) {
        m_dec_i[IDX_DEC_I_CRC_SEL] = 1;
    }
}
void CornerChecker::Event_Flag(int index)
{
    if (m_flag != NULL) {
        if (FLAG_LOW == m_flag[index]) {
            m_flag[index] = FLAG_HIGH;
        }
    }
}
void CornerChecker::Event_LLR(int index)
{
    if (m_llr != NULL) {
        if (FLAG_LOW == m_llr[index]) {
            m_llr[index] = FLAG_HIGH;
        }
    }
}
void CornerChecker::Event_Power_Stopping(int index)
{
    if (m_power_stopping_col_idx != NULL) {
        if (FLAG_LOW == m_power_stopping_col_idx[index]) {
            m_power_stopping_col_idx[index] = FLAG_HIGH;
        }
    }
}
void CornerChecker::Event_Result(int uncor, int itr, int err_cnt)
{
    if (m_result != NULL) {
        m_result[IDX_RESULT_UNCOR] = uncor;
        m_result[IDX_RESULT_ITERATION] = itr;
        m_result[IDX_RESULT_ERR_CNT] = err_cnt;
    }
}
void CornerChecker::Print_Head(int all)
{
    if (all == FALSE) {
        fprintf(m_fp, "FILENAME\t");
    }
    fprintf(m_fp, "IDX_I_CODE_RATE\t");
    fprintf(m_fp, "IDX_I_META\t");
    fprintf(m_fp, "IDX_I_MSG_INVERT\t");
    fprintf(m_fp, "IDX_DEC_I_PRIME_MODE\t");
    fprintf(m_fp, "IDX_DEC_I_DEC_MODE\t");
    fprintf(m_fp, "IDX_DEC_I_MAX_ITR\t");
    fprintf(m_fp, "IDX_DEC_I_HD_STOP_IDX\t");
    fprintf(m_fp, "IDX_DEC_I_SD_STOP_IDX\t");
    fprintf(m_fp, "IDX_DEC_I_CRC_SEL\t");
    fprintf(m_fp, "IDX_FLAG_POWER_STOPPING\t");
    fprintf(m_fp, "IDX_FLAG_JUMP\t");
    fprintf(m_fp, "IDX_FLAG_IDLE_CYCLE\t");
    fprintf(m_fp, "IDX_FLAG_PCRC_POINT_0\t");
    fprintf(m_fp, "IDX_FLAG_PCRC_POINT_1\t");
    fprintf(m_fp, "IDX_FLAG_PCRC_POINT_2\t");
    fprintf(m_fp, "IDX_FLAG_PCRC_POINT_3\t");
    fprintf(m_fp, "IDX_FLAG_FULL_CRC\t");
    fprintf(m_fp, "IDX_FLAG_HBF_ON\t");
    fprintf(m_fp, "IDX_FLAG_HD_5_8_SET_TYPE_0\t");
    fprintf(m_fp, "IDX_FLAG_HD_5_8_SET_TYPE_1\t");
    fprintf(m_fp, "IDX_FLAG_HD_5_8_SET_TYPE_2\t");
    fprintf(m_fp, "IDX_FLAG_HD_FLOOR_TYPE_0\t");
    fprintf(m_fp, "IDX_FLAG_HD_FLOOR_TYPE_1\t");
    fprintf(m_fp, "IDX_FLAG_HD_FLOOR_TYPE_2\t");
    fprintf(m_fp, "IDX_FLAG_HD_FLOOR_TYPE_3\t");
    for (int i = 0; i < IDX_LLR_LEN; i++) {
        fprintf(m_fp, "IDX_LLR_%2d\t", (i + 1));
    }
    for (int i = 0; i < IDX_POWER_STOPPING_COL_IDX_LEN; i++) {
        fprintf(m_fp, "IDX_POWER_COL_%3d\t", i);
    }
    if (all == TRUE) {
        fprintf(m_fp, "IDX_RESULT_UNCOR\t");
        fprintf(m_fp, "IDX_RESULT_ITERATION\t");
        fprintf(m_fp, "IDX_RESULT_ERR_CNT\t");
    }
    fprintf(m_fp, "\n");
}
void CornerChecker::Print(int all, char* buf)
{
    if (all == FALSE) {
        fprintf(m_fp, "%s\t", buf);
    }
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_input[IDX_I_CODE_RATE]) {
        fprintf(m_fp, "TLC_512B_VSS_OFF\t");
    }
    fprintf(m_fp, "%dB\t", m_input[IDX_I_META]);
    fprintf(m_fp, "%d\t", m_input[IDX_I_MSG_INVERT]);
    if (0 == m_dec_i[IDX_DEC_I_PRIME_MODE]) {
        fprintf(m_fp, "NORMAL\t");
    }
    else {
        fprintf(m_fp, "PRIME\t");
    }
    if (MODE_DEC_HD == m_dec_i[IDX_DEC_I_DEC_MODE]) {
        fprintf(m_fp, "HD\t");
    }
    else if (MODE_DEC_2SD == m_dec_i[IDX_DEC_I_DEC_MODE]) {
        fprintf(m_fp, "2SD\t");
    }
    else if (MODE_DEC_3SD == m_dec_i[IDX_DEC_I_DEC_MODE]) {
        fprintf(m_fp, "3SD\t");
    }
    else if (MODE_DEC_1_5SD == m_dec_i[IDX_DEC_I_DEC_MODE]) {
        fprintf(m_fp, "1_5SD\t");
    }
    for (int i = IDX_DEC_I_MAX_ITR; i < IDX_DEC_I_LEN; i++) {
        fprintf(m_fp, "%d\t", m_dec_i[i]);
    }
    for (int i = 0; i < IDX_FLAG_LEN; i++) {
        fprintf(m_fp, "%d\t", m_flag[i]);
    }
    for (int i = 0; i < IDX_LLR_LEN; i++) {
        fprintf(m_fp, "%d\t", m_llr[i]);
    }
    for (int i = 0; i < IDX_POWER_STOPPING_COL_IDX_LEN; i++) {
        fprintf(m_fp, "%d\t", m_power_stopping_col_idx[i]);
    }
    if (all == TRUE) {
        for (int i = 0; i < IDX_RESULT_LEN; i++) {
            fprintf(m_fp, "%d\t", m_result[i]);
        }
    }
    fprintf(m_fp, "\n");
}
int CornerChecker::Open_File(char* buf)
{
    int first = FALSE;
    char filename[LEN_FILENAME];
    sprintf(filename, "corner_%s", buf);
    FILE* fp_temp = NULL;
    fp_temp = fopen(filename, "rt");
    if (fp_temp == NULL) {
        m_fp = fopen(filename, "wt");
        first = TRUE;
    }
    else {
        // exist
        fclose(fp_temp);
        m_fp = fopen(filename, "at+");
    }
    return first;
}
void CornerChecker::Close_File()
{
    if (m_fp != NULL) {
        fclose(m_fp);
        m_fp = NULL;
    }
}
int CornerChecker::Update(CornerChecker* corner)
{
    m_flag_update = 0;
    for (int i = 0; i < IDX_FLAG_LEN; i++) {
        if (FLAG_LOW == m_flag[i]) {
            if (FLAG_HIGH == corner->m_flag[i]) {
                m_flag[i] = FLAG_HIGH;
                m_flag_update = 1;
            }
        }
    }
    for (int i = 0; i < IDX_LLR_LEN; i++) {
        if (FLAG_LOW == m_llr[i]) {
            if (FLAG_HIGH == corner->m_llr[i]) {
                m_llr[i] = FLAG_HIGH;
                m_flag_update = 1;
            }
        }
    }
    for (int i = 0; i < IDX_POWER_STOPPING_COL_IDX_LEN; i++) {
        if (FLAG_LOW == m_power_stopping_col_idx[i]) {
            if (FLAG_HIGH == corner->m_power_stopping_col_idx[i]) {
                m_power_stopping_col_idx[i] = FLAG_HIGH;
                m_flag_update = 1;
            }
        }
    }
    return m_flag_update;
}
