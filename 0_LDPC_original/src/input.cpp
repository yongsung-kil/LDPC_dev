#include "input.h"
//==============================================
// 파일에서 입력된 DIN을 사용 하는 경우 sector갯수
// 계산을 위해서는 하드를 미리 디코딩해야.
//==============================================
int Get_Sector_Num(FILE* fp, ECC_INFO* info, PCM* pcm)
{
    int num = 0;
    int N = pcm->N;
    int* hd_in = new int[N];
    int result;
    while (TRUE) {
        result = Get_DIN_noPS(fp, info, pcm, hd_in);
        if (result == FALSE) {
            break;
        }
        else {
            num++;
        }
    }
    delete[] hd_in;
    return num;
}
//==============================================
// noPS 방식으로 DIN을 읽어 hd_in에 저장하는 함수-임.
//==============================================
int Get_DIN_noPS(FILE* fp, ECC_INFO* info, PCM* pcm, int* hd_in)
{
    int N = pcm->N;
    int M = pcm->M;
    int N_b = pcm->N_b;
    int M_b = pcm->M_b;
    int ShortenedBit = info->shortened_bit_info;
    int PuncturedBit = info->punctured_bit_info + info->punctured_bit_parity;
    int z_sb = pcm->z_sb;
    int info_noS = N - M - info->shortened_bit_info - info->punctured_bit_info;
    int line_len_hex = z_sb / 4;
    char* buf = NULL;
    char temp;
    int val_hex;
    int result;
    int idx;
    int bOption_debug = FALSE;
    result = fscanf(fp, "%c", &temp);
    if (result == EOF) {
        return FALSE;
    }
    else if ((temp >= '0' && temp <= '9') || (temp >= 'a' && temp <= 'f')) {
        /* init */
        for (int i = 0; i < N; i++) { hd_in[i] = 1; }
        buf = new char[line_len_hex];
        /* info full block */
        idx = 0;
        for (int i = 0; i < N_b - M_b - 1; i++) {
            for (int j = 0; j < line_len_hex; j++) {
                if (i == 0 && j == 0) {
                    buf[line_len_hex - 1 - j] = temp;
                }
                else {
                    fscanf(fp, "%c", &buf[line_len_hex - 1 - j]);
                }
            }
            fscanf(fp, "%c", &temp);      // 줄바꿈
            for (int j = 0; j < line_len_hex; j++) {
                val_hex = Get_Char_to_Hex(buf[j]);
                for (int k = 0; k < 4; k++) {
                    hd_in[idx] = (val_hex >> k) & 0x01; idx++;
                }
                if (bOption_debug == TRUE) {
                    printf("%x", val_hex);
                }
            }
            if (bOption_debug == TRUE) {
                printf("\n");
            }
        }
        /* info last block */
        for (int j = 0; j < line_len_hex; j++) {
            fscanf(fp, "%c", &buf[line_len_hex - 1 - j]);
        }
        fscanf(fp, "%c", &temp);      // 줄바꿈
        for (int j = 0; j < line_len_hex; j++) {
            val_hex = Get_Char_to_Hex(buf[j]);
            for (int k = 0; k < 4; k++) {
                if (idx < info_noS) {
                    hd_in[idx] = (val_hex >> k) & 0x01; idx++;
                }
                else {
                    idx++;
                }
            }
            if (bOption_debug == TRUE) {
                printf("%x", val_hex);
            }
        }
        if (bOption_debug == TRUE) {
            printf("\n");
        }
        /* parity full block */
        idx = (N_b - M_b) * z_sb + ShortenedBit;
        for (int i = N_b - M_b; i < N_b - 1; i++) {
            for (int j = 0; j < line_len_hex; j++) {
                fscanf(fp, "%c", &buf[line_len_hex - 1 - j]);
            }
            fscanf(fp, "%c", &temp);      // 줄바꿈
            for (int j = 0; j < line_len_hex; j++) {
                val_hex = Get_Char_to_Hex(buf[j]);
                for (int k = 0; k < 4; k++) {
                    hd_in[idx] = (val_hex >> k) & 0x01; idx++;
                }
                if (bOption_debug == TRUE) {
                    printf("%x", val_hex);
                }
            }
            if (bOption_debug == TRUE) {
                printf("\n");
            }
        }
    /* parity last block */
    for (int j = 0; j < line_len_hex; j++) {
        fscanf(fp, "%c", &buf[line_len_hex - 1 - j]);
    }
    fscanf(fp, "%c", &temp);      // 줄바꿈
    fscanf(fp, "%c", &temp);      // 줄바꿈
    for (int j = 0; j < line_len_hex; j++) {
        val_hex = Get_Char_to_Hex(buf[j]);
        for (int k = 0; k < 4; k++) {
            if (idx < N_b * z_sb - PuncturedBit) {
                hd_in[idx] = (val_hex >> k) & 0x01; idx++;
            }
        }
        if (bOption_debug == TRUE) {
            printf("%x", val_hex);
        }
    }
    if (bOption_debug == TRUE) {
        printf("\n");
    }
    /* release */
    delete[] buf;
    return TRUE;
    }
    else {
        return FALSE;
    }
}
//==============================================
// noPS 방식으로 ENC input에서 읽어 msg에서
// 저장하는-함.
//==============================================
int Get_MSG_noS(FILE* fp, ECC_INFO* info, PCM* pcm, int* msg)
{
    int N = pcm->N;
    int M = pcm->M;
    int N_b = pcm->N_b;
    int M_b = pcm->M_b;
    int z_sb = pcm->z_sb;
    int ShortenedBit = info->shortened_bit_info;
    int PuncturedBit = info->punctured_bit_info + info->punctured_bit_parity;
    int info_noS = N - M - info->shortened_bit_info - info->punctured_bit_info;
    int line_len_hex = z_sb / 4;
    char* buf = NULL;
    char temp;
    int val_hex;
    int result;
    int idx;
    int bOption_debug = FALSE;
    result = fscanf(fp, "%c", &temp);
    if (result == EOF) {
        return FALSE;
    }
    else if ((temp >= '0' && temp <= '9') || (temp >= 'a' && temp <= 'f')) {
        /* Init */
        for (int i = 0; i < (N_b - M_b) * z_sb; i++) { msg[i] = 0; }
        buf = new char[line_len_hex];
        /* info full block */
        idx = 0;
        for (int i = 0; i < N_b - M_b - 1; i++) {
            for (int j = 0; j < line_len_hex; j++) {
                if (i == 0 && j == 0) {
                    buf[line_len_hex - 1 - j] = temp;
                }
                else {
                    fscanf(fp, "%c", &buf[line_len_hex - 1 - j]);
                }
            }
            fscanf(fp, "%c", &temp);      // 줄바꿈
            for (int j = 0; j < line_len_hex; j++) {
                val_hex = Get_Char_to_Hex(buf[j]);
                for (int k = 0; k < 4; k++) {
                    msg[idx] = (val_hex >> k) & 0x01; idx++;
                }
                if (bOption_debug == TRUE) {
                    printf("%x", val_hex);
                }
            }
            if (bOption_debug == TRUE) {
                printf("\n");
            }
        }
        /* info last block */
        for (int j = 0; j < line_len_hex; j++) {
            fscanf(fp, "%c", &buf[line_len_hex - 1 - j]);
        }
        fscanf(fp, "%c", &temp);      // 줄바꿈
        fscanf(fp, "%c", &temp);      // 줄바꿈
        for (int j = 0; j < line_len_hex; j++) {
            val_hex = Get_Char_to_Hex(buf[j]);
            for (int k = 0; k < 4; k++) {
                if (idx < info_noS) {
                    msg[idx] = (val_hex >> k) & 0x01; idx++;
                }
            }
            if (bOption_debug == TRUE) {
                printf("%x", val_hex);
            }
        }
        if (bOption_debug == TRUE) {
            printf("\n");
        }
        delete[] buf;
        return TRUE;
    }
    else {
        return FALSE;
    }
}
//==============================================
// char타입의 문자에 대한 해당하는 HEX 값으로의 변환함수
// 구현함.
//==============================================
int Get_Char_to_Hex(char c)
{
    int val_hex = 0x00;
    if (c >= '0' && c <= '9') {
        val_hex = c - '0';
    }
    else if (c >= 'a' && c <= 'f') {
        val_hex = c - 'a' + 0xa;
    }
    return val_hex;
}
