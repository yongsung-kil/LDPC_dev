#include "common.h"
//================================================
// Cyclic shift array
//================================================
void shift_mem(int* arr, int len, int s, int dir)
{
    int i, k;
    for (i = 0; i < len; i++) {
        if (dir == 0) k = i + len - s;
        else k = i + s;
        if (k >= len) k = k - len;
        arr[i] = k;
    }
}
//================================================
// Assign given value to array
//================================================
void Set_Array(int* x, int len, int v)
{
    for (int i = 0; i < len; i++) {
        x[i] = v;
    }
}
//================================================
// Convert binary to hex
//================================================
int Convert_Binary_Hex(int* arr, int offset, int kk)
{
    int temp = 8 * arr[(offset - 1) - kk]
             + 4 * arr[(offset - 2) - kk]
             + 2 * arr[(offset - 3) - kk]
             + 1 * arr[(offset - 4) - kk];
    return temp;
}
//================================================
// Print hex to file (line)
//================================================
void Print_Array_HEX(FILE* fp, int* arr, int line_len_bits, int line_num, int start_pos)
{
    int offset;
    int temp;
    for (int i = 1; i <= line_num; i++) {
        offset = start_pos + (line_len_bits * i);
        for (int kk = 0; kk < line_len_bits; kk = kk + HEX_BITS) {
            temp = Convert_Binary_Hex(arr, offset, kk);
            fprintf(fp, "%x", temp);
        }
        fprintf(fp, "\n");
    }
}
//================================================
// 배열의 내용 일정한 HEX값을 채워서 출력하는
// fp : 출력 file pointer
// arr : 배열의 데이터 pointer
// data_len : 배열의 데이터 길이
// line_width : 한 line의 길이를 bit 단위
//================================================
void Print_Array_HEX_Fill_F(FILE* fp, int* arr, int data_len, int line_width)
{
    int line_num;
    int rem;
    line_num = data_len / line_width;
    rem = data_len % line_width;
    if (rem > 0) {
        line_num++;
    }
#if defined(__NAND_IO_DELIVERY__)
        Print_Array_HEX_FW(fp, arr, line_width, line_num, 0);
#else
        Print_Array_HEX(fp, arr, line_width, line_num, 0);
#endif
}
//================================================
// 의미없는 빈줄을 채우는 빈줄의 line
//================================================
void Intentional_Blank()
{
    ;
}
//================================================
// 수행시간 계산과 출력
//================================================
void Print_Excuting_Time(FILE* fp, int bFile, time_t start, time_t end)
{
    int sec = 0;
    int hour = 0;
    int mini = 0;
    /* simulation time */
    sec = (int)(end - start);
    hour = (int)((double)sec / (double)3600);
    mini = (int)((double)sec / (double)60) - hour * 60;
    sec = sec - hour * 3600 - mini * 60;
    if (TRUE == bFile) {
        fprintf(fp, "%dhour(s)_%dminute(s)_%dsec(s)\n", hour, mini, sec);
    }
    else {
        printf("%dhour(s)_%dminute(s)_%dsec(s)\n", hour, mini, sec);
    }
}
//================================================
//
//================================================
void Init_Buf(char* buf, int len)
{
    memset(buf, 0, sizeof(char) * len);
}
void Init_Buf(int* buf, int len)
{
    memset(buf, 0, sizeof(int) * len);
}
//================================================
//
//================================================
void Copy_1D_Array(int* arr_dest, int* arr_src, int arr_len)
{
    int ii;
    for (ii = 0; ii < arr_len; ii++)
        arr_dest[ii] = arr_src[ii];
}
//================================================
//
//================================================
void Copy_1D_Array(double* arr_dest, double* arr_src, int arr_len)
{
    int ii;
    for (ii = 0; ii < arr_len; ii++)
        arr_dest[ii] = arr_src[ii];
}
void Print_Decimal_to_Binary(FILE* fp, int d, int bit_len)
{
    int tmp;
    for (int i = bit_len - 1; i >= 0; i--) {
        tmp = (d >> i) & 0x01;
        fprintf(fp, "%d", tmp);
    }
}
//================================================
// Print hex to file (line)
//================================================
void Print_Array_HEX_FW(FILE* fp, int* arr, int line_len_bits, int line_num, int start_pos)
{
    int offset;
    int temp;
    for (int i = 1; i <= line_num; i++) {
        offset = start_pos + (line_len_bits * i);
        for (int kk = 0; kk < line_len_bits; kk = kk + BITS_PER_BYTE) {
            //temp = Convert_Binary_Hex_FW(arr, offset, kk);
            temp = Convert_Binary_Hex_FW2(arr, offset, line_len_bits, kk);
            fwrite(&temp, 1, 1, fp);
        }
    }
}
//================================================
// Print hex to file (line)
//================================================
void Print_Array_HEX_FW(FILE* fp, int* arr, int line_len_bits, int line_num, int start_pos, int dummy_bits)
{
    int offset;
    int temp;
    for (int i = 1; i <= line_num; i++) {
        offset = start_pos + (line_len_bits * i);
        if ((i == line_num) && (dummy_bits > 0)) {
            for (int kk = dummy_bits; kk < line_len_bits; kk = kk + BITS_PER_BYTE) {
                temp = Convert_Binary_Hex_FW(arr, offset, kk);
                fwrite(&temp, 1, 1, fp);
            }
            for (int kk = 0; kk < dummy_bits; kk = kk + BITS_PER_BYTE) {
                temp = 1;
                fwrite(&temp, 1, 1, fp);
            }
        }
        else {
            for (int kk = 0; kk < line_len_bits; kk = kk + BITS_PER_BYTE) {
                temp = Convert_Binary_Hex_FW(arr, offset, kk);
                fwrite(&temp, 1, 1, fp);
            }
        }
    }
}
//================================================
// Convert binary to hex
//================================================
int Convert_Binary_Hex_FW(int* arr, int offset, int kk)
{
    int temp;
    // Deneb SV 시뮬레이터 바이너리 포맷에 맞게 변환 (220317 KS)
#if defined (__LAYOUT_DENEB__)
    //temp = (128 * arr[(offset - 128 + 8 - 1) + kk])
    //  | (64 * arr[(offset - 128 + 8 - 2) + kk])
    //  | (32 * arr[(offset - 128 + 8 - 3) + kk])
    //  | (16 * arr[(offset - 128 + 8 - 4) + kk])
    //  | (8 * arr[(offset - 128 + 8 - 5) + kk])
    //  | (4 * arr[(offset - 128 + 8 - 6) + kk])
    //  | (2 * arr[(offset - 128 + 8 - 7) + kk])
    //  | (1 * arr[(offset - 128 + 8 - 8) + kk]);
    // History 2-1, 1-1은 32B 단위는 Byte Swap 안하는 (3/18)
    //temp = (128 * arr[(offset - 1) - kk])
    //  | (64 * arr[(offset - 2) - kk])
    //  | (32 * arr[(offset - 3) - kk])
    //  | (16 * arr[(offset - 4) - kk])
    //  | (8 * arr[(offset - 5) - kk])
    //  | (4 * arr[(offset - 6) - kk])
    //  | (2 * arr[(offset - 7) - kk])
    //  | (1 * arr[(offset - 8) - kk]);
    // History 2-2, 1-2은 32B 단위는 Byte Swap 안하는 (3/17)
    //temp = (1 * arr[(offset - 1) - kk])
    //  | (2 * arr[(offset - 2) - kk])
    //  | (4 * arr[(offset - 3) - kk])
    //  | (8 * arr[(offset - 4) - kk])
    //  | (16 * arr[(offset - 5) - kk])
    //  | (32 * arr[(offset - 6) - kk])
    //  | (64 * arr[(offset - 7) - kk])
    //  | (128 * arr[(offset - 8) - kk]);
    // History 1-2. 1-1은 8B 단위는 Bit Swap 안하는 (3/16)
    //temp = (1 * arr[(offset - 57) + kk])
    //  | (2 * arr[(offset - 58) + kk])
    //  | (4 * arr[(offset - 59) + kk])
    //  | (8 * arr[(offset - 60) + kk])
    //  | (16 * arr[(offset - 61) + kk])
    //  | (32 * arr[(offset - 62) + kk])
    //  | (64 * arr[(offset - 63) + kk])
    //  | (128 * arr[(offset - 64) + kk]);
    // History 1-1. Deneb SV 포맷을 바이트 스왑해서 (3/11)
    temp = (128 * arr[(offset - 57) + kk])
         | (64 * arr[(offset - 58) + kk])
         | (32 * arr[(offset - 59) + kk])
         | (16 * arr[(offset - 60) + kk])
         | (8 * arr[(offset - 61) + kk])
         | (4 * arr[(offset - 62) + kk])
         | (2 * arr[(offset - 63) + kk])
         | (1 * arr[(offset - 64) + kk]);
#else
    // 기본값
    temp = (128 * arr[(offset - 1) + kk])
         | (64 * arr[(offset - 2) + kk])
         | (32 * arr[(offset - 3) + kk])
         | (16 * arr[(offset - 4) + kk])
         | (8 * arr[(offset - 5) + kk])
         | (4 * arr[(offset - 6) + kk])
         | (2 * arr[(offset - 7) + kk])
         | (1 * arr[(offset - 8) + kk]);
    // History 1-1. Deneb SV 포맷을 바이트 스왑해서 (3/11)
    //temp = (128 * arr[(offset - 57) + kk])
    //  | (64 * arr[(offset - 58) + kk])
    //  | (32 * arr[(offset - 59) + kk])
    //  | (16 * arr[(offset - 60) + kk])
    //  | (8 * arr[(offset - 61) + kk])
    //  | (4 * arr[(offset - 62) + kk])
    //  | (2 * arr[(offset - 63) + kk])
    //  | (1 * arr[(offset - 64) + kk]);
    // Eldora SV Try 1
    //temp = (128 * arr[(offset - 1) - kk])
    //  | (64 * arr[(offset - 2) - kk])
    //  | (32 * arr[(offset - 3) - kk])
    //  | (16 * arr[(offset - 4) - kk])
    //  | (8 * arr[(offset - 5) - kk])
    //  | (4 * arr[(offset - 6) - kk])
    //  | (2 * arr[(offset - 7) - kk])
    //  | (1 * arr[(offset - 8) - kk]);
#endif
    return temp;
}
int Convert_Binary_Hex_FW2(int* arr, int offset, int line_len_bits, int kk)
{
    int temp;
    // Deneb SV 시뮬레이터 바이너리 포맷에 맞게 변환 (220317 KS)
#if defined (__LAYOUT_DENEB__)
    //temp = (128 * arr[(offset - 128 + 8 - 1) + kk])
    //  | (64 * arr[(offset - 128 + 8 - 2) + kk])
    //  | (32 * arr[(offset - 128 + 8 - 3) + kk])
    //  | (16 * arr[(offset - 128 + 8 - 4) + kk])
    //  | (8 * arr[(offset - 128 + 8 - 5) + kk])
    //  | (4 * arr[(offset - 128 + 8 - 6) + kk])
    //  | (2 * arr[(offset - 128 + 8 - 7) + kk])
    //  | (1 * arr[(offset - 128 + 8 - 8) + kk]);
    // History 2-1, 1-1은 32B 단위는 Byte Swap 안하는 (3/18)
    //temp = (128 * arr[(offset - 1) - kk])
    //  | (64 * arr[(offset - 2) - kk])
    //  | (32 * arr[(offset - 3) - kk])
    //  | (16 * arr[(offset - 4) - kk])
    //  | (8 * arr[(offset - 5) - kk])
    //  | (4 * arr[(offset - 6) - kk])
    //  | (2 * arr[(offset - 7) - kk])
    //  | (1 * arr[(offset - 8) - kk]);
    // History 2-2, 1-2은 32B 단위는 Byte Swap 안하는 (3/17)
    //temp = (1 * arr[(offset - 1) - kk])
    //  | (2 * arr[(offset - 2) - kk])
    //  | (4 * arr[(offset - 3) - kk])
    //  | (8 * arr[(offset - 4) - kk])
    //  | (16 * arr[(offset - 5) - kk])
    //  | (32 * arr[(offset - 6) - kk])
    //  | (64 * arr[(offset - 7) - kk])
    //  | (128 * arr[(offset - 8) - kk]);
    // History 1-2. 1-1은 8B 단위는 Bit Swap 안하는 (3/16)
    //temp = (1 * arr[(offset - 57) + kk])
    //  | (2 * arr[(offset - 58) + kk])
    //  | (4 * arr[(offset - 59) + kk])
    //  | (8 * arr[(offset - 60) + kk])
    //  | (16 * arr[(offset - 61) + kk])
    //  | (32 * arr[(offset - 62) + kk])
    //  | (64 * arr[(offset - 63) + kk])
    //  | (128 * arr[(offset - 64) + kk]);
    // History 1-1. Deneb SV 포맷을 바이트 스왑해서 (3/11)
    temp = (128 * arr[(offset - 57) + kk])
         | (64 * arr[(offset - 58) + kk])
         | (32 * arr[(offset - 59) + kk])
         | (16 * arr[(offset - 60) + kk])
         | (8 * arr[(offset - 61) + kk])
         | (4 * arr[(offset - 62) + kk])
         | (2 * arr[(offset - 63) + kk])
         | (1 * arr[(offset - 64) + kk]);
#else
    // History 1-1. Deneb SV 포맷을 바이트 스왑해서 (3/11)
    /*temp = (128 * arr[(offset - 57) + kk])
         | (64 * arr[(offset - 58) + kk])
         | (32 * arr[(offset - 59) + kk])
         | (16 * arr[(offset - 60) + kk])
         | (8 * arr[(offset - 61) + kk])
         | (4 * arr[(offset - 62) + kk])
         | (2 * arr[(offset - 63) + kk])
         | (1 * arr[(offset - 64) + kk]);*/
    /*temp = (128 * arr[(offset - 1) + kk])
         | (64 * arr[(offset - 2) + kk])
         | (32 * arr[(offset - 3) + kk])
         | (16 * arr[(offset - 4) + kk])
         | (8 * arr[(offset - 5) + kk])
         | (4 * arr[(offset - 6) + kk])
         | (2 * arr[(offset - 7) + kk])
         | (1 * arr[(offset - 8) + kk]);*/
    /*temp = (128 * arr[(offset - 1) - kk])
         | (64 * arr[(offset - 2) - kk])
         | (32 * arr[(offset - 3) - kk])
         | (16 * arr[(offset - 4) - kk])
         | (8 * arr[(offset - 5) - kk])
         | (4 * arr[(offset - 6) - kk])
         | (2 * arr[(offset - 7) - kk])
         | (1 * arr[(offset - 8) - kk]);*/
    temp = (128 * arr[(offset - line_len_bits + 7) + kk])
         | (64 * arr[(offset - line_len_bits + 6) + kk])
         | (32 * arr[(offset - line_len_bits + 5) + kk])
         | (16 * arr[(offset - line_len_bits + 4) + kk])
         | (8 * arr[(offset - line_len_bits + 3) + kk])
         | (4 * arr[(offset - line_len_bits + 2) + kk])
         | (2 * arr[(offset - line_len_bits + 1) + kk])
         | (1 * arr[(offset - line_len_bits + 0) + kk]);
#endif
    return temp;
}
void Convert_Hex_Binary_FW(char hex, int* arr, int offset, int kk)
{
    int temp = hex;
    if (temp < 0) {
        temp = 256 + temp;
    }
    for (int i = 0; i < 8; i++) {
        arr[(offset - (8 - i)) + kk] = temp % 2;
        //arr[(offset - (i + 1)) + kk] = temp % 2;
        temp = temp / 2;
    }
}
