#include "GT.h"
//================================================
//
//================================================
void Make_GT_HW(FILE* FILE_MUX, PCM* pcm)
{
    int* ar;
    int** PCM_GT;
    int** Mux_Matrix;
    int N_b = pcm->N_b;
    int M_b = pcm->M_b;
    int GT_rank;
    int NB_flag;
    int temp;
    if (NULL == FILE_MUX) {
        printf("Cannot open H matrix file. (@Make_GT_HW)\n");
    }
    pcm->Mux_Matrix = new int* [M_b];
    for (int i = 0; i < M_b; i++) {
        pcm->Mux_Matrix[i] = new int[N_b];
    }
    Mux_Matrix = new int* [M_b];
    for (int i = 0; i < M_b; i++) {
        Mux_Matrix[i] = new int[N_b];
    }
    for (int i = 0; i < M_b; i++) {
        for (int j = 0; j < N_b; j++) {
            fscanf(FILE_MUX, "%d", &temp);
            Mux_Matrix[i][j] = temp;
        }
    }
    pcm->Mux_idx = new int* [MAX_DV_GLOBAL];
    for (int i = 0; i < MAX_DV_GLOBAL; i++) {
        pcm->Mux_idx[i] = new int[N_b];
        for (int j = 0; j < N_b; j++) {
            pcm->Mux_idx[i][j] = EMPTY;
        }
    }
    for (int j = 0; j < N_b; j++) {
        GT_rank = 0;
        for (int i = 0; i < M_b; i++) {
            if (EMPTY != Mux_Matrix[i][j]) {
                pcm->Mux_idx[GT_rank][j] = Mux_Matrix[i][j];
                GT_rank++;
            }
        }
    }
    /********************************************/
    // PCM memory allocation
    /********************************************/
    pcm->ar = new int[GT_HW_MAX_ROW];
    ar = new int[GT_HW_MAX_ROW];// 1: active, 0: non-active
    /* Active Row allocation */
    for (int i = 0; i < GT_HW_MAX_ROW; i++) {
        //ar[i] = 1;
        if (i < M_b)    ar[i] = 1;
        else            ar[i] = 0;
    }
    // 2021.02.01 GT rule 적용
    /*
    if (M_b == 20) {}
    else if (M_b == 19) { ar[19] = 0; }
    else if (M_b == 18) { ar[19] = 0; ar[18] = 0; }
    else if (M_b == 17) { ar[19] = 0; ar[18] = 0; ar[17] = 0; }
    else if (M_b == 16) { ar[19] = 0; ar[18] = 0; ar[17] = 0; ar[16] = 0; }
    else if (M_b == 15) { ar[19] = 0; ar[18] = 0; ar[17] = 0; ar[16] = 0;  ar[15] = 0; }
    else if (M_b == 14) { ar[19] = 0; ar[18] = 0; ar[17] = 0; ar[16] = 0; ar[15] = 0; ar[14] = 0; }
    else if (M_b == 13) { ar[19] = 0; ar[18] = 0; ar[17] = 0; ar[16] = 0; ar[15] = 0; ar[14] = 0; ar[13] = 0; }
    else if (M_b == 12) { ar[19] = 0; ar[18] = 0; ar[17] = 0; ar[16] = 0; ar[15] = 0; ar[14] = 0; ar[13] = 0; ar[12] = 0; }
    else if (M_b == 11) { ar[19] = 0; ar[18] = 0; ar[17] = 0; ar[16] = 0; ar[15] = 0; ar[14] = 0; ar[13] = 0; ar[12] = 0; ar[11] = 0; }
    else if (M_b == 10) { ar[19] = 0; ar[18] = 0; ar[17] = 0; ar[16] = 0; ar[15] = 0; ar[14] = 0; ar[13] = 0; ar[12] = 0; ar[11] = 0; ar[10] = 0; }
    else { printf("Cannot support this OH!!\n"); }
    */
    /* Copy */
    for (int i = 0; i < GT_HW_MAX_ROW; i++) {
        pcm->ar[i] = ar[i];
    }
    /**************************************/
    // PCM memory allocation
    /**************************************/
    pcm->PCM_GT = new int* [MAX_DV_GLOBAL];
    for (int i = 0; i < MAX_DV_GLOBAL; i++)    pcm->PCM_GT[i] = new int[N_b];
    PCM_GT = new int* [MAX_DV_GLOBAL];
    for (int i = 0; i < MAX_DV_GLOBAL; i++)    PCM_GT[i] = new int[N_b];
    for (int col_idx = 0; col_idx < N_b; col_idx++) {
        NB_flag = 0;
        for (int k = 0; k < MAX_DV_GLOBAL; k++) {
            GT_rank = 0;
            for (int i = 0; i < M_b; i++) {
                if (EMPTY != Mux_Matrix[i][col_idx] && k != Mux_Matrix[i][col_idx]) {
                    GT_rank++;
                }
                else if (k == Mux_Matrix[i][col_idx]) {
                    PCM_GT[k][col_idx] = GT_rank;
                    break;
                }
            }
            if (GT_rank >= pcm->ColW[col_idx]) {
                PCM_GT[k][col_idx] = pcm->ColW[col_idx] + NB_flag;
                NB_flag++;
            }
        }
    }
    /* Copy */
    for (int i = 0; i < MAX_DV_GLOBAL; i++) {
        for (int j = 0; j < N_b; j++) {
            pcm->PCM_GT[i][j] = PCM_GT[i][j];
        }
    }
    /* release temp */
    delete[] ar;
    for (int i = 0; i < MAX_DV_GLOBAL; i++) { delete[] PCM_GT[i]; }
    delete[] PCM_GT;
    for (int i = 0; i < M_b; i++) { delete[] Mux_Matrix[i]; }
    delete[] Mux_Matrix;
}
int Get_Sel_Signal_In_MUX(int* ar, int row_idx)
{
    int cnt = 0;
    for (int k = 0; k < row_idx; k++) {
        if (ar[k] == 1) {
            cnt++;
        }
    }
    return cnt;
}
int Get_Row_Index_In_MUX(int* ar, int row_num, int sel_signal)
{
    int cnt = 0;
    for (int k = 0; k < row_num; k++) {
        if (ar[k] == 1) {
            if (cnt == sel_signal) {
                return k;
            }
            cnt++;
        }
    }
    return 0;
}
int Get_Empty_Sel_Signal_In_MUX(int* ar, int sel_signal_default, int row_num, int* selected, int mux_name)
{
    int bRun = TRUE;
    int signal = sel_signal_default;
    int row_idx;
    while (TRUE == bRun) {
        row_idx = Get_Row_Index_In_MUX(ar, row_num, signal);
        if (TRUE == selected[row_idx]) {
            signal = signal - 1;
            if (signal < 0) {
                bRun = FALSE;
[NOT VISIBLE]
            }
        }
        else {
            bRun = FALSE;
        }
    }
    return signal;
}
//================================================
//
//================================================
void Release_GT(PCM* pcm)
{
    delete[] pcm->ar;
    for (int i = 0; i < MAX_DV_GLOBAL; i++) {
        delete[] pcm->PCM_GT[i];
    }
    delete[] pcm->PCM_GT;
    for (int i = 0; i < pcm->M_b; i++) {
        delete[] pcm->Mux_Matrix[i];
    }
    delete[] pcm->Mux_Matrix;
    for (int i = 0; i < MAX_DV_GLOBAL; i++) {
        delete[] pcm->Mux_idx[i];
    }
    delete[] pcm->Mux_idx;
}
