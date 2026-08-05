#ifndef ECCTG_LOCAL_OPT_H
#define ECCTG_LOCAL_OPT_H

#include "common.h"
#include "ecc_data.h"
#include "Decoder.h"
#include "Encoder.h"
#include "full_CRC.h"
#include "partial_CRC.h"
#include "random.h"
#include "input.h"
#include "GT.h"
#include "ECC_Top.h"

class LOCAL_OPT
{
public:
    LOCAL_OPT();
    ~LOCAL_OPT();

    void    Run_Local_Opt(PARAM_REF_C * p_ref_c, ECC_INFO* ecc_info, PARAM_DEC * param_dec, int myrank, int num_process, int signal);
private:
    void    Read_LLR_info_Auto(PARAM_LLR* LLR_info, PARAM_OPT* OPT_info);
    void    Run_Simu_Curr_LLR();

private:
    int         m_my_rank;
    int         m_num_process;
    ECC_Top*    g_pECC;
    PARAM_LLR   m_param_LLR;
    PARAM_OPT   m_param_OPT;
    PARAM_REF_C*    m_ref_c;
    PARAM_DEC*      m_param_dec;
    ECC_INFO*       m_ecc_info;
};

#endif
