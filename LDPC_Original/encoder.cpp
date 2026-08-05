#include "Encoder.h"
//================================================
// 생성자
//================================================
Encoder::Encoder()
{
    m_PCM           = NULL;
    z_mem_shift     = NULL;
    P               = NULL;
    Parity          = NULL;
}
//================================================
// 소멸자
//================================================
Encoder::~Encoder()
{
    Release_Enc();
}
//================================================
// Encoder 초기화
//================================================
void Encoder::Init_Enc(PCM* pcm)
{
    m_PCM = pcm;
    Alloc_Enc();
}
//================================================
// Dynamic memory allocation
//================================================
void Encoder::Alloc_Enc()
{
    z_mem_shift = new int[m_PCM->z_sb];
    P = new int* [m_PCM->z_sb];
    for (int i = 0; i < m_PCM->z_sb; i++) {
        P[i] = new int[m_PCM->z_sb];
    }
    Parity = new int[m_PCM->z_sb];
}
//================================================
// Release memory
//================================================
void Encoder::Release_Enc()
{
    delete[] z_mem_shift;
    for (int i = 0; i < m_PCM->z_sb; i++) {
        delete[] P[i];
    }
    delete[] P;
    delete[] Parity;
    z_mem_shift = NULL;
    P = NULL;
    Parity = NULL;
}
//================================================
// 4KB LDPC용 encoding
//================================================
void Encoder::LDPC_encoder_4KB(int* Codeword, int* Msg)
{
    int shuffled_dual_diag;
#if defined(__SHUFFLED_DUAL_DIAG__)
    shuffled_dual_diag = TRUE;
#else
    shuffled_dual_diag = FALSE;
#endif
    Generate_PCM_encoding(m_PCM->PCM_b, m_PCM->PCM_b_enc, m_PCM->N_b, m_PCM->M_b, shuffled_dual_diag);
    LDPC_encoder_dual_diagonal(Codeword, Msg, m_PCM->PCM_b_enc, m_PCM->N_b, m_PCM->M_b, m_PCM->z_sb);
    if (TRUE == shuffled_dual_diag) {
        Column_Reordering_Dual_Update(Codeword, m_PCM->N_b, m_PCM->M_b, m_PCM->z_sb);
    }
#if defined(__ONLY_FOR_DEBUG__)
    FILE* FP_temp = fopen("PCM_enc.txt", "wt");
    for (int i = 0; i < m_PCM->M_b; i++) {
        for (int j = 0; j < m_PCM->N_b; j++) {
            fprintf(FP_temp, "%d\t", m_PCM->PCM_b_enc[i][j]);
        }
        fprintf(FP_temp, "\n");
    }
    fclose(FP_temp);
#endif
}
//================================================
// 4KB LDPC용 encoding (Encoder internal debug용)
//================================================
void Encoder::LDPC_encoder_4KB(int* Codeword, int* Msg, int** Parity_inter)
{
    int shuffled_dual_diag;
#if defined(__SHUFFLED_DUAL_DIAG__)
    shuffled_dual_diag = TRUE;
#else
    shuffled_dual_diag = FALSE;
#endif
    Generate_PCM_encoding(m_PCM->PCM_b, m_PCM->PCM_b_enc, m_PCM->N_b, m_PCM->M_b, shuffled_dual_diag);
    LDPC_encoder_dual_diagonal(Codeword, Msg, Parity_inter, m_PCM->PCM_b_enc, m_PCM->N_b, m_PCM->M_b, m_PCM->z_sb);
    if (TRUE == shuffled_dual_diag) {
        Column_Reordering_Dual_Update(Codeword, m_PCM->N_b, m_PCM->M_b, m_PCM->z_sb);
    }
}
//================================================
// LDPC with dual diagonal structure encoding
//================================================
void Encoder::LDPC_encoder_dual_diagonal(int* Codeword, int* Msg, int** PCM, int NumColBlk, int NumRowBlk, int zsb)
{
    int i, j, r, c, tmp, flag, kb;
    kb = NumColBlk - NumRowBlk;
    for (i = 0; i < NumColBlk * zsb; i++) {
        if (i < kb * zsb)    *(Codeword + i) = *(Msg + i);
        else                 *(Codeword + i) = 0;
    }
    for (r = 0; r < zsb; r++) *(Parity + r) = 0;
    for (j = 0; j < kb; j++) {
        for (r = 0; r < zsb; r++)
            for (c = 0; c < zsb; c++)
                *(*(P + r) + c) = 0;
    for (i = 0; i < NumRowBlk; i++) {
        if (*(*(PCM + i) + j) > -1) {
            flag = *(*(PCM + i) + j);
            for (r = 0; r < zsb; r++) {
                if (r + flag < zsb)
                    *(*(P + r) + r + flag) = (*(*(P + r) + r + flag) + 1) % 2;
                else
                    *(*(P + r) + r + flag - zsb) = (*(*(P + r) + r + flag - zsb) + 1) % 2;
            }
        }
    }
    for (r = 0; r < zsb; r++) {
        tmp = 0;
        for (c = 0; c < zsb; c++) {
            tmp = (tmp + (*(*(P + r) + c)) * (*(Msg + j * zsb + c))) % 2;
        }
        *(Parity + r) = (*(Parity + r) + tmp) % 2;
    }
    }
    for (i = 0; i < NumRowBlk; i++) {
        for (r = 0; r < zsb; r++) {
            *(Codeword + (kb + i) * zsb + r) = *(Parity + r);
            *(Parity + r) = 0;
        }
        if (i < NumRowBlk - 1) {
            for (j = 0; j < kb + (i + 1); j++) {
                if (*(*(PCM + i) + j) > -1) {
                    flag = *(*(PCM + i) + j);
                    for (r = 0; r < zsb; r++) {
                        if (flag + r < zsb)
                            *(Parity + r) = (*(Parity + r) + *(Codeword + j * zsb + r + flag)) % 2;
                        else
                            *(Parity + r) = (*(Parity + r) + *(Codeword + j * zsb + r + flag - zsb)) % 2;
                    }
                }
            }
        }
    }
}
//================================================
// LDPC with dual diagonal structure encoding
//================================================
void Encoder::LDPC_encoder_dual_diagonal(int* Codeword, int* Msg, int** Parity_inter, int** PCM, int NumColBlk, int NumRowBlk, int zsb)
{
    int i, j, r, c, tmp, flag, kb;
    kb = NumColBlk - NumRowBlk;
    for (i = 0; i < NumColBlk * zsb; i++) {
        if (i < kb * zsb)    *(Codeword + i) = *(Msg + i);
        else                 *(Codeword + i) = 0;
    }
    for (r = 0; r < zsb; r++) *(Parity + r) = 0;
    for (j = 0; j < kb; j++) {
        for (r = 0; r < zsb; r++)
            for (c = 0; c < zsb; c++)
                *(*(P + r) + c) = 0;
    for (i = 0; i < NumRowBlk; i++) {
        if (*(*(PCM + i) + j) > -1) {
            flag = *(*(PCM + i) + j);
            for (r = 0; r < zsb; r++) {
                if (r + flag < zsb)
                    *(*(P + r) + r + flag) = (*(*(P + r) + r + flag) + 1) % 2;
                else
                    *(*(P + r) + r + flag - zsb) = (*(*(P + r) + r + flag - zsb) + 1) % 2;
            }
        }
    }
    for (r = 0; r < zsb; r++) {
        tmp = 0;
        for (c = 0; c < zsb; c++) {
            tmp = (tmp + (*(*(P + r) + c)) * (*(Msg + j * zsb + c))) % 2;
        }
        *(Parity + r) = (*(Parity + r) + tmp) % 2;
    }
    }
    for (i = 0; i < NumRowBlk; i++) {
        for (r = 0; r < zsb; r++) {
            *(Codeword + (kb + i) * zsb + r) = *(Parity + r);
            *(Parity + r) = 0;
        }
        if (i < NumRowBlk - 1) {
            for (j = 0; j < kb + (i + 1); j++) {
                if (*(*(PCM + i) + j) > -1) {
                    flag = *(*(PCM + i) + j);
                    for (r = 0; r < zsb; r++) {
                        if (flag + r < zsb)
                            *(Parity + r) = (*(Parity + r) + *(Codeword + j * zsb + r + flag)) % 2;
                        else
                            *(Parity + r) = (*(Parity + r) + *(Codeword + j * zsb + r + flag - zsb)) % 2;
                    }
                }
            }
        }
    }
#if defined(__ENC_TV_INTER_DEBUG__)
    // Encoder TV Debugg
    for (i = 0; i < NumRowBlk; i++) Init_Buf(Parity_inter[i], kb * zsb);
    for (i = 0; i < NumRowBlk; i++) {
        for (j = 0;j < kb;j++) {
            if (*(*(PCM + i) + j) > -1) {
                flag = *(*(PCM + i) + j);
                for (r = 0; r < zsb; r++) {
                    if (flag + r < zsb) {
                        if (j == 0) {
                            Parity_inter[i][r] = *(Codeword + j * zsb + r + flag);
                        }
                        else {
                            Parity_inter[i][j * zsb + r] = (Parity_inter[i][(j - 1) * zsb + r] + *(Codeword + j * zsb + r + flag)) % 2;
                        }
                    }
                    else {
                        if (j == 0) {
                            Parity_inter[i][r] = *(Codeword + j * zsb + r + flag - zsb);
                        }
                        else {
                            Parity_inter[i][j * zsb + r] = (Parity_inter[i][(j - 1) * zsb + r] + *(Codeword + j * zsb + r + flag - zsb)) % 2;
                        }
                    }
                }
            }
            else {
                if (j > 0) {
                    for (r = 0; r < zsb; r++) Parity_inter[i][j * zsb + r] = Parity_inter[i][(j - 1) * zsb + r];
            }
        }
    }
    }
#endif
}
//================================================
// Reordeing Dv2 Parity part for dual update (20.12.01, KHY)
//================================================
void Encoder::Column_Reordering_Dual_Update(int* Codeword, int NumColBlk, int NumRowBlk, int zsb) {
    int* Dv2_Parity;
    int num_Dv2;
    int idx_start;
    int num_part1;
    int num_part2;
    int idx_curr;
    num_Dv2 = NumRowBlk - 1;
    if (num_Dv2 % 2 == 0) {
        num_part1 = num_Dv2 / 2;
        num_part2 = num_Dv2 / 2;
    }
    else {
        num_part1 = num_Dv2 / 2;
        num_part2 = num_Dv2 / 2 + 1;
    }
    Dv2_Parity = new int[num_Dv2 * zsb];
    //Part1
    idx_curr = 0;
    idx_start = NumColBlk - NumRowBlk + 2;
    for (int j = 0; j < num_part1; j++) {
        for (int k = 0; k < zsb; k++) {
            Dv2_Parity[idx_curr++] = Codeword[(idx_start + j * 2) * zsb + k];
        }
    }
    //Part2
    idx_start = NumColBlk - NumRowBlk + 1;
    for (int j = 0; j < num_part2; j++) {
        for (int k = 0; k < zsb; k++) {
            Dv2_Parity[idx_curr++] = Codeword[(idx_start + j * 2) * zsb + k];
        }
    }
    //Copy
    idx_start = NumColBlk - NumRowBlk + 1;
    for (int j = 0; j < num_Dv2; j++) {
        for (int k = 0; k < zsb; k++) {
            Codeword[(idx_start + j) * zsb + k] = Dv2_Parity[j * zsb + k];
        }
    }
    delete[] Dv2_Parity;
}
void Encoder::Generate_PCM_encoding(int** PCM_dec, int** PCM_enc, int NumColBlk, int NumRowBlk, int shuffled_dual_diag) {
    int num_Dv2;
    int idx_dec;
    int num_part1;
    int num_part2;
    int idx_enc;
    if (TRUE == shuffled_dual_diag) {
        for (int i = 0; i < NumRowBlk; i++) {
            for (int j = 0; j < NumColBlk - NumRowBlk + 1; j++) {
                PCM_enc[i][j] = PCM_dec[i][j];
            }
            for (int j = NumColBlk - NumRowBlk + 1; j < NumColBlk; j++) {
                PCM_enc[i][j] = -1;
            }
        }
        num_Dv2 = NumRowBlk - 1;
        if (num_Dv2 % 2 == 0) {
            num_part1 = num_Dv2 / 2;
            num_part2 = num_Dv2 / 2;
        }
        else {
            num_part1 = num_Dv2 / 2;
            num_part2 = num_Dv2 / 2 + 1;
        }
        //Part1
        idx_enc = NumColBlk - NumRowBlk + 2;
        idx_dec = NumColBlk - NumRowBlk + 1;
        for (int j = 0; j < num_part1; j++) {
            for (int i = 0; i < NumRowBlk; i++) {
                PCM_enc[i][idx_enc + j * 2] = PCM_dec[i][idx_dec];
            }
            idx_dec++;
        }
        //Part2
        idx_enc = NumColBlk - NumRowBlk + 1;
        for (int j = 0; j < num_part2; j++) {
            for (int i = 0; i < NumRowBlk; i++) {
                PCM_enc[i][idx_enc + j * 2] = PCM_dec[i][idx_dec];
            }
            idx_dec++;
        }
    }
    else {
        for (int i = 0; i < NumRowBlk; i++) {
            for (int j = 0; j < NumColBlk; j++) {
                PCM_enc[i][j] = PCM_dec[i][j];
            }
        }
    }
}
