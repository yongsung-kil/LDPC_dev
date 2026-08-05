#include "random.h"

unsigned  int memory_for_rng_init[SEED_LEN] = {
    3701687786,  458299110, 2500872618, 3633119408,  516391518,
    2377269574, 2599949379,  717229868,  137866584,  395339113,
    1301295572, 1728310821, 3538670320, 1187274473, 2316753268,
    4061953237, 2129415220,  448488982,  643481932,  934407046,
    723553448, 3932869644,  449460396, 2728332712, 2381680799
};

unsigned  int memory_for_rng[SEED_LEN] = {
    3701687786,  458299110, 2500872618, 3633119408,  516391518,
    2377269574, 2599949379,  717229868,  137866584,  395339113,
    1301295572, 1728310821, 3538670320, 1187274473, 2316753268,
    4061953237, 2129415220,  448488982,  643481932,  934407046,
    723553448, 3932869644,  449460396, 2728332712, 2381680799
};

int seed_for_ran2;

//================================================
// Initialize xor25 with value "v"
//================================================
void Set_Random_Seed_xor25(int v)
{
    seed_for_ran2 = v;
    for (int n = 0; n < SEED_LEN; n++) {
        if (n == 0)
            memory_for_rng[n] = (unsigned int)(ran2(seed_for_ran2, 1) * 4294967295);
        else
            memory_for_rng[n] = (unsigned int)(ran2(seed_for_ran2, 0) * 4294967295);
    }
}

//================================================
// Set random state with "s"
//================================================
void Set_Random_Seed(unsigned int* s)
{
    for (int n = 0; n < SEED_LEN; n++) {
        memory_for_rng[n] = s[n];
    }
}

//================================================
// Get random state
//================================================
void Get_Random_Seed(unsigned int* s)
{
    for (int n = 0; n < SEED_LEN; n++) {
        s[n] = memory_for_rng[n];
    }
}

int Read_Uncor_Vector_Format(int N, FILE* fp_uncor_seed, int* uncor_input)
{
    int num_hex;
    int hex;
    char result = 0;
    int uncor_type = 0;
    int idx_bin = 0;
    int idx_hex = 0;
    int hex_per_line = TV_LINE_WIDTH_16;    // 16진 데이터 개수
    //int hex_per_line = TV_LINE_WIDTH_32;  // FPGA Seed to Data 변환용
    int bit_per_hex = 4;

    num_hex = N / bit_per_hex;
    while (1)
    {
        hex = getc(fp_uncor_seed);

        if (hex == EOF)
            return FALSE;

        if ((hex >= '0' && hex <= '9') || (hex >= 'a' && hex <= 'f') || (hex >= 'A' && hex <= 'F'))
            //if (hex != '\n')
        {
            Convert_Hex_Bin(hex, uncor_input + idx_bin);
            idx_hex++;
            idx_bin += 4;

            if (idx_hex % hex_per_line == 0)
                Reverse_Arr(uncor_input + idx_bin - hex_per_line * bit_per_hex, hex_per_line * bit_per_hex);
        }

        if (idx_hex >= num_hex) {
            Reverse_Arr(uncor_input + idx_bin - ((idx_hex % hex_per_line) * bit_per_hex), (idx_hex % hex_per_line) * bit_per_hex);
            break;
        }

    }

    return TRUE;
}

