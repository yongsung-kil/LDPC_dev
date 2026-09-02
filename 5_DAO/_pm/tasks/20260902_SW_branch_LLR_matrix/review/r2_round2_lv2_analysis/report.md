# Round 2 결과: 분석 (lv2, 4팀)

작성: 2026-09-03 01:27:08
팀 요약: [team_P_summary.md](team_P_summary.md)(파일과 파서), [team_D_summary.md](team_D_summary.md)(디코더 분기 로직), [team_I_summary.md](team_I_summary.md)(iteration 번호 체계와 빌드 갈래), [team_C_summary.md](team_C_summary.md)(문서 정합과 규칙)
워커: P_1, P_2, P_3, D_1, D_2, D_3, I_1, I_2, I_3, I_4, C_1, C_2, C_3 (13개)

리뷰 대상은 코드가 아니라 코드 수정 계획 문서 두 개다. "코드 결함"은 code_diff.md의 수정 후 코드를 그대로 적용했을 때 생기는 결함, "문서 오류"는 서술 자체의 인용 불일치, 상충, 누락이다.

발견: 34건 (CRITICAL 1, HIGH 7, MEDIUM 17, LOW 9). 네 팀의 발견 가운데 같은 뿌리는 하나로 합쳤다.

## 발견 목록

| # | 심각도 | 문제 | 위치 | 지적 팀 |
|---|--------|------|------|--------|
| R2-1 | CRITICAL | 비AUTO 빌드에서 code_diff 8.1, 8.2가 `#else` 갈래를 지우면 `Is_Iter_Type_Edge_Clear`, `Is_Iter_Type_Init`이 미초기화 포인터 `m_param_LLR`을 매 iteration 역참조한다 (`ECC_Top` 생성자와 4인자 `Init_ECC_Top`이 이 포인터를 세우지 않고, 비AUTO 진입점 `main.cpp:105, 127`이 4인자를 부른다). 딸린 것: 비AUTO 2SD와 3SD의 restart 지점 8개(`common.h:679-686`)가 사라지고, TV Gen 빌드에서 `matrix_sel` 가드가 사라져 edge clear와 init 시점이 새로 생긴다. 저장소의 `mode.h` 그대로는 비AUTO TV Gen 빌드이므로 가정 위의 위험이 아니다 | code_diff 8.1, 8.2; `ecc_top.cpp:6-34, 197-210`, `decoder.cpp:436, 6567, 6627` | I (I_4 단독) |
| R2-2 | HIGH | `Clear_Flag`(`decoder.cpp:612-613`)가 code_diff 2.2에서 지우는 `flag_HD_1_4_Set`, `flag_HD_5_8_Set`에 대입한다. 수정 후 코드가 어느 장에도 없어 AUTO와 비AUTO 빌드 모두 컴파일되지 않는다. 지워지는 두 멤버의 참조 전수에서 code_diff가 다루지 않는 곳은 이 두 줄뿐이다 | code_diff 2.2, 9장 1단계 | D, C, I (세 팀 독립 일치) |
| R2-3 | HIGH | 구간(span) 번호의 뜻이 파서와 디코더에서 다르다. 3.2 파서는 분기 index가 0으로 되돌아온 등장 순서로 번호를 매기고, 2.2 주석, 4.1 문턱 배열, 5.1 `Select_BF`는 구간 0을 iteration 1~4, 구간 1을 5~8로 못박는다. 배경 메모 `msg1.md:31`의 예시(1~4 분기 없음, 5~8에 분기 셋)를 넣으면 5~8이 구간 0이 되어 BF 진입 프레임은 문턱 130으로 고르고 미진입 프레임은 분기 0 고정이 되며 분기 2는 영영 선택되지 않는다. 오류 출력 없음. `LLR_MATRIX_1.txt`는 두 구간 모두 분기가 있어 우연히 맞는다 | code_diff 3.2, 2.2, 4.1, 5.1; 상위 7장 ㉰ | P, D (세 워커 독립 일치) |
| R2-4 | HIGH | 9장 적용 순서가 어느 단계에서도 성립하지 않는다. ㉮ 1단계(1장, 2장)만 넣으면 지워지는 이름의 대체 코드가 3.3과 4.1에 흩어져 있어 `local_opt.cpp` 3줄과 `decoder.cpp` 8줄에서 빌드가 깨진다. ㉯ 3단계 전제 "`cur_sw_branch_idx[]`가 모두 0"이 거짓이다. 생성자(`Initialize_Dec`는 포인터만 NULL), `Clear_Flag`, 4.1 어디도 채우지 않고 채우는 곳은 5.1(4단계)뿐이다. ㉰ 0으로 채워도 3단계 검증 기준 "기존 동작과 결과가 같아야 한다"는 뒤집힌다. 옛 AUTO 루프는 iteration 1~4에 그룹 2, 5에 그룹 4, 6~8에 그룹 5를 잡고 새 루프는 분기 0 조건으로 그룹 0, 1, 3을 잡는다. 기준 문장이 정상 구현을 결함으로 판정하게 한다 | code_diff 9장 1~3단계, 6.1, 2.2 | D, C (독립 일치) |
| R2-5 | HIGH | `ITER_MAX_HBF`를 4로 하면 `local_opt.cpp:124-131`의 보정이 `MN[]`을 `[4, -3, -2, -1, 0, ..., 118, 120]`으로 만든다. 결과 파일의 iteration별 FER 열 1~3이 모든 프레임을 세어 1.0 고정이고 머리글에 음수가 찍힌다(`ecc_top.cpp:877-879, 2052-2056`). 실행 iteration이 124회에서 120회로 줄고 BF 진입 프레임은 파일의 121~124 row에 닿지 않는다. `iter_num -= ITER_MAX_HBF`(`decoder.cpp:1973-1979`)가 살아나 DAO가 읽는 `avg_iteration` 척도가 바뀐다. mn 0에서 끝나는 프레임은 `iter_num`이 -4가 된다(도달 가능성 미확정). 두 문서 어디에도 이 셈이 없다 | 상위 5.5; code_diff 1.2, 3.5 | I, P, C |
| R2-6 | HIGH | code_diff 3.2 표, 4.1, 5.1 ㉯, 6.1 표는 상위 4장 ㉮ 형태(type 전부 1, 분기 줄 추가)로 변환된 파일을 전제하는데 변환 절차와 변환된 파일이 어디에도 없다. 현재 `LLR_MATRIX_1.txt`를 3.2 파서에 넣으면 분기 줄이 restart 줄부터 읽혀 이후 헤더가 밀리고 row가 12토큰씩 어긋난다(6.2 ㉯ "여기서 걸린다"는 깨끗한 거부가 아니다). DAO 쪽은 형태(1)이 `Is_LLR_Valid` RW2에서 거부되고 형태(2)는 DAO 파서가 새 줄을 `num_restart`로 읽는다 | code_diff 3.2 표, 6.2 ㉯, 9장 2단계; 상위 4장 ㉮ | P, C (독립 일치) |
| R2-7 | HIGH | iteration 1~4 구간의 분기 존재와 문턱 130이 메모, 파일, code_diff에서 다르고 미결정에 없다. 메모는 1~4를 `1/4/-1`(분기 없음)로 적고, 파일은 분기 둘을 두며, 수정 전 코드는 `FLAG_HD_1_4_SET_TYPE_0`으로 못박고(`decoder.cpp:2090`) `TYPE_1`을 고르는 코드가 없다. `syn_th_BF1`(130)은 대입만 되고 읽는 곳이 없어 "준비해 둔 것"은 추정이다. syn_weight 130 이상 680 미만에서 그룹 2를 쓰는 것은 새 동작이다 | code_diff 2.2, 4.1, 5.1 ㉯; 상위 2장, 7장 | I, D (독립 일치) |
| R2-8 | HIGH | 3.4 대조 검사의 `err = TRUE`는 아무 효과가 없다(`local_opt.cpp:56`의 `err`는 140행 대입만 있고 읽는 곳 없음, 함수는 void). `printf`라 로그 파일에도 남지 않고, DAO는 `subprocess.run(check=True)`(`DAO_Main.py:7937`)로 stdout을 받지 않으며 `main.cpp:69`가 return 0 고정이라 종료 코드로도 알 수 없다. 어긋난 파일로 DAO 최적화가 그대로 진행된다 | code_diff 3.4; `local_opt.cpp:56, 139-141` | P |
| R2-9 | MEDIUM | 파일의 구간별 분기 개수와 컴파일 상수 `num_sw_branch[]`를 대조하지 않는다. 상위 4장 ㉮ "x는 읽는 쪽에서 센다"에 대응하는 코드가 없고 4.1 끝의 "대조하는 검사를 넣으면"은 제안 문장이다. default 갈래 `num_sw_branch[0] = 1`에 `LLR_MATRIX_1.txt`를 넣으면 그룹 2가 어떤 프레임에서도 선택되지 않고 오류도 없다(AUTO 빌드에서 `main.cpp:141-143`이 `argc > 19`이면 임의 `matrix_sel`을 받아 도달). 세 번째 구간, 상수보다 적은 분기, 문턱 누락(0이면 마지막 분기 고정), `num_sw_span > MAX_SW_SPAN` 미검사도 같은 뿌리다 | code_diff 4.1, 3.2, 6.1; 상위 4장 ㉮ | P, D, C (다섯 워커) |
| R2-10 | MEDIUM | 첫 분기 그룹의 index가 0이 아니면 3.2가 `sw_span_idx_each_group`을 -1로 쓰고 6.1이 `cur_sw_branch_idx[-1]`을 읽는다(정의되지 않은 동작). 구 파일 `Prime_ECC_2.4/.../LLR_MATRIX_0.txt`(분기 줄 `1 2 31`)가 실제 사례다. 분기 0 그룹이 같은 구간의 분기 1 그룹 뒤에 오면 새 구간으로 오인한다. 분기 불연속(`0 2`)과 `MAX_SW_BRANCH` 이상 검사가 없다 | code_diff 3.2, 6.1 | P, D |
| R2-11 | MEDIUM | "분기 일치를 넣으면 순서에 좌우되지 않는다"는 서술이 실제 범위를 넘는다. 후보 집합(현재 분기 그룹과 분기 없는 그룹) 안에서 iteration 범위가 겹치지 않을 때만 성립하고, 같은 분기 안 겹침이나 iteration 1~8을 통째로 덮는 분기 없는 그룹과 5~8 분기 그룹의 공존에서는 여전히 뒤쪽 그룹이 이긴다. 수정 전 AUTO 갈래와 같은 성질이라 새 결함은 아니다 | 상위 5.3-2; code_diff 6.1 ㉯ | D (D_1 단독) |
| R2-12 | MEDIUM | 상위 6.1이 "고쳐야 하는 곳"으로 든 `decoder.cpp:1137-1141`(`Get_Cur_LLR_Idx_FILE` 대 `Get_VNU_Table_Idx` 갈림)과 `6609-6626`(`Is_Iter_Type_Init`)에 수정 후 코드가 없다. `Get_Cur_LLR_Idx_FILE`을 부르는 곳은 1138 하나뿐이고 그 줄이 AUTO 안이라 이 함수의 비AUTO 갈래(`7001-7047`)는 실행되지 않는 코드다. 따라서 상위 5.3-4의 "`TYPE_1`이면 -1로 남는다"는 일어나지 않고 7장 ㉱ 미결정은 가독성 문제로 줄어든다 | 상위 6.1 표, 5.3-4, 7장 ㉱; code_diff 8.2 | I, C |
| R2-13 | MEDIUM | `ITER_MAX_HBF` 딸린 곳 표가 전수가 아니다. `decoder.cpp:2169`(`__DUAL_UPDATE__` 켜짐, AUTO에서 실제 실행)는 4로 바꾸면 iteration 5도 마지막 termination point에서만 종료해 `stop_by_partial_crc`와 throughput 지표 `overall_clk`이 바뀐다. 꺼진 스위치 안의 형제 5곳(1448, 1622, 1821, 1828, 2190)도 빠졌다. "12곳"은 표(11행, 14줄)와도 소스(활성 49줄)와도 맞지 않는다. `MN_size` 17곳과 564는 상쇄로 불변이고 `TV_Dec_Inter.cpp` 5곳은 TV 빌드와 AUTO가 배타라 영향 없음 | 상위 5.5 표; code_diff 1.2 | I, C |
| R2-14 | MEDIUM | 상위 6장 전수 목록에서 `m_log_CSW_auto` 네 블록(`decoder.cpp:7741-7743, 7773-7775, 7803-7805, 7928-7938`)이 빠졌고 "86"은 어느 셈으로도 재현되지 않는다(grep 히트 87) | 상위 6.3 | I, C |
| R2-15 | MEDIUM | code_diff 3.5가 `local_opt.cpp:124-131`(HD 보정 블록)을 다루지 않는다. 이 블록을 지우면 `MN[MN_num-1]`이 124로 남아 미진입 프레임이 mn 128까지 돌아 오류 경로로 빠지므로 살려야 한다. 블록 안 `MODE_DEC_1_SSD`(124행)는 저장소 어디에도 정의가 없는 기존 손상이며(정의된 이름은 `MODE_DEC_1_5SD`), 문서에 전제로 적어야 적용자가 헤매지 않는다 | code_diff 3.5; 상위 5.5 표 | I, C |
| R2-16 | MEDIUM | `ITER_MAX_HBF`가 4이면 BF 미진입 프레임은 mn 0에서 5로 건너뛰므로 파일의 `restart_iter`가 1~4에 있을 때 그 프레임만 restart edge clear를 놓친다. `LLR_MATRIX_1.txt`는 `restart_num`이 0이라 잠재 결함이다 | code_diff 8.1, 5.1; 상위 5.6 | D (리더 추가) |
| R2-17 | MEDIUM | 활성 SW 문턱 상수가 내림차순(`SET0` 1100 > `SET1` 950, default 960 > 950)이라 "문턱은 오름차순" 서술과 "SET1은 `[1][1]`에 들어간다" 문장이 성립하지 않는다. 분기 셋 이상이면 중간 분기가 영영 선택되지 않는다. 현재 분기 둘에서는 영향 없음 | code_diff 4.1, 5.1 | D, I |
| R2-18 | MEDIUM | BF가 살아나면 iteration 1~4에서도 파일 row가 쓰인다. `ch1`은 모든 column에, `th1~th7`은 `v_deg <= DV_5` column에 적용된다(`decoder.cpp:4019, 4056-4120`). 메모의 "bf라면 threshold를 받지 않아, -1"이 row의 분기 칸을 뜻하는지 th 칸을 뜻하는지 문서가 정하지 않았다 | 상위 2장, 5.5; code_diff 6.2, 7장 | I |
| R2-19 | MEDIUM | `iter_num -= ITER_MAX_HBF`는 `LAYOUT_PRIME_512B_TLC_VSS_OFF`에서만 걸려 layout별 통계 뜻이 갈리고, default layout에서는 histogram 색인이 495로 크기 480을 넘는다(`__PRINT_LOG_DATA__` 꺼짐이라 현재 미컴파일) | 상위 5.5; code_diff 1.2 | I |
| R2-20 | LOW | 5.1 Corner 이벤트가 HD와 1.5SD 갈래 밖으로 나와 2SD, 3SD에서도 찍히고 분기 index 3 이상이면 `IDX_FLAG_HD_FLOOR_TYPE_0`을 침범한다(`corner.h:78-86`, `Event_Flag`에 범위 검사 없음). `__CORNER_CHECKER__`는 꺼져 있다 | code_diff 5.1 | D, I, C |
| R2-21 | MEDIUM | 두 문서가 다른 결정을 말한다. ㉮ MPI: 상위 5.2-3 "함께 실어야 한다" 대 3.7 조건부. 판정은 각 rank가 파일을 따로 읽고(`local_opt.cpp:27-36` rank 조건 없음) `__RUN_MPI__`는 AUTO와 배타(`mode.h:21-25`)라 3.7 추가분은 컴파일되지 않으며 필요 없다. ㉯ 문턱 입력: 5.4-3 "파일이나 인자로 받아야" 대 전제 ㉰ "기존 상수". ㉰ 비AUTO 통일: 5.3-4 단정 대 7장 ㉱ 미결정인데 5.1, 6.1, 8.1, 8.2가 통일을 실행(Decision급 결정이 암묵적) | 상위 5.2-3, 5.4-3, 5.3-4, 7장; code_diff 3.7, 전제 | P, C |
| R2-22 | MEDIUM | 4단계 중간 상태(`ITER_MAX_HBF` 아직 0)의 판정 기준이 없고 5.1 주석 "iteration 1~4를 건너뛰므로 span 0은 쓰이지 않는다"는 5단계 이후에만 맞다 | code_diff 9장 4단계, 5.1 | C |
| R2-23 | MEDIUM | 변경 등급(Decision) 미표기, 태스크 양식의 안전성 체크리스트 절 부재, 변경 금지 대상(TV 출력 hex 포맷) 확인 기록 없음. 실제 TV 영향은 없다(TV 빌드와 AUTO 배타, TV 빌드의 `ITER_MAX_HBF`는 이미 4) | 상위 1장, 7장; TODO | C |
| R2-24 | MEDIUM | 8.3 Preprocessing 인용에 감싸는 `__RUN_PREPROCESSING__`(꺼짐)과 모드 조건 두 겹이 빠져 현재 구성에서 성립하지 않는 서술이다. 8.1 끝의 edge clear 지점 문장이 불완전하다(진입 프레임 0, 1, 5, 미진입 프레임 0, 5) | code_diff 8.1, 8.3; 상위 5.6 | D, I |
| R2-25 | MEDIUM | 구 포맷 파일 하위 호환 방침이 없고, 3.4 검사가 헤더와 row 일치만 보며 값 범위와 구간 안 연속성은 보지 않는다. 결과 로그(`local_opt.cpp:133-183`)에 새 헤더 줄 출력이 없다. `fopen` 실패 시 `fscanf(NULL)` 진행은 기존 결함 | code_diff 3장 | P |
| R2-26 | MEDIUM | CSW 로그(`m_log_CSW_auto`)에 프레임이 탄 분기 index가 남지 않고, BF가 살아나면 미진입 프레임의 자리 1~4가 -1로 남아 한 열에 -1과 실제 CSW가 섞인다 | 상위 6.3 | I |
| R2-27 | LOW | 인용 줄 범위 4건 수정 필요: `Select_BF` 5.4 `2084-2130`(갈래는 2084-2129, 함수는 2082-2130), `Get_Cur_LLR_Idx_FILE` 6.1 제목 `6973-6999`(인용은 7047까지)와 6.2 제목 `7048-7071`(7073이 맞음), `Is_Iter_Type_Init` 양쪽 표기(갈래 6609-6625, 함수 6606-6676), `Read_LLR_info_Auto` 5.1 `52-132`(함수는 52-184). 나머지 5건은 갈래와 함수의 차이라 둘 다 맞다 | 상위 5.1, 5.4, 5.6; code_diff 6.1, 6.2, 8.2 | C |
| R2-28 | LOW | 4.1 default 갈래가 원본에서 미초기화이던 `syn_th_BF0`을 630으로 확정한다. 개선이지만 동작 변경이고 전제 ㉰와 본문 어디에도 없다 | code_diff 4.1 | D, C, I |
| R2-29 | LOW | 6.2의 오류 반환 0이 정상 row 0과 구별되지 않고 호출자(`decoder.cpp:1136-1142`)가 검사하지 않는다. 2SD와 3SD가 분기 0으로 고정되는 동작이 5.1 바뀐 점에 없다 | code_diff 6.2, 5.1 | D |
| R2-30 | LOW | 이름 표에 `num_sw_span`, `Select_SW_Branch` 없음. `SW_BRANCH_NONE`이 "분기 없음"과 "구간 없음" 두 뜻. 상위 1장 대상 파일 목록에 수정 없는 `mode.h`, `ecc_top.cpp`가 있고 `corner.h`, `corner.cpp`가 없음. 1.1 앵커 미링크. 상위 5.2-1은 새 필드 1개, 2.1은 3개. 9장 1단계 "1장"이 1.2를 포함하는 것으로 읽힘. 5장 끝 enum 삭제의 적용 단계 없음. 상위 5.1-4 확인 결과 미기재(실제는 `local_opt.cpp:116, 120`뿐). 5.4-4가 `syn_th_BF0`도 배열화 대상으로 읽힘 | 두 문서 여러 곳 | C |
| R2-31 | LOW | 문서 규칙: 약어 첫 등장 풀어쓰기 누락 17건(BF, HD, MPI, VNU, C2V, V2C, VN, uncor, PCM, SW, 1.5SD, rank, span, Corner), 식별자 축약 4곳(`1_4_Set`, `5_8_Set`, `TYPE_0`, `TYPE_1`), 수정 후 주석 `(옛 floor_flag)`가 규칙 ㉮에 걸림, "지금" 표현 11곳, 작성 시각(23:13:58)이 파일 수정 시각(23:40)보다 이름. 금지 문자와 규칙 ㉲ 위반은 없음 | 두 문서 전체 | C |
| R2-32 | LOW | 기존 손상과 범위 밖: `__12META__` 갈래에 `SW_TH_BF0/BF1_512B_TLC_OFF` 없음(원본도 같음), `main.cpp:308`이 `SW_Threshold`로 630을 찍는데 실제 문턱은 680, `Mock_ECC.py:221-233` CSW 로그 형식이 실제와 이미 어긋남, `5_DAO/_pm/tasks/_template/README.md` 없음 | 여러 곳 | I, C |
| R2-33 | LOW | 분기(프레임 시작 SW)와 row 선택(직전 CSW)의 역할 구분이 한 곳에 없다. iteration 0은 row 0 고정이라 분기를 타지 않음을 미서술. `iter <= 4` 다섯째 히트(`decoder.cpp:7005`)는 비AUTO 갈래라 표의 넷과 성격이 다름 | 상위 3장, 5.3, 5.5 | I |
| R2-34 | LOW | 상위 5.6과 code_diff 8.2가 `Is_Iter_Type_Init`의 restart 처리를 각각 "확인 필요"와 "의도로 보인다"로 적고 미결정에 없다. 판정: 비AUTO 갈래도 HD와 1.5SD는 `iter == 0`만 보고 restart 레지스터 비우기는 `Clear_Edge_Restart`(`decoder.cpp:709-739`)가 맡으므로 의도가 맞다 | 상위 5.6; code_diff 8.2 | D, C |

