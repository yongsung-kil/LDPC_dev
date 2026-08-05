#include "TV_Dec.h"
using namespace std;
//=============================================
// ◆◆◆◆◆
//=============================================
TV_Dec::TV_Dec()
{
	m_param_dec = NULL;
	m_ecc_info = NULL;
	m_PCM = NULL;
	m_fp_in = NULL;
	m_fp_in_noPS = NULL;
	m_fp_in_2SD = NULL;
	m_fp_in_2SD_noPS = NULL;
	m_fp_in_3SD = NULL;
	m_fp_in_3SD_noPS = NULL;
	m_fp_in_COR_SGN = NULL;
	m_fp_in_COR_SGN_noPS = NULL;
	m_fp_out = NULL;
	m_fp_out_noPS = NULL;
	m_fp_out_noS = NULL;
	m_TV_idx = 0;
	m_TV_sub_idx = 0;
	//TEMP_HY
	//m_bits_per_line = TV_LINE_WIDTH_256;
	m_bits_per_line = TV_LINE_WIDTH_128;
	//m_bits_per_line = TV_LINE_WIDTH_64;
}
//=============================================
// ◆4◆◆◆
//=============================================
TV_Dec::~TV_Dec()
{
}
//=============================================
// ◆# ◆◆◆ ◆◆ decoder parameter ◆◆◆◆
//=============================================
void TV_Dec::Set_Param(ECC_INFO* ecc_info, PCM* pcm, PARAM_DEC* param)
{
	m_ecc_info = ecc_info;
	m_PCM = pcm;
	m_param_dec = param;
}
//=============================================
// TV ◆◆8 ◆◆◆◆
//=============================================
void TV_Dec::Set_TV_idx(int idx, int sub_idx)
{
	m_TV_idx = idx;
	m_TV_sub_idx = sub_idx;
}
//=============================================
// TV ◆◆◆◆ ◆/◆ ◆◆◆◆
//=============================================
void TV_Dec::Set_Filename()
{
	memset(m_str_DEC_IN_HD, LEN_FILENAME, 0);
	memset(m_str_DEC_IN_HD_noPS, LEN_FILENAME, 0);
	memset(m_str_DEC_OUT, LEN_FILENAME, 0);
	memset(m_str_DEC_OUT_noPS, LEN_FILENAME, 0);
	memset(m_str_DEC_OUT_noS, LEN_FILENAME, 0);
	memset(m_str_DECIN_2SD, LEN_FILENAME, 0);
	memset(m_str_DECIN_2SD_noPS, LEN_FILENAME, 0);
	memset(m_str_DECIN_3SD, LEN_FILENAME, 0);
	memset(m_str_DECIN_3SD_noPS, LEN_FILENAME, 0);
	memset(m_str_DECIN_CD, LEN_FILENAME, 0);
	memset(m_str_DECIN_CD_noPS, LEN_FILENAME, 0);
	memset(m_str_COR_SGN, LEN_FILENAME, 0);
	memset(m_str_COR_SGN_noPS, LEN_FILENAME, 0);
#if defined (__WIN_OS__)
	if (EMPTY == m_TV_sub_idx) {
	    sprintf(m_str_DEC_IN_HD, "output\\C_TEST%04d_DECIN_HD.dat", m_TV_idx);
	    sprintf(m_str_DEC_IN_HD_noPS, "output\\C_TEST%04d_DECIN_HD_noPS.dat", m_TV_idx);
	    sprintf(m_str_DEC_OUT, "output\\C_TEST%04d_DEC_OUT.dat", m_TV_idx);
	    sprintf(m_str_DEC_OUT_noPS, "output\\C_TEST%04d_DEC_OUT_noPS.dat", m_TV_idx);
	    sprintf(m_str_DEC_OUT_noS, "output\\C_TEST%04d_DEC_OUT_noS.dat", m_TV_idx);
	    if (MODE_DEC_2SD == m_param_dec->init_n) {
	        sprintf(m_str_DECIN_2SD, "output\\C_TEST%04d_DECIN_2SD.dat", m_TV_idx);
	        sprintf(m_str_DECIN_2SD_noPS, "output\\C_TEST%04d_DECIN_2SD_noPS.dat", m_TV_idx);
	    }
	    else if (MODE_DEC_3SD == m_param_dec->init_n) {
	        sprintf(m_str_DECIN_2SD, "output\\C_TEST%04d_DECIN_2SD.dat", m_TV_idx);
	        sprintf(m_str_DECIN_2SD_noPS, "output\\C_TEST%04d_DECIN_2SD_noPS.dat", m_TV_idx);
	        sprintf(m_str_DECIN_3SD, "output\\C_TEST%04d_DECIN_3SD.dat", m_TV_idx);
	        sprintf(m_str_DECIN_3SD_noPS, "output\\C_TEST%04d_DECIN_3SD_noPS.dat", m_TV_idx);
	    }
	    else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
	        sprintf(m_str_DECIN_CD, "output\\C_TEST%04d_DECIN_CD.dat", m_TV_idx);
	        sprintf(m_str_DECIN_CD_noPS, "output\\C_TEST%04d_DECIN_CD_noPS.dat", m_TV_idx);
	        sprintf(m_str_COR_SGN, "output\\C_TEST%04d_COR_SGN.dat", m_TV_idx);
	        sprintf(m_str_COR_SGN_noPS, "output\\C_TEST%04d_COR_SGN_noPS.dat", m_TV_idx);
	    }
	}
	else {
	    sprintf(m_str_DEC_IN_HD, "output\\C_TEST%04d_%d_DECIN_HD.dat", m_TV_idx, m_TV_sub_idx);
	    sprintf(m_str_DEC_IN_HD_noPS, "output\\C_TEST%04d_%d_DECIN_HD_noPS.dat", m_TV_idx, m_TV_sub_idx);
	    sprintf(m_str_DEC_OUT, "output\\C_TEST%04d_%d_DEC_OUT.dat", m_TV_idx, m_TV_sub_idx);
	    sprintf(m_str_DEC_OUT_noPS, "output\\C_TEST%04d_%d_DEC_OUT_noPS.dat", m_TV_idx, m_TV_sub_idx);
	    sprintf(m_str_DEC_OUT_noS, "output\\C_TEST%04d_%d_DEC_OUT_noS.dat", m_TV_idx, m_TV_sub_idx);
	    if (MODE_DEC_2SD == m_param_dec->init_n) {
	        sprintf(m_str_DECIN_2SD, "output\\C_TEST%04d_%d_DECIN_2SD.dat", m_TV_idx, m_TV_sub_idx);
	        sprintf(m_str_DECIN_2SD_noPS, "output\\C_TEST%04d_%d_DECIN_2SD_noPS.dat", m_TV_idx, m_TV_sub_idx);
	    }
	    else if (MODE_DEC_3SD == m_param_dec->init_n) {
	        sprintf(m_str_DECIN_2SD, "output\\C_TEST%04d_%d_DECIN_2SD.dat", m_TV_idx, m_TV_sub_idx);
	        sprintf(m_str_DECIN_2SD_noPS, "output\\C_TEST%04d_%d_DECIN_2SD_noPS.dat", m_TV_idx, m_TV_sub_idx);
	        sprintf(m_str_DECIN_3SD, "output\\C_TEST%04d_%d_DECIN_3SD.dat", m_TV_idx, m_TV_sub_idx);
            sprintf(m_str_DECIN_3SD_noPS, "output\\C_TEST%04d_%d_DECIN_3SD_noPS.dat", m_TV_idx, m_TV_sub_idx);
        }
        else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
            sprintf(m_str_DECIN_CD, "output\\C_TEST%04d_%d_DECIN_CD.dat", m_TV_idx, m_TV_sub_idx);
            sprintf(m_str_DECIN_CD_noPS, "output\\C_TEST%04d_%d_DECIN_CD_noPS.dat", m_TV_idx, m_TV_sub_idx);
            sprintf(m_str_COR_SGN, "output\\C_TEST%04d_%d_COR_SGN.dat", m_TV_idx, m_TV_sub_idx);
            sprintf(m_str_COR_SGN_noPS, "output\\C_TEST%04d_%d_COR_SGN_noPS.dat", m_TV_idx, m_TV_sub_idx);
        }
    }
