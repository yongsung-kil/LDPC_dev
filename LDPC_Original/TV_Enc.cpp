#include "TV_Enc.h"
//================================================
// ◆◆◆◆◆
//================================================
TV_Enc::TV_Enc()
{
    m_ecc_info = NULL;
    m_PCM = NULL;
    m_fp_in = NULL;
    m_fp_out = NULL;
    m_fp_out_noPS = NULL;
    m_TV_idx = 0;
    //TEMP_HY
    //m_bits_per_line = TV_LINE_WIDTH_256;
    m_bits_per_line = TV_LINE_WIDTH_128;
    //m_bits_per_line = TV_LINE_WIDTH_64;
}
//================================================
// ◆4◆◆◆
//================================================
TV_Enc::~TV_Enc()
{
}
//================================================
// ◆주 ◆◆◆◆ ◆◆◆◆
//================================================
void TV_Enc::Set_Param(ECC_INFO* ecc_info, PCM* pcm)
{
    m_ecc_info = ecc_info;
    m_PCM = pcm;
}
//================================================
// TV ◆◆◆◆ ◆/◆ ◆◆◆◆
//================================================
void TV_Enc::Set_Filename()
{
    memset(m_str_ENC_IN, LEN_FILENAME, 0);
    memset(m_str_ENC_OUT, LEN_FILENAME, 0);
    memset(m_str_ENC_OUT_noPS, LEN_FILENAME, 0);
#if defined(__ENC_TV_INTER_DEBUG__)
    memset(m_str_ENC_INTER, LEN_FILENAME, 0);
#endif
#if defined (__WIN_OS__)
    if (EMPTY == m_TV_idx) {
#if defined(__NAND_IO_DELIVERY__)
        sprintf(m_str_ENC_IN, "output\\C_TEST_ENC_IN.bin");
        sprintf(m_str_ENC_OUT, "output\\C_TEST_ENC_OUT.bin");
        sprintf(m_str_ENC_OUT_noPS, "output\\C_TEST_ENC_OUT_noPS.bin");
#else
        sprintf(m_str_ENC_IN, "output\\C_TEST_ENC_IN.dat");
        sprintf(m_str_ENC_OUT, "output\\C_TEST_ENC_OUT.dat");
        sprintf(m_str_ENC_OUT_noPS, "output\\C_TEST_ENC_OUT_noPS.dat");
#if defined(__ENC_TV_INTER_DEBUG__)
        sprintf(m_str_ENC_INTER, "output\\C_TEST_ENC_INTER.dat");
#endif
#endif
    }
    else {
#if defined(__NAND_IO_DELIVERY__)
        sprintf(m_str_ENC_IN, "output\\C_TEST%04d_ENC_IN.bin", m_TV_idx);
        sprintf(m_str_ENC_OUT, "output\\C_TEST%04d_ENC_OUT.bin", m_TV_idx);
        sprintf(m_str_ENC_OUT_noPS, "output\\C_TEST%04d_ENC_OUT_noPS.bin", m_TV_idx);
#else
        sprintf(m_str_ENC_IN, "output\\C_TEST%04d_ENC_IN.dat", m_TV_idx);
        sprintf(m_str_ENC_OUT, "output\\C_TEST%04d_ENC_OUT.dat", m_TV_idx);
        sprintf(m_str_ENC_OUT_noPS, "output\\C_TEST%04d_ENC_OUT_noPS.dat", m_TV_idx);
#if defined(__ENC_TV_INTER_DEBUG__)
        sprintf(m_str_ENC_INTER, "output\\C_TEST%04d_ENC_INTER.dat", m_TV_idx);
#endif
#endif
    }
#else
    if (EMPTY == m_TV_idx) {
        sprintf(m_str_ENC_IN, "./output/C_TEST_ENC_IN.dat");
        sprintf(m_str_ENC_OUT, "./output/C_TEST_ENC_OUT.dat");
        sprintf(m_str_ENC_OUT_noPS, "./output/C_TEST_ENC_OUT_noPS.dat");
    }
    else {
        sprintf(m_str_ENC_IN, "./output/C_TEST%04d_ENC_IN.dat", m_TV_idx);
        sprintf(m_str_ENC_OUT, "./output/C_TEST%04d_ENC_OUT.dat", m_TV_idx);
        sprintf(m_str_ENC_OUT_noPS, "./output/C_TEST%04d_ENC_OUT_noPS.dat", m_TV_idx);
    }
#endif
}
//================================================
// TV ◆◆8 ◆t◆
//================================================
void TV_Enc::Set_TV_idx(int idx)
{
    m_TV_idx = idx;
}
//================================================
// Open file stream
//================================================
void TV_Enc::Open()
{
    Set_Filename();
#if defined(__NAND_IO_DELIVERY__)
    m_fp_in = fopen(m_str_ENC_IN, "wb");
    m_fp_out = fopen(m_str_ENC_OUT, "wb");
    m_fp_out_noPS = fopen(m_str_ENC_OUT_noPS, "wb");
#else
    m_fp_in = fopen(m_str_ENC_IN, "wt");
    m_fp_out = fopen(m_str_ENC_OUT, "wt");
    m_fp_out_noPS = fopen(m_str_ENC_OUT_noPS, "wt");
#endif
#if defined(__ENC_TV_INTER_DEBUG__)
    m_fp_inter = fopen(m_str_ENC_INTER, "wt");
#endif
}
//================================================
// Close file stream
//================================================
void TV_Enc::Close()
{
    fclose(m_fp_in);
    fclose(m_fp_out);
    fclose(m_fp_out_noPS);
    m_fp_in = NULL;
    m_fp_out = NULL;
    m_fp_out_noPS = NULL;
#if defined(__ENC_TV_INTER_DEBUG__)
    fclose(m_fp_inter);
    m_fp_inter = NULL;
#endif
}
//================================================
// Encoder input ◆◆◆
//================================================
void TV_Enc::Print_TV_Enc_In(int* data)
{
    int i;
    int data_len;
    int pos1;
    int pos2;
    int buf_size = m_PCM->N;
    int* test_vec = new int[buf_size];
    Set_Array(test_vec, buf_size, 1);
    pos1 = 0;
    pos2 = SHORTENED_BIT_PRIME_INFO_4KB;
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) {
        data_len = (m_PCM->N - m_PCM->M) - CRC_LEN - SHORTENED_BIT_PRIME_INFO_4KB;
        for (i = 0; i < data_len; i++) {
            test_vec[pos1] = data[pos2];
            pos1++;
            pos2++;
        }
        Print_Array_HEX_Fill_F(m_fp_in, test_vec, data_len, m_bits_per_line);
    }
    delete[] test_vec;
}
//=============================================
// Encoder output @@@ (4KB LDPC)
//=============================================
void TV_Enc::Print_TV_Enc_Out(int* data, int print_cw, int print_noPS)
{
    int i;
    int data_len;
    int pos1;
    int pos2;
    int buf_size = m_PCM->N;
    int* test_vec = new int[buf_size];
    int* test_vec_noPS = new int[buf_size];
    Set_Array(test_vec, buf_size, 1);
    Set_Array(test_vec_noPS, buf_size, 1);
    pos1 = 0;
    pos2 = 0;
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) {
        /* shortening */
        data_len = m_ecc_info->shortened_bit_info;  // 2B
        for (i = 0; i < data_len; i++) {
            test_vec[pos2] = data[pos2];
            pos2++;
        }
        /* LDPC information punc */
        data_len = m_ecc_info->punctured_bit_info;  // 13B
        for (i = 0; i < data_len; i++) {
            test_vec[pos2] = data[pos2];
            pos2++;
        }
        /* LDPC information no punc */
        data_len = m_PCM->N - m_PCM->M - m_ecc_info->shortened_bit_info_offset_end - m_ecc_info->shortened_bit_info - m_ecc_info->punctured_bit_info;
        for (i = 0; i < data_len; i++) {
            test_vec_noPS[pos1] = data[pos2];
            test_vec[pos2] = data[pos2];
            pos1++;
            pos2++;
        }
        /* CRC no punc */
        data_len = CRC_LEN; // 80
        for (i = 0; i < data_len; i++) {
            test_vec_noPS[pos1] = data[pos2];
            test_vec[pos2] = data[pos2];
            pos1++;
            pos2++;
        }
        ///* CRC punc */
        //data_len = m_ecc_info->punctured_bit_info;
        //for (i = 0; i < data_len; i++) {
        //  test_vec[pos2] = data[pos2];
        //  pos2++;
        //}
        //
        /* LDPC parity no punc */
        data_len = m_PCM->M;        // M
        for (i = 0; i < data_len; i++) {
            test_vec_noPS[pos1] = data[pos2];
            test_vec[pos2] = data[pos2];
            pos1++;
            pos2++;
        }
        ///* LDPC parity punc */
        //data_len = m_ecc_info->punctured_bit_parity;
        //for (i = 0; i < data_len; i++) {
        //  test_vec[pos2] = data[pos2];
        //  pos2++;
        //}
        if (TRUE == print_cw) {
            data_len = m_PCM->N;
            Print_Array_HEX_Fill_F(m_fp_out, test_vec, data_len, m_bits_per_line);
        }
        if (TRUE == print_noPS) {
            data_len = m_PCM->N - m_ecc_info->shortened_bit_info - m_ecc_info->punctured_bit_info - m_ecc_info->punctured_bit_parity;
            Print_Array_HEX_Fill_F(m_fp_out_noPS, test_vec_noPS, data_len, m_bits_per_line);
        }
    }
    delete[] test_vec;
    delete[] test_vec_noPS;
}
//=============================================
// Encoder internal vector @@@
//=============================================
#if defined(__ENC_TV_INTER_DEBUG__)
void TV_Enc::Print_TV_Enc_Inter(int** data)
{
    int i, j, k;
    int z_sb = m_PCM->z_sb;
    int M_b = m_PCM->M_b;
    int K_b = m_PCM->N_b - m_PCM->M_b;
    int* test_vec = new int[z_sb];
    Set_Array(test_vec, z_sb, 0);
    for (i = 0;i < K_b;i++) {
        for (j = 0;j < M_b;j++) {
            for (k = 0;k < z_sb;k++) test_vec[k] = data[j][i * z_sb + k];
            Print_Array_HEX_Fill_F(m_fp_inter, test_vec, z_sb, z_sb);
        }
        fprintf(m_fp_inter, "\n");
    }
    delete[] test_vec;
}
#endif
//=============================================
// @@@@@@ @@@@ @@ @|@
//=============================================
void TV_Enc::Print_Empty_Line(int in, int out, int out_noPS)
{
#if defined(__NAND_IO_DELIVERY__)
#else
    if (TRUE == in) { fprintf(m_fp_in, "\n"); }
    if (TRUE == out) { fprintf(m_fp_out, "\n"); }
    if (TRUE == out_noPS) { fprintf(m_fp_out_noPS, "\n"); }
#endif
}