### 통과 관점 (문제 미발견, 확인 범위)

- 관점 1 파일 해석: 상위 2장 표(그룹 12개, row 77개, 헤더 44토큰, CSW 나열, iteration 범위, 마지막 칸)와 읽는 규칙 ㉮~㉱, 4장 ㉮ 예시 헤더가 모두 `LLR_MATRIX_1.txt`와 손계산 일치 (P_1, C_1, I_1 독립 확인). 다만 `{x}{y}` 해석의 출처가 저장소에 없고 2장 ㉲ "상한 9"는 추론이다
- 관점 11 MPI: 각 rank가 파일을 따로 읽는 구조로 확정. `Run_Local_Opt`에 rank 조건 없음, `__RUN_MPI__`는 AUTO와 상호 배타, `mpi.cpp`는 스텁, DAO는 rank마다 단일 프로세스 EXE (P_2, C_2)
- 관점 13 호출 순서: syn_weight 확정(`decoder.cpp:3439-3444`) → `Select_BF`(1968-1970) → `Get_Cur_LLR_Idx_FILE`(1136-1142) 순서가 프레임 안에서 고정이고, 최종 상태에서는 `Select_BF`가 프레임마다 배열을 0으로 채워 프레임 간 누수가 없다 (D_3)
- 관점 9 구조체: `PARAM_LLR`은 포인터 한 줄로만 전달되고 값 복사, `memcpy`, `sizeof` 경로가 없어 중간 삽입이 안전하다. 4.1의 루프 변수 `i`는 함수 지역 선언이 있다 (D_2, D_3)
- 관점 14 인용: code_diff의 수정 전 블록 22개가 소스와 글자 단위로 일치한다 (C_1)
- 관점 17 규칙: 줄표, 가운뎃점과 유사 문자 9종 없음. 링크와 앵커 전부 동작. 규칙 ㉲(입력 파일 성격 서술 금지) 위반 없음 (C_3)
- 관점 6 일부: `MN_size` 17곳과 `decoder.cpp:564`는 `MN[MN_num-1]`이 4 줄고 `ITER_MAX_HBF`가 4 늘어 상쇄. `TV_Dec_Inter.cpp` 5곳은 TV 빌드와 AUTO가 배타라 TV 출력 시점과 포맷 모두 불변 (I_2)
- 관점 5 일부: 문턱 배열 구조, 1.5SD 등가성, span 1 동작 보존(BF 진입 조건 680이 문턱 1100보다 작아 분기 0), 미진입 프레임의 span 1 판정이 기존 `syn_weight < syn_th_5_8_Set_0`과 같은 결과 (D_2)

