#include "full_CRC.h"
/* generator polynomial */
int CRC80_BCH_PLY[CRC_LEN] = { 0,0,1,1,0,0,1,0,0,0,0,0,1,1,1,1,0,1,1,1,0,1,0,1,0,1,0,0,0,0,1,0,1,1,0,1,1,0,0,1,0,0,1,0,0,1,1,0,0,1,0,0,0,1,0,1,1,1,0,0,1,0,0,1,0,0,1,0,1,0,0,0,0,1,1,1,
int CRC80_INIT[CRC_LEN] = { 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
//=============================================
// CRC check
//=============================================
void CRC_decoder(int *codeword, int number_of_code_block, int *success_flag, int *CRC_dec_LFSR_final, int ShortenedBit)
{
	int i, j, k;
	int N_CWD;
	int N_CWD_4K;
	int chk;
	N_CWD = number_of_code_block;
	N_CWD_4K = N_CWD * 4;
	int **msg;
	int *crc_dec;
	int *crc_par;
	msg = new int*[N_CWD_4K];
	for (i = 0; i < N_CWD_4K; i++) {
		msg[i] = new int[ZSB_CRC];
	}
	crc_dec = new int[CRC_LEN];
	crc_par = new int[CRC_LEN];
	for (j = 0; j < CRC_LEN; j++) {
		if (ShortenedBit == 0) {
			crc_par[j] = codeword[(N_CWD_4K - 1) * ZSB_CRC - 16 + j];
		}
	}
	k = 0;
	for (i = 0; i < N_CWD_4K; i++) {
		for (j = 0; j < ZSB_CRC; j++) {
			if (ShortenedBit == 0) {
				if (k < 80)		msg[i][j] = 0;
				else				msg[i][j] = codeword[k - 80];
			}
			k++;
		}
	}
	GEN_CRC80(crc_dec, CRC80_BCH_PLY, CRC80_INIT, msg, N_CWD_4K, ZSB_CRC);
	chk = 0;
	for (i = 0; i < CRC_LEN; i++) {
		if (crc_par[i] != crc_dec[i]) {
			chk++;
		}
		CRC_dec_LFSR_final[i] = crc_dec[i];
	}
	if (chk == 0) success_flag[0] = 0;
	else			success_flag[0] = 1;
	for (i = 0; i < N_CWD_4K; i++) {
		delete[] msg[i];
	}
	delete[] msg;
	delete[] crc_dec;
	delete[] crc_par;
}
//=============================================
// CRC check
//=============================================
void CRC_decoder(int *codeword, int number_of_code_block, int *success_flag, int *CRC_dec_LFSR_final, int **CRC_dec_LFSR_internal, int ShortenedBit)
{
	int i, j, k;
	int N_CWD;
	int N_CWD_4K;
	int chk;
	N_CWD = number_of_code_block;
	N_CWD_4K = N_CWD * 4;
	int** msg;
	int* crc_dec;
	int* crc_par;
	msg = new int* [N_CWD_4K];
	for (i = 0; i < N_CWD_4K; i++) {
		msg[i] = new int[ZSB_CRC];
	}
	crc_dec = new int[CRC_LEN];
	crc_par = new int[CRC_LEN];
	int** crc_dec_internal;
	crc_dec_internal = new int* [N_CWD_4K];
	for (i = 0;i < N_CWD_4K;i++) crc_dec_internal[i] = new int[CRC_LEN];
	for (i = 0;i < N_CWD_4K;i++) Init_Buf(crc_dec_internal[i], CRC_LEN);
	for (j = 0; j < CRC_LEN; j++) {
		if (ShortenedBit == 0) {
			crc_par[j] = codeword[(N_CWD_4K - 1) * ZSB_CRC - 16 + j];
		}
	}
	k = 0;
	for (i = 0; i < N_CWD_4K; i++) {
		for (j = 0; j < ZSB_CRC; j++) {
			if (ShortenedBit == 0) {
				if (k < 80)		msg[i][j] = 0;
				else				msg[i][j] = codeword[k - 80];
			}
			k++;
		}
	}
	GEN_CRC80(crc_dec_internal, crc_dec, CRC80_BCH_PLY, CRC80_INIT, msg, N_CWD_4K, ZSB_CRC);
	chk = 0;
	for (i = 0; i < CRC_LEN; i++) {
		if (crc_par[i] != crc_dec[i]) {
			chk++;
		}
		CRC_dec_LFSR_final[i] = crc_dec[i];
	}
	for (i = 0; i < N_CWD_4K; i++) {
		for (j = 0;j < CRC_LEN;j++) {
			CRC_dec_LFSR_internal[i][j] = crc_dec_internal[i][j];
		}
	}
	if (chk == 0) success_flag[0] = 0;
	else			success_flag[0] = 1;
	for (i = 0; i < N_CWD_4K; i++) {
		delete[] msg[i];
		delete[] crc_dec_internal[i];
	}
	delete[] msg;
	delete[] crc_dec;
	delete[] crc_par;
	delete[] crc_dec_internal;
}
//=============================================
// Generate CRC parity
//=============================================
void CRC_encoder(int *user_data, int number_of_info_block, int ShortenedBit)
{
	int i, j, k;
	int N_MSG;
	int N_MSG_4K;
	N_MSG = number_of_info_block;
	N_MSG_4K = N_MSG * 4;
	int **msg;
	int *crc;
	msg = new int*[N_MSG_4K];
	for (i = 0; i < N_MSG_4K; i++) {
		msg[i] = new int[ZSB_CRC];
	}
	crc = new int[CRC_LEN];
	k = 0;
	for (i = 0; i < N_MSG_4K; i++) {
		for (j = 0; j < ZSB_CRC; j++) {
			if (ShortenedBit == 0) {
				if (k < 80)		msg[i][j] = 0;
				else				msg[i][j] = user_data[k - 80];
			}
			k++;
		}
	}
	GEN_CRC80(crc, CRC80_BCH_PLY, CRC80_INIT, msg, N_MSG_4K, ZSB_CRC);
	for (i = 0; i < CRC_LEN; i++) {
		if (ShortenedBit == 0) {
			user_data[i + (N_MSG_4K - 1) * ZSB_CRC - 16] = crc[i];
		}
	}
	for (i = 0; i < N_MSG_4K; i++) {
		delete[] msg[i];
	}
	delete[] msg;
	delete[] crc;
}
//=============================================
// CRC 80 gnerator
//=============================================
void GEN_CRC80(int *crc80, int *crc80_ply, int *crc80_init, int **msg, int n_msg, int zsb) {
	memcpy(crc80, crc80_init, sizeof(int) * CRC_LEN);
	for (int i = 0; i < n_msg; i++) for (int j = 0; j < zsb; j++) CRC_LFSR(crc80, msg[i][j], crc80_ply, CRC_LEN);
}
//=============================================
// CRC 80 gnerator: internal TV generation
//=============================================
void GEN_CRC80(int** crc80_internal, int* crc80, int* crc80_ply, int* crc80_init, int** msg, int n_msg, int zsb) {
	memcpy(crc80, crc80_init, sizeof(int) * CRC_LEN);
	for (int i = 0; i < n_msg; i++) {
	    for (int j = 0; j < zsb; j++) { CRC_LFSR(crc80, msg[i][j], crc80_ply, CRC_LEN); }
	    memcpy(crc80_internal[i], crc80, sizeof(int) * CRC_LEN);
	}
}
//=============================================
// CRC 1-bit Generator (Linear Feedback Shift Register)
// crc(out): CRC value
// crc_ply:  CRC generate polynomial
// n_ply:    CRC size
//=============================================
void CRC_LFSR(int *crc, int m, int *crc_ply, int n_ply) {
	int crc_tmp = crc[0];
	for (int i = 0; i < n_ply - 1; i++) {
	    crc[i] = crc[i + 1];
	    if (crc_ply[i] == 1) crc[i] ^= (crc_tmp ^ m);
	}
	crc[n_ply - 1] = m ^ crc_tmp;
}