//================================================
// Convert binary to hex
//================================================
void Convert_Hex_Bin(char hex, int* arr)
{
    switch (hex)
    {
        case '0':
            arr[0] = 0; arr[1] = 0; arr[2] = 0; arr[3] = 0; break;
        case '1':
            arr[0] = 0; arr[1] = 0; arr[2] = 0; arr[3] = 1; break;
        case '2':
            arr[0] = 0; arr[1] = 0; arr[2] = 1; arr[3] = 0; break;
        case '3':
            arr[0] = 0; arr[1] = 0; arr[2] = 1; arr[3] = 1; break;
        case '4':
            arr[0] = 0; arr[1] = 1; arr[2] = 0; arr[3] = 0; break;
        case '5':
            arr[0] = 0; arr[1] = 1; arr[2] = 0; arr[3] = 1; break;
        case '6':
            arr[0] = 0; arr[1] = 1; arr[2] = 1; arr[3] = 0; break;
        case '7':
            arr[0] = 0; arr[1] = 1; arr[2] = 1; arr[3] = 1; break;
        case '8':
            arr[0] = 1; arr[1] = 0; arr[2] = 0; arr[3] = 0; break;
        case '9':
            arr[0] = 1; arr[1] = 0; arr[2] = 0; arr[3] = 1; break;
        case 'a':
            arr[0] = 1; arr[1] = 0; arr[2] = 1; arr[3] = 0; break;
        case 'b':
            arr[0] = 1; arr[1] = 0; arr[2] = 1; arr[3] = 1; break;
        case 'c':
            arr[0] = 1; arr[1] = 1; arr[2] = 0; arr[3] = 0; break;
        case 'd':
            arr[0] = 1; arr[1] = 1; arr[2] = 0; arr[3] = 1; break;
        case 'e':
            arr[0] = 1; arr[1] = 1; arr[2] = 1; arr[3] = 0; break;
        case 'f':
            arr[0] = 1; arr[1] = 1; arr[2] = 1; arr[3] = 1; break;
        case 'A':
            arr[0] = 1; arr[1] = 0; arr[2] = 1; arr[3] = 0; break;
        case 'B':
            arr[0] = 1; arr[1] = 0; arr[2] = 1; arr[3] = 1; break;
        case 'C':
            arr[0] = 1; arr[1] = 1; arr[2] = 0; arr[3] = 0; break;
        case 'D':
            arr[0] = 1; arr[1] = 1; arr[2] = 0; arr[3] = 1; break;
        case 'E':
            arr[0] = 1; arr[1] = 1; arr[2] = 1; arr[3] = 0; break;
        case 'F':
            arr[0] = 1; arr[1] = 1; arr[2] = 1; arr[3] = 1; break;
        default:
            printf("Invalid hexadecimal digit\n");
    }
}

void Reverse_Arr(int* arr, int num)
{
    int temp;
    for (int i = 0; i < num / 2; i++)
    {
        temp = arr[i];
        arr[i] = arr[num - i - 1];
        arr[num - i - 1] = temp;
    }
}

//================================================
// Read random state and copy to "current_seed"
// return FALSE if file pointer is
// at the end of file
//================================================
int Read_Seed(FILE* fp_uncor_seed, unsigned int* current_seed)
{
    int result = 0;
    int uncor_type = 0;
    result = fscanf(fp_uncor_seed, "%d", &uncor_type);
    if (result == EOF) {
        return FALSE;
    }

    for (int n = 0; n < SEED_LEN; n++) {
        fscanf(fp_uncor_seed, "%u", &current_seed[n]);
    }
    return TRUE;
}

//================================================
// Read random state
// return FALSE if file pointer is
// at the end of file
//================================================
int Read_Uncor_Seed_Format(FILE* fp_uncor_seed)
{
    int result = 0;
    int uncor_type = 0;
    unsigned int temp;
    result = fscanf(fp_uncor_seed, "%d", &uncor_type);
    if (result == EOF) {
        return FALSE;
    }

    for (int n = 0; n < SEED_LEN; n++) {
        fscanf(fp_uncor_seed, "%u", &temp);
    }
    return TRUE;
}