### 작성자 요청 7건 판정 (Round 2 기준)

| 요청 | 판정 |
|------|------|
| 1 파일 해석 | 표는 파일과 일치. `{x}{y}` 해석 출처와 "상한 9"는 저장소 밖 근거 |
| 2 6장 순서 독립성 | 부분 성립. 서로 다른 분기 사이 순서 의존은 해소. 구간 번호(R2-3, R2-10)와 같은 후보 집합 안 iteration 겹침(R2-11)은 여전히 순서에 좌우 |
| 3 3.2 구간 번호 반례 | 반례 있음. 첫 분기 그룹 index가 0이 아닌 파일(구 파일이 실제 사례), 분기가 한 구간에만 있는 파일(메모 예시), 구간 5개 이상, 분기 불연속 (R2-3, R2-10) |
| 4 Select_BF 변경 타당성 | 조건부 타당. 구조와 등가성은 확인. 문턱 130 채택과 1~4 분기 존재의 Decision(R2-7), 구간 정의 통일(R2-3), 오름차순 서술 수정(R2-17), 분기 수 대조(R2-9) 네 조건 |
| 5 ITER_MAX_HBF 12곳 누락 | 누락 있음. AUTO에서 실제 실행되는 `decoder.cpp:2169` 한 곳, 꺼진 스위치 안 5곳, 표에 있으나 결과 파괴를 다루지 않은 `local_opt.cpp:126-130`. "12"는 어느 셈과도 불일치 (R2-13, R2-5) |
| 6 `__AUTO_LLR_OPT__` 분류 | 한 곳 조건부 오분류(`ecc_top.cpp:652, 680, 944-950` 결과 출력이 R2-5로 깨짐). `m_log_CSW_auto` 4블록 누락. 나머지 6.3 항목은 분류가 맞음 (R2-14) |
| 7 MPI 구조 | 각 rank가 파일을 따로 읽음. 3.7 Bcast 추가는 컴파일되지 않으며 불필요. 상위 5.2-3 단정을 "필요 없다"로 고쳐야 함 (R2-21 ㉮) |

## 다음 단계 결정

→ Round 3 (lv2, 검증 3팀 + 재탐색 1팀) 진행
  사유: CRITICAL 1건과 HIGH 7건이 있고, R2-1(비AUTO 갈래 유지)과 R2-3, R2-9(처방 두 갈래), R2-5(처방 세 갈래)는 처방이 계획의 방향이나 동작 변경을 요구한다. R2-1, R2-11, R2-16은 단일 워커 또는 리더 단독 발견이다. R2-5의 mn 0 종료 도달 가능성은 재현 조건이 미확정이다.

검증 대상 선별과 팀 배분은 [../r3_round3_lv2_verification/context.md](../r3_round3_lv2_verification/context.md)에 있다.