#else
    if (EMPTY == m_TV_sub_idx) {
        sprintf(m_str_DEC_IN_HD, "./output/C_TEST%04d_DECIN_HD.dat", m_TV_idx);
        sprintf(m_str_DEC_IN_HD_noPS, "./output/C_TEST%04d_DECIN_HD_noPS.dat", m_TV_idx);
        sprintf(m_str_DEC_OUT, "./output/C_TEST%04d_DEC_OUT.dat", m_TV_idx);
        sprintf(m_str_DEC_OUT_noPS, "./output/C_TEST%04d_DEC_OUT_noPS.dat", m_TV_idx);
        sprintf(m_str_DEC_OUT_noS, "./output/C_TEST%04d_DEC_OUT_noS.dat", m_TV_idx);
        if (MODE_DEC_2SD == m_param_dec->init_n) {
            sprintf(m_str_DECIN_2SD, "./output/C_TEST%04d_DECIN_2SD.dat", m_TV_idx);
            sprintf(m_str_DECIN_2SD_noPS, "./output/C_TEST%04d_DECIN_2SD_noPS.dat", m_TV_idx);
        }
        else if (MODE_DEC_3SD == m_param_dec->init_n) {
            sprintf(m_str_DECIN_2SD, "./output/C_TEST%04d_DECIN_2SD.dat", m_TV_idx);
            sprintf(m_str_DECIN_2SD_noPS, "./output/C_TEST%04d_DECIN_2SD_noPS.dat", m_TV_idx);
            sprintf(m_str_DECIN_3SD, "./output/C_TEST%04d_DECIN_3SD.dat", m_TV_idx);
            sprintf(m_str_DECIN_3SD_noPS, "./output/C_TEST%04d_DECIN_3SD_noPS.dat", m_TV_idx);
        }
        else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
            sprintf(m_str_DECIN_CD, "./output/C_TEST%04d_DECIN_CD.dat", m_TV_idx);
            sprintf(m_str_DECIN_CD_noPS, "./output/C_TEST%04d_DECIN_CD_noPS.dat", m_TV_idx);
            sprintf(m_str_COR_SGN, "./output/C_TEST%04d_COR_SGN.dat", m_TV_idx);
            sprintf(m_str_COR_SGN_noPS, "./output/C_TEST%04d_COR_SGN_noPS.dat", m_TV_idx);
        }
    }
    else {
        sprintf(m_str_DEC_IN_HD, "./output/C_TEST%04d_%d_DECIN_HD.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(m_str_DEC_IN_HD_noPS, "./output/C_TEST%04d_%d_DECIN_HD_noPS.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(m_str_DEC_OUT, "./output/C_TEST%04d_%d_DEC_OUT.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(m_str_DEC_OUT_noPS, "./output/C_TEST%04d_%d_DEC_OUT_noPS.dat", m_TV_idx, m_TV_sub_idx);
        sprintf(m_str_DEC_OUT_noS, "./output/C_TEST%04d_%d_DEC_OUT_noS.dat", m_TV_idx, m_TV_sub_idx);
        if (MODE_DEC_2SD == m_param_dec->init_n) {
            sprintf(m_str_DECIN_2SD, "./output/C_TEST%04d_%d_DECIN_2SD.dat", m_TV_idx, m_TV_sub_idx);
            sprintf(m_str_DECIN_2SD_noPS, "./output/C_TEST%04d_%d_DECIN_2SD_noPS.dat", m_TV_idx, m_TV_sub_idx);
        }
        else if (MODE_DEC_3SD == m_param_dec->init_n) {
            sprintf(m_str_DECIN_2SD, "./output/C_TEST%04d_%d_DECIN_2SD.dat", m_TV_idx, m_TV_sub_idx);
            sprintf(m_str_DECIN_2SD_noPS, "./output/C_TEST%04d_%d_DECIN_2SD_noPS.dat", m_TV_idx, m_TV_sub_idx);
            sprintf(m_str_DECIN_3SD, "./output/C_TEST%04d_%d_DECIN_3SD.dat", m_TV_idx, m_TV_sub_idx);
            sprintf(m_str_DECIN_3SD_noPS, "./output/C_TEST%04d_%d_DECIN_3SD_noPS.dat", m_TV_idx, m_TV_sub_idx);
        }
        else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
            sprintf(m_str_DECIN_CD, "./output/C_TEST%04d_%d_DECIN_CD.dat", m_TV_idx, m_TV_sub_idx);
            sprintf(m_str_DECIN_CD_noPS, "./output/C_TEST%04d_%d_DECIN_CD_noPS.dat", m_TV_idx, m_TV_sub_idx);
            sprintf(m_str_COR_SGN, "./output/C_TEST%04d_%d_COR_SGN.dat", m_TV_idx, m_TV_sub_idx);
            sprintf(m_str_COR_SGN_noPS, "./output/C_TEST%04d_%d_COR_SGN_noPS.dat", m_TV_idx, m_TV_sub_idx);
        }
    }
#endif
}
//=============================================
// Open file stream
//=============================================
void TV_Dec::Open()
{
    Set_Filename();
    m_fp_in = fopen(m_str_DEC_IN_HD, "wt");
    m_fp_in_noPS = fopen(m_str_DEC_IN_HD_noPS, "wt");
    m_fp_out = fopen(m_str_DEC_OUT, "wt");
    m_fp_out_noPS = fopen(m_str_DEC_OUT_noPS, "wt");
    m_fp_out_noS = fopen(m_str_DEC_OUT_noS, "wt");
    if (MODE_DEC_2SD == m_param_dec->init_n) {
        m_fp_in_2SD = fopen(m_str_DECIN_2SD, "wt");
        m_fp_in_2SD_noPS = fopen(m_str_DECIN_2SD_noPS, "wt");
    }
    else if (MODE_DEC_3SD == m_param_dec->init_n) {
        m_fp_in_2SD = fopen(m_str_DECIN_2SD, "wt");
        m_fp_in_2SD_noPS = fopen(m_str_DECIN_2SD_noPS, "wt");
        m_fp_in_3SD = fopen(m_str_DECIN_3SD, "wt");
        m_fp_in_3SD_noPS = fopen(m_str_DECIN_3SD_noPS, "wt");
    }
    else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
        m_fp_in_2SD = fopen(m_str_DECIN_CD, "wt");
        m_fp_in_2SD_noPS = fopen(m_str_DECIN_CD_noPS, "wt");
        m_fp_in_COR_SGN = fopen(m_str_COR_SGN, "wt");
        m_fp_in_COR_SGN_noPS = fopen(m_str_COR_SGN_noPS, "wt");
    }
}
//=============================================
// Close file stream
//=============================================
void TV_Dec::Close()
{
    fclose(m_fp_in);
    fclose(m_fp_in_noPS);
    fclose(m_fp_out);
    fclose(m_fp_out_noPS);
    fclose(m_fp_out_noS);
    if (MODE_DEC_2SD == m_param_dec->init_n) {
        fclose(m_fp_in_2SD);
        fclose(m_fp_in_2SD_noPS);
    }
    else if (MODE_DEC_3SD == m_param_dec->init_n) {
        fclose(m_fp_in_2SD);
        fclose(m_fp_in_2SD_noPS);
        fclose(m_fp_in_3SD);
        fclose(m_fp_in_3SD_noPS);
    }
    else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
        fclose(m_fp_in_2SD);
        fclose(m_fp_in_2SD_noPS);
        fclose(m_fp_in_COR_SGN);
        fclose(m_fp_in_COR_SGN_noPS);
    }
    m_fp_in = NULL;
    m_fp_in_noPS = NULL;
    m_fp_out = NULL;
    m_fp_out_noPS = NULL;
    m_fp_out_noS = NULL;
    m_fp_in_2SD = NULL;
    m_fp_in_2SD_noPS = NULL;
    m_fp_in_3SD = NULL;
    m_fp_in_3SD_noPS = NULL;
    m_fp_in_COR_SGN = NULL;
    m_fp_in_COR_SGN_noPS = NULL;
}
//=============================================
// Decoder input ◆◆◆
//=============================================
void TV_Dec::Print_TV_Dec_In(int* i_HD_input, int* i_SD_input, int* i_CC_input, int* i_CD_input, int print_cw, int print_noPS)
{
    int i;
    int data_len;
    int pos1;
    int pos2;
    int buf_size = m_PCM->N;
    int z_sb = m_PCM->z_sb;
    int* test_vec = new int[buf_size];
    int* test_vec_noPS = new int[buf_size];
    int* test_vec_2SD = new int[buf_size];
    int* test_vec_2SD_noPS = new int[buf_size];
    int* test_vec_3SD = new int[buf_size];
    int* test_vec_3SD_noPS = new int[buf_size];
    int* test_vec_1_5SD = new int[buf_size];
    int* test_vec_1_5SD_noPS = new int[buf_size];
    int* test_vec_CD = new int[buf_size];
    int* test_vec_CD_noPS = new int[buf_size];
    Set_Array(test_vec, buf_size, 1);
    Set_Array(test_vec_noPS, buf_size, 1);
    Set_Array(test_vec_2SD, buf_size, 1);
    Set_Array(test_vec_2SD_noPS, buf_size, 1);
    Set_Array(test_vec_3SD, buf_size, 1);
    Set_Array(test_vec_3SD_noPS, buf_size, 1);
    Set_Array(test_vec_1_5SD, buf_size, 1);
    Set_Array(test_vec_1_5SD_noPS, buf_size, 1);
    Set_Array(test_vec_CD, buf_size, 1);
    Set_Array(test_vec_CD_noPS, buf_size, 1);
    pos1 = 0;
    pos2 = 0;
    for (i = 0; i < m_PCM->N; i++) {
        test_vec_CD[i] = (i_HD_input[i] + i_CD_input[i]) % 2;
    }
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) {
        data_len = m_PCM->N;
        for (i = 0; i < data_len; i++) {
            test_vec[i] = i_HD_input[i];
            test_vec_2SD[i] = i_SD_input[i];
            test_vec_3SD[i] = i_CC_input[i];
            test_vec_1_5SD[i] = i_CD_input[i];
        }
        /* No PS */
        /* LDPC information */
        data_len = (m_PCM->N - m_PCM->M) - (m_ecc_info->shortened_bit_info_offset_end + m_ecc_info->shortened_bit_info + m_ecc_info->punctured_bit_info);
        pos1 = 0;
        pos2 = m_ecc_info->shortened_bit_info + m_ecc_info->punctured_bit_info;
        for (i = 0; i < data_len; i++) {
            test_vec_noPS[pos1] = i_HD_input[pos2];
            test_vec_2SD_noPS[pos1] = i_SD_input[pos2];
            test_vec_3SD_noPS[pos1] = i_CC_input[pos2];
            test_vec_1_5SD_noPS[pos1] = i_CD_input[pos2];
            test_vec_CD_noPS[pos1] = test_vec_CD[pos2];
            pos1++;
            pos2++;
        }
        /* CRC */
        data_len = CRC_LEN; // CRC length (80)
        for (i = 0; i < data_len; i++) {
            test_vec_noPS[pos1] = i_HD_input[pos2];
            test_vec_2SD_noPS[pos1] = i_SD_input[pos2];
            test_vec_3SD_noPS[pos1] = i_CC_input[pos2];
            test_vec_1_5SD_noPS[pos1] = i_CD_input[pos2];
            test_vec_CD_noPS[pos1] = test_vec_CD[pos2];
            pos1++;
            pos2++;
        }
        /* LDPC parity no punc */
        data_len = m_PCM->M;
        for (i = 0; i < data_len; i++) {
            test_vec_noPS[pos1] = i_HD_input[pos2];
            test_vec_2SD_noPS[pos1] = i_SD_input[pos2];
            test_vec_3SD_noPS[pos1] = i_CC_input[pos2];
            test_vec_1_5SD_noPS[pos1] = i_CD_input[pos2];
            test_vec_CD_noPS[pos1] = test_vec_CD[pos2];
            pos1++;
            pos2++;
        }
    if (TRUE == print_cw) {
        data_len = m_PCM->N;
        if (MODE_DEC_HD == m_param_dec->init_n) {
            Print_Array_HEX_Fill_F(m_fp_in, test_vec, data_len, m_bits_per_line);
        }
        else if (MODE_DEC_2SD == m_param_dec->init_n) {
            Print_Array_HEX_Fill_F(m_fp_in, test_vec, data_len, m_bits_per_line);
            Print_Array_HEX_Fill_F(m_fp_in_2SD, test_vec_2SD, data_len, m_bits_per_line);
        }
        else if (MODE_DEC_3SD == m_param_dec->init_n) {
            Print_Array_HEX_Fill_F(m_fp_in, test_vec, data_len, m_bits_per_line);
            Print_Array_HEX_Fill_F(m_fp_in_2SD, test_vec_2SD, data_len, m_bits_per_line);
            Print_Array_HEX_Fill_F(m_fp_in_3SD, test_vec_3SD, data_len, m_bits_per_line);
        }
        else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
            Print_Array_HEX_Fill_F(m_fp_in, test_vec, data_len, m_bits_per_line);
            Print_Array_HEX_Fill_F(m_fp_in_2SD, test_vec_1_5SD, data_len, m_bits_per_line);
            Print_Array_HEX_Fill_F(m_fp_in_COR_SGN, test_vec_CD, data_len, m_bits_per_line);
        }
    }
    if (TRUE == print_noPS) {
        data_len = m_PCM->N - m_ecc_info->shortened_bit_info - m_ecc_info->punctured_bit_info - m_ecc_info->punctured_bit_parity;
        if (MODE_DEC_HD == m_param_dec->init_n) {
            Print_Array_HEX_Fill_F(m_fp_in_noPS, test_vec_noPS, data_len, m_bits_per_line);
        }
        else if (MODE_DEC_2SD == m_param_dec->init_n) {
            Print_Array_HEX_Fill_F(m_fp_in_noPS, test_vec_noPS, data_len, m_bits_per_line);
            Print_Array_HEX_Fill_F(m_fp_in_2SD_noPS, test_vec_2SD_noPS, data_len, m_bits_per_line);
        }
        else if (MODE_DEC_3SD == m_param_dec->init_n) {
            Print_Array_HEX_Fill_F(m_fp_in_noPS, test_vec_noPS, data_len, m_bits_per_line);
            Print_Array_HEX_Fill_F(m_fp_in_2SD_noPS, test_vec_2SD_noPS, data_len, m_bits_per_line);
            Print_Array_HEX_Fill_F(m_fp_in_3SD_noPS, test_vec_3SD_noPS, data_len, m_bits_per_line);
        }
        else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
            Print_Array_HEX_Fill_F(m_fp_in_noPS, test_vec_noPS, data_len, m_bits_per_line);
            Print_Array_HEX_Fill_F(m_fp_in_2SD_noPS, test_vec_2SD_noPS, data_len, m_bits_per_line);
            Print_Array_HEX_Fill_F(m_fp_in_COR_SGN_noPS, test_vec_CD_noPS, data_len, m_bits_per_line);
        }
    }
}
    delete[] test_vec;
    delete[] test_vec_noPS;
    delete[] test_vec_2SD;
    delete[] test_vec_2SD_noPS;
    delete[] test_vec_3SD;
    delete[] test_vec_3SD_noPS;
    delete[] test_vec_1_5SD;
    delete[] test_vec_1_5SD_noPS;
    delete[] test_vec_CD;
    delete[] test_vec_CD_noPS;
}
//=============================================
// Decoder output ◆◆◆
//=============================================
void TV_Dec::Print_TV_Dec_Out(int* cwc, int* i_HD_input, int CRC_flag, int print_cw, int print_noPS, int print_noS)
{
    int i;
    int buf_size = m_PCM->N;
    int z_sb = m_PCM->z_sb;
    int data_len;
    int pos1;
    int pos2;
    int start1, start2, start3;
    int* test_vec = new int[buf_size];
    int* test_vec_noPS = new int[buf_size];
    int* test_vec_noS = new int[buf_size];
    Set_Array(test_vec, buf_size, 1);
    Set_Array(test_vec_noPS, buf_size, 1);
    Set_Array(test_vec_noS, buf_size, 1);
    pos2 = 0;
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) {
        if (FLAG_LOW == CRC_flag) {
            //COR : print message
            /* LDPC information */
            data_len = (m_PCM->N - m_PCM->M) - (m_ecc_info->shortened_bit_info_offset_end);
            start1 = 0;
            pos1 = 0;
            for (i = start1; i < data_len; i++) {
                test_vec[pos1] = cwc[i];
                pos1++;
            }
            start2 = m_ecc_info->shortened_bit_info + m_ecc_info->punctured_bit_info;
            pos1 = 0;
            for (i = start2; i < data_len; i++) {
                test_vec_noPS[pos1] = cwc[i];
                pos1++;
            }
            start3 = m_ecc_info->shortened_bit_info;
            pos1 = 0;
            for (i = start3; i < data_len; i++) {
                test_vec_noS[pos1] = cwc[i];
                pos1++;
            }
            if (TRUE == print_cw) {
                Print_Array_HEX_Fill_F(m_fp_out, test_vec, data_len - start1, m_bits_per_line);
            }
            if (TRUE == print_noPS) {
                Print_Array_HEX_Fill_F(m_fp_out_noPS, test_vec_noPS, data_len - start2, m_bits_per_line);
            }
            if (TRUE == print_noS) {
                Print_Array_HEX_Fill_F(m_fp_out_noS, test_vec_noS, data_len - start3, m_bits_per_line);
            }
        }
        else {
            //UNCOR : print HD input
            data_len = m_PCM->N;
            for (i = 0; i < data_len; i++) {
                test_vec[i] = i_HD_input[i];
            }
            /* LDPC information */
            data_len = (m_PCM->N - m_PCM->M) - (m_ecc_info->shortened_bit_info_offset_end + m_ecc_info->shortened_bit_info + m_ecc_info->punctured_bit_info);
            pos1 = 0;
            pos2 = m_ecc_info->shortened_bit_info + m_ecc_info->punctured_bit_info;
            start2 = pos2;
            for (i = 0; i < data_len; i++) {
                test_vec_noPS[pos1] = i_HD_input[pos2];
                pos1++;
                pos2++;
            }
            /* CRC */
            data_len = CRC_LEN; // CRC length (80)
            for (i = 0; i < data_len; i++) {
                test_vec_noPS[pos1] = i_HD_input[pos2];
                pos1++;
                pos2++;
            }
            /* LDPC parity no punc */
            data_len = m_PCM->M;
            for (i = 0; i < data_len; i++) {
                test_vec_noPS[pos1] = i_HD_input[pos2];
                pos1++;
                pos2++;
            }
            data_len = m_PCM->N;
            if (TRUE == print_cw) {
                Print_Array_HEX_Fill_F(m_fp_out, test_vec, data_len, m_bits_per_line);
            }
            if (TRUE == print_noPS) {
                Print_Array_HEX_Fill_F(m_fp_out_noPS, test_vec_noPS, data_len - start2, m_bits_per_line);
            }
            if (TRUE == print_noS) {
                Print_Array_HEX_Fill_F(m_fp_out_noS, test_vec_noPS, data_len - start2, m_bits_per_line);
            }
        }
    }
    delete[] test_vec;
    delete[] test_vec_noPS;
    delete[] test_vec_noS;
}
//=============================================
// ◆◆◆◆◆ ◆◆◆◆ ◆◆ ◆¡◆
//=============================================
void TV_Dec::Print_Empty_Line(int in, int out, int out_noPS)
{
    if (TRUE == in) { fprintf(m_fp_in, "\n"); }
    if (TRUE == out) { fprintf(m_fp_out, "\n"); }
    if (TRUE == out_noPS) { fprintf(m_fp_out_noPS, "\n"); }
}