//================================================
// Print random state to file
//================================================
void Print_Seed(FILE* fp_uncor_seed, int uncor_type, char* filename_uncor_seed, unsigned int* current_seed)
{
    // 이벤트마다 fopen(append)/fclose 하던 것을 핸들 유지 + fflush로 교체 (파일 내용 동일)
    // SAVE_ALL_SEED 모드에서는 매 프레임 호출되므로 open/close 비용이 큼
    static FILE* fp_keep = NULL;
    static char last_name[512] = "";
    if ((fp_keep == NULL) || (strcmp(last_name, filename_uncor_seed) != 0)) {
        if (fp_keep != NULL) fclose(fp_keep);
        fp_keep = fopen(filename_uncor_seed, "a");
        strncpy(last_name, filename_uncor_seed, sizeof(last_name) - 1);
        last_name[sizeof(last_name) - 1] = '\0';
    }
    fprintf(fp_keep, "%d\t", uncor_type);
    for (int n = 0; n < SEED_LEN; n++) {
        fprintf(fp_keep, "%u\t", current_seed[n]);
    }
    fprintf(fp_keep, "\n");
    fflush(fp_keep);    // 크래시 시 유실 방지
}

//================================================
// Print init state to file
// For MODE_SEED_SAVE_UNCOR_SEED_LOAD_INIT_SEED
//================================================
#ifdef __AUTO_LLR_OPT__
void Print_Init_Seed(FILE* fp_uncor_seed, int uncor_type, char* filename_uncor_seed, unsigned int* current_seed)
{
    fp_uncor_seed = fopen(filename_uncor_seed, "w");
    fprintf(fp_uncor_seed, "%d\t", uncor_type);
    for (int n = 0; n < SEED_LEN; n++) {
        fprintf(fp_uncor_seed, "%u\t", current_seed[n]);
    }
    fprintf(fp_uncor_seed, "\n");
    fclose(fp_uncor_seed);
}

#endif
//================================================
// Get random
//================================================
double ran2(int seed_ran2, int reset)
{
    int j;
    long k;
    static long idum = 0;
    static long idum2 = 123456789;
    static long iy = 0;
    static long iv[NTAB];
    double temp;

    if (TRUE == reset) {
        idum = 0;
        idum2 = 123456789;
        iy = 0;
    }

    if (idum <= 0) {
        idum = seed_ran2;
        idum2 = idum;
        for (j = NTAB + 7; j >= 0; --j) {
            k = idum / IQ1;
            idum = IA1 * (idum - k * IQ1) - k * IR1;
            if (idum < 0) idum += IM1;
            if (j < NTAB) iv[j] = idum;
        }
        iy = iv[0];
    }

    k = idum / IQ1;
    idum = IA1 * (idum - k * IQ1) - k * IR1;
    if (idum < 0) idum += IM1;
    k = idum2 / IQ2;
    idum2 = IA2 * (idum2 - k * IQ2) - k * IR2;
    if (idum2 < 0) idum2 += IM2;
    j = iy / NDIV;
    iy = iv[j] - idum2;
    iv[j] = idum;
    if (iy < 1) iy += IMM1;
    if ((temp = AM * iy) > RNMX)    return RNMX;
    else                             return temp;
}

//================================================
// Get Gaussian (mean a,standard deviation d)
//================================================
double Gaussian_xor25(double a, double d)
{
    double static t = 0.0;
    double x, v1, v2, r;
    if (t == 0) {
        do {
            v1 = 2.0 * (xor_r25(memory_for_rng)) - 1.0;
            v2 = 2.0 * (xor_r25(memory_for_rng)) - 1.0;

            r = v1 * v1 + v2 * v2;

        } while (r >= 1.0);
        r = sqrt((-2.0 * log(r)) / r);
        t = v2 * r;
        return(a + v1 * r * d);
    }
    else
    {
        x = t;
        t = 0.0;
        return(a + x * d);
    }
}

//================================================
// Calculate xor25 (정수 경로 — 상태 갱신 + w 반환)
// 정수 소비처(rand_msg_xor25 등)의 double 왕복
// w → w/4294967295.0 → ×4294967295 → (unsigned) 제거용.
// 왕복은 전 범위(2^32) 전수 검증으로 항등 확인됨 → 값 동일 (5-6)
//================================================
unsigned int xor_r25_u32(unsigned int* a)
{
    unsigned int t = (a[18] ^ (a[18] << 5));
    unsigned int w = (t ^ (t >> 13)) ^ (a[0] ^ (a[0] << 20));
    memmove(a, a + 1, 24 * sizeof(unsigned int));    // 24회 원소별 이동 → 단일 블록 이동 (겹치는 영역이라 memmove)
    a[24] = w;
    return w;
}

