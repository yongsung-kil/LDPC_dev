#ifndef __CORNER_H__
#define __CORNER_H__

#include "common.h"
#include "ecc_data.h"

/*
    Corner Case Checker
    IP: Prime ECC 1.3
    CTRL: Deneb, Piccolo
    @20180712

    HW IO description
*/

class CornerChecker
{
public:
    CornerChecker();
    ~CornerChecker();
public:
    void Set_Param(ECC_INFO* ecc_info, PARAM_DEC* param, int scenario);
    void Event_Flag(int index);
    void Event_LLR(int index);
    void Event_Power_Stopping(int col_index);
    void Event_Result(int uncor, int itr, int err_cnt);
    int Update(CornerChecker* sector);
    void Print(int all, char* buf);
    void Print_Head(int all);
    int Open_File(char* buf);
    void Close_File();
    void Clear(int all);

private:
    void Init();
    void Set_Parameters();
private:
    int* m_input;
    int* m_dec_i;
    int* m_flag;
    int* m_result;
    int* m_llr;
    int*  m_power_stopping_col_idx;   // 2022.01.26 PrimQ
    int  m_flag_update;

    ECC_INFO* m_ecc_info;
    PARAM_DEC* m_param_dec;
    int m_scenario;
    FILE* m_fp;

public:
    enum {
        IDX_I_CODE_RATE = 0,
        IDX_I_META,
        IDX_I_MSG_INVERT,
        IDX_I_LEN
    };

    enum {
        IDX_DEC_I_PRIME_MODE = 0,
        IDX_DEC_I_DEC_MODE,
        IDX_DEC_I_MAX_ITR,
        IDX_DEC_I_HD_STOP_IDX,
        IDX_DEC_I_SD_STOP_IDX,
        IDX_DEC_I_CRC_SEL, //0: partial crc 0, 1: full crc
        IDX_DEC_I_LEN
    };

    enum {
        IDX_FLAG_POWER_STOPPING = 0,
        IDX_FLAG_JUMP,
        IDX_FLAG_IDLE_CYCLE,
        IDX_FLAG_PCRC_POINT_0,
        IDX_FLAG_PCRC_POINT_1,
        IDX_FLAG_PCRC_POINT_2,
        IDX_FLAG_PCRC_POINT_3,
        IDX_FLAG_FULL_CRC,
        IDX_FLAG_HBF_ON,
        IDX_FLAG_HD_5_8_SET_TYPE_0,
        IDX_FLAG_HD_5_8_SET_TYPE_1,
        IDX_FLAG_HD_5_8_SET_TYPE_2,
        IDX_FLAG_HD_FLOOR_TYPE_0,
        IDX_FLAG_HD_FLOOR_TYPE_1,
        IDX_FLAG_HD_FLOOR_TYPE_2,
        IDX_FLAG_HD_FLOOR_TYPE_3,
        IDX_FLAG_LEN
    };

    enum {
        IDX_RESULT_UNCOR,       //0: cor, 1: uncor
        IDX_RESULT_ITERATION,   //
        IDX_RESULT_ERR_CNT,
        IDX_RESULT_LEN
    };

    int IDX_LLR_LEN;
    int IDX_POWER_STOPPING_COL_IDX_LEN;
};

#endif