//================================================
// Calculate xor25
//================================================
double xor_r25(unsigned int* a)
{
    // 실수 소비처(Gaussian_xor25)용 — 정수 경로 위에 나눗셈 1회 (기존과 동일 값)
    return xor_r25_u32(a) / (double)4294967295;
}

//================================================
// Generate random message
//================================================
void rand_msg_xor25(int* msg, int msglen)
{
    int i;
    unsigned int tmp;
    for (i = 0; i < msglen; i++) {
        tmp = xor_r25_u32(memory_for_rng);    // double 왕복 제거 — 전수 검증으로 동일 값 보장
        *(msg + i) = (int)(tmp % 2);
    }
}

//================================================
// Generate random error locator
// n_err_len : number of selected bits
//================================================
void rand_sel_ep(int* err_position, int len_max, int n_err_len, int type)
{
    int i, j, s;
    int temp;
    unsigned int tmp = 0;
    // 매 프레임 len_max(수만) identity 재초기화 대신, 직전 호출의 swap을 역순으로 되돌려 identity 복원.
    // 전제: 호출자는 반환 후 err_position을 읽기만 함 (외부에서 쓰면 복원이 깨짐).
    // 난수 소비 순서와 선택 결과는 기존과 완전 동일.
    static int* swap_hist = NULL;
    static int swap_cap = 0;
    static int swap_cnt = 0;
    static int* last_arr = NULL;
    static int last_len = 0;

    if (swap_cap < n_err_len) {
        delete[] swap_hist;
        swap_hist = new int[n_err_len];
        swap_cap = n_err_len;
    }
    if ((last_arr == err_position) && (last_len == len_max)) {
        /* 역순 복원: swap은 자기 역원이므로 역순 적용 시 identity로 복귀 */
        for (j = swap_cnt - 1; j >= 0; j--) {
            s = swap_hist[j];
            temp = err_position[j];
            err_position[j] = err_position[s];
            err_position[s] = temp;
        }
    }
    else {
        for (i = 0; i < len_max; i++) {
            err_position[i] = i;
        }
        last_arr = err_position;
        last_len = len_max;
    }
    swap_cnt = 0;

    for (j = 0; j < n_err_len; j++) {
        if (MODE_RANDOM_TYPE_SRAND == type) {
            tmp = (unsigned int)(rand() * rand());
        }
        else if (MODE_RANDOM_TYPE_XOR_25 == type) {
            tmp = xor_r25_u32(memory_for_rng);    // double 왕복 제거 — 전수 검증으로 동일 값 보장
        }
        s = (tmp % (len_max - j)) + j;
        swap_hist[j] = s;
        swap_cnt = j + 1;

        temp = err_position[j];
        err_position[j] = err_position[s];
        err_position[s] = temp;
    }
}

//================================================
// TV용 message 생성 함수
//================================================
void Make_Msg_TV(int* msg, int msglen, int input_index, int type)
{
    int n, i;
    if (MODE_RANDOM_TYPE_SRAND == type) {
        switch (input_index) {
            case 0:
                for (n = 0; n < msglen; n++) { msg[n] = rand() % 2; }
                break;
            case 1:
                for (n = 0; n < msglen; n++) { msg[n] = 1; }
                break;
            case 2:
                for (n = 0; n < msglen; n = n + 2) { msg[n] = 1;      msg[n + 1] = 0; }
                break;
            case 3:
                for (n = 0; n < msglen; n = n + 2) { msg[n] = 0;      msg[n + 1] = 1; }
                break;
            case 4:
                for (n = 0; n < msglen; n++) { msg[n] = rand() % 2; }
                break;
            case 5:
                for (n = 0; n < msglen; n = n + 16) {
                    if (n % 256 == 0) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 0; msg[n + i + 2] = 0; msg[n + i + 3] = 0; // 0
                        }
                    }
                    else if (n % 256 == 16) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 0; msg[n + i + 2] = 0; msg[n + i + 3] = 1; // 1
                        }
                    }
                    else if (n % 256 == 32) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 0; msg[n + i + 2] = 1; msg[n + i + 3] = 0; // 2
                        }
                    }
                    else if (n % 256 == 48) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 0; msg[n + i + 2] = 1; msg[n + i + 3] = 1; // 3
                        }
                    }
                    else if (n % 256 == 64) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 1; msg[n + i + 2] = 0; msg[n + i + 3] = 0; // 4
                        }
                    }
                    else if (n % 256 == 80) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 1; msg[n + i + 2] = 0; msg[n + i + 3] = 1; // 5
                        }
                    }
                    else if (n % 256 == 96) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 1; msg[n + i + 2] = 1; msg[n + i + 3] = 0; // 6
                        }
                    }
                    else if (n % 256 == 112) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 1; msg[n + i + 2] = 1; msg[n + i + 3] = 1; // 7
                        }
                    }
                    else if (n % 256 == 128) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 0; msg[n + i + 2] = 0; msg[n + i + 3] = 0; // 8
                        }
                    }
                    else if (n % 256 == 144) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 0; msg[n + i + 2] = 0; msg[n + i + 3] = 1; // 9
                        }
                    }
                    else if (n % 256 == 160) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 0; msg[n + i + 2] = 1; msg[n + i + 3] = 0; // A
                        }
                    }
                    else if (n % 256 == 176) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 0; msg[n + i + 2] = 1; msg[n + i + 3] = 1; // B
                        }
                    }
                    else if (n % 256 == 192) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 1; msg[n + i + 2] = 0; msg[n + i + 3] = 0; // C
                        }
                    }
                    else if (n % 256 == 208) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 1; msg[n + i + 2] = 0; msg[n + i + 3] = 1; // D
                        }
                    }
                    else if (n % 256 == 224) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 1; msg[n + i + 2] = 1; msg[n + i + 3] = 0; // E
                        }
                    }
                    else {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 1; msg[n + i + 2] = 1; msg[n + i + 3] = 1; // F
                        }
                    }
                }
                break;
            case 6:
                for (n = 0; n < msglen; n = n + 8) {
                    msg[n] = 0; msg[n + 1] = 1; msg[n + 2] = 0; msg[n + 3] = 1; msg[n + 4] = 1; msg[n + 5] = 0; msg[n + 6] = 1; msg[n + 7] = 0;
                }
                break;
            case 7:
                for (n = 0; n < msglen; n = n + 8) {
                    msg[n] = 1; msg[n + 1] = 0; msg[n + 2] = 1; msg[n + 3] = 0; msg[n + 4] = 0; msg[n + 5] = 1; msg[n + 6] = 0; msg[n + 7] = 1;
                }
                break;
            case 8:
            case 9:
                for (n = 0; n < msglen; n++) { msg[n] = rand() % 2; }
                break;
            case 10:
                for (n = 0; n < msglen; n++) { msg[n] = 0; }
                break;
            default:
                for (n = 0; n < msglen; n++) { msg[n] = rand() % 2; }
                break;
            }
        }
    else if (MODE_RANDOM_TYPE_XOR_25 == type) {
        switch (input_index) { //// Change
            case 0:
                rand_msg_xor25(msg, msglen);
            /*{
                for (n = 0; n < msglen; n++) { msg[n] = 0; }
                //msg[121 * 256] = 1;
                for (n = 0; n < 136; n++) {
                    for (int n2 = 128; n2 < 256; n2++) {
                        msg[n * 256 + n2] = 1;
                    }
                }
                for (n = 0; n < 256; n++) { msg[n] = 1; }
            }*/
                break;
            case 1:
                for (n = 0; n < msglen; n++) { msg[n] = 1; }
                break;
            case 2:
                for (n = 0; n < msglen; n = n + 2) { msg[n] = 1;      msg[n + 1] = 0; }
                break;
            case 3:
                for (n = 0; n < msglen; n = n + 2) { msg[n] = 0;      msg[n + 1] = 1; }
                break;
            case 4:
                rand_msg_xor25(msg, msglen);
                break;
            case 5:
                for (n = 0; n < msglen; n = n + 16) {
                    if (n % 256 == 0) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 0; msg[n + i + 2] = 0; msg[n + i + 3] = 0; // 0
                        }
                    }
                    else if (n % 256 == 16) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 0; msg[n + i + 2] = 0; msg[n + i + 3] = 1; // 1
                        }
                    }
                    else if (n % 256 == 32) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 0; msg[n + i + 2] = 1; msg[n + i + 3] = 0; // 2
                        }
                    }
                    else if (n % 256 == 48) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 0; msg[n + i + 2] = 1; msg[n + i + 3] = 1; // 3
                        }
                    }
                    else if (n % 256 == 64) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 1; msg[n + i + 2] = 0; msg[n + i + 3] = 0; // 4
                        }
                    }
                    else if (n % 256 == 80) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 1; msg[n + i + 2] = 0; msg[n + i + 3] = 1; // 5
                        }
                    }
                    else if (n % 256 == 96) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 1; msg[n + i + 2] = 1; msg[n + i + 3] = 0; // 6
                        }
                    }
                    else if (n % 256 == 112) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 0; msg[n + i + 1] = 1; msg[n + i + 2] = 1; msg[n + i + 3] = 1; // 7
                        }
                    }
                    else if (n % 256 == 128) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 0; msg[n + i + 2] = 0; msg[n + i + 3] = 0; // 8
                        }
                    }
                    else if (n % 256 == 144) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 0; msg[n + i + 2] = 0; msg[n + i + 3] = 1; // 9
                        }
                    }
                    else if (n % 256 == 160) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 0; msg[n + i + 2] = 1; msg[n + i + 3] = 0; // A
                        }
                    }
                    else if (n % 256 == 176) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 0; msg[n + i + 2] = 1; msg[n + i + 3] = 1; // B
                        }
                    }
                    else if (n % 256 == 192) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 1; msg[n + i + 2] = 0; msg[n + i + 3] = 0; // C
                        }
                    }
                    else if (n % 256 == 208) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 1; msg[n + i + 2] = 0; msg[n + i + 3] = 1; // D
                        }
                    }
                    else if (n % 256 == 224) {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 1; msg[n + i + 2] = 1; msg[n + i + 3] = 0; // E
                        }
                    }
                    else {
                        for (i = 0; i < 15; i = i + 4) {
                            msg[n + i] = 1; msg[n + i + 1] = 1; msg[n + i + 2] = 1; msg[n + i + 3] = 1; // F
                        }
                    }
                }
                break;
            case 6:
                for (n = 0; n < msglen; n = n + 8) {
                    msg[n] = 0; msg[n + 1] = 1; msg[n + 2] = 0; msg[n + 3] = 1; msg[n + 4] = 1; msg[n + 5] = 0; msg[n + 6] = 1; msg[n + 7] = 0;
                }
                break;
            case 7:
                for (n = 0; n < msglen; n = n + 8) {
                    msg[n] = 1; msg[n + 1] = 0; msg[n + 2] = 1; msg[n + 3] = 0; msg[n + 4] = 0; msg[n + 5] = 1; msg[n + 6] = 0; msg[n + 7] = 1;
                }
                break;
            case 8:
            case 9:
                rand_msg_xor25(msg, msglen);
                break;
            case 10:
                for (n = 0; n < msglen; n++) { msg[n] = 0; }
                break;
            default:
                rand_msg_xor25(msg, msglen);
                break;
            }
        }
}

unsigned char rand_int(void)
{
    unsigned int tmp = xor_r25_u32(memory_for_rng);    // double 왕복 제거 — 전수 검증으로 동일 값 보장
    tmp = tmp % 256;
    return (unsigned char)tmp;
}

