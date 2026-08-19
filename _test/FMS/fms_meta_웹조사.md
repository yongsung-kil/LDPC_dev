# 관련 웹 자료 정리: FDP와 Meta의 QLC 전략

해설: [fms_meta_해설.md](fms_meta_해설.md) | 원문: [fms_meta.md](fms_meta.md)

조사 시각 기준: 2026-08-19

---

## 1. FDP 표준의 정체

- ㉮ FDP는 NVMe 표준 제안 TP4146 으로 비준되었고 NVM Express 2.1 개정판에 반영되었습니다
- ㉯ Meta, Google, Samsung 이 공동으로 추진했고 표준화에 약 6개월이 걸렸습니다
- ㉰ OCP(Open Compute Project) 데이터센터 NVMe SSD 규격 2.5 판에 포함되어, 하이퍼스케일 조달
  요구사항에 들어갔습니다

### 표준이 정의하는 구조

| 이름 | 뜻 |
|------|-----|
| Reclaim Unit (RU, 회수 단위) | 다른 회수 단위를 건드리지 않고 통째로 지우고 재사용할 수 있는 물리 저장 영역입니다. 논리 주소(LBA)와는 무관한 순수 물리 개념이며, 발표 슬라이드의 "슈퍼블록"에 해당합니다 |
| Reclaim Group (RG, 회수 그룹) | 회수 단위 여러 개를 묶은 집합입니다 |
| Reclaim Unit Handle (RUH, 회수 단위 손잡이) | 각 회수 그룹 안의 회수 단위 하나를 가리키는 컨트롤러 자원입니다. 호스트가 "여기에 이어 써라"라고 지목하는 대상입니다 |
| Placement Handle (배치 손잡이) | 네임스페이스 범위에서 RUH 를 가리키는 이름입니다 |
| Placement Identifier (PID, 배치 식별자) | 회수 그룹 식별자와 배치 손잡이의 쌍입니다. 쓰기 명령에 이것을 실어 보내면 그 데이터가 어느 회수 단위로 갈지가 정해집니다. 발표 슬라이드에서 Hot, Warm, Cold 를 PID 로 쓴다고 한 것이 이것입니다 |

즉 슬라이드의 "수명 힌트"는 표준 용어로는 쓰기 명령에 붙는 배치 식별자이고, "격리된 슈퍼블록"은
회수 단위입니다.

## 2. 이전 세대 기술과의 차이

| 기술 | 호스트가 지는 부담 | 생태계 영향 |
|------|--------------------|-------------|
| Open-Channel SSD | 호스트가 물리 블록 관리와 마모 평준화까지 전부 담당 | 응용과 파일 시스템을 전면 재작성해야 함 |
| NVMe Streams | 스트림 번호로 데이터를 분리 | 구현 편차가 크고 보증이 약해 널리 자리 잡지 못함 |
| ZNS (Zoned Namespace) | 존 단위 순차 쓰기 규칙을 호스트가 지켜야 함 | 파일 시스템과 응용 수정 폭이 큼 |
| FDP | 쓰기에 힌트만 붙임. 물리 배치와 마모 평준화는 SSD가 계속 담당 | 기존 스택을 유지한 채 점진 도입 가능 |

업계 설명에서는 FDP를 "호스트와 장치 협력의 첫 80% 를 노린 기술"로 표현합니다. 나머지 20% 를
포기하는 대신 도입 비용을 크게 낮춘 절충입니다. 발표 슬라이드의 "힌트를 꺼도 10% 개선" 결과도 이
성질에서 나옵니다. FDP 드라이브는 호스트가 협력하지 않아도 기본 동작이 망가지지 않습니다.

## 3. Meta 쪽 자료가 말하는 QLC 전략

### 3.1 Meta 엔지니어링 블로그, "A case for QLC SSDs in the data center" (2025-03-04)

- ㉮ 하드디스크는 용량이 커질수록 TB 당 대역폭이 계속 떨어지고 있습니다. 그래서 뜨거운 데이터를
  TLC 플래시로 올리거나 용량을 과다 배치해야 하는 문제가 생깁니다
- ㉯ QLC 플래시는 TB 당 10 MB/s 수준의 성능을 요구하는 워크로드를 감당하는 자리, 즉 하드디스크와
  TLC SSD 사이의 빈 구간을 노립니다. 슬라이드의 R + 4W ≤ 32 예산선이 바로 이 자리의 수치 표현입니다
- ㉰ **QLC 드라이브는 읽기 처리량이 쓰기 처리량의 4배 이상일 수 있습니다.** 슬라이드의
  "Writes are 4x costlier" 와 계수 4 의 근거가 이 문장입니다
- ㉱ 대상 워크로드는 읽기 대역폭 위주이고 쓰기 요구가 드물고 적은 종류입니다. 낸드 전력 소비의
  대부분이 쓰기에서 나오므로 이 선택은 전력에도 유리합니다
- ㉲ 밀도 목표는 현재 출하 중인 가장 조밀한 TLC 서버의 6배입니다

### 3.2 MSST 2025 기조연설, Ross Stenfort (Meta), "QLC in the Real World"

- 이번 FMS 발표와 같은 흐름의 자료입니다. 원문은 PDF 슬라이드 이미지라 자동 텍스트 추출이 되지
  않았으므로, 수치가 필요하면 직접 열람이 필요합니다

### 3.3 EuroSys 2025 논문, "Towards Efficient Flash Caches with Emerging NVMe Flexible Data Placement SSDs"

- ㉮ 대상은 CacheLib 입니다. Meta 생태계에서 널리 쓰이는 오픈소스 플래시 캐시입니다
- ㉯ Meta 와 Twitter 의 실제 운영 트레이스로 평가했습니다
- ㉰ FDP 기본 기능으로 데이터 배치를 조정해 **장치 쓰기 증폭 약 1.0** 을 달성했습니다. 다른 지표의
  손해는 거의 없었습니다
- ㉱ 캐시 적중률을 해치지 않으면서 SSD 활용률을 올렸고, 탄소 배출과 전력 소비도 함께 줄었습니다
- ㉲ 이번 슬라이드가 저장 서비스 관점의 결과라면 이 논문은 캐시 관점의 결과입니다. 서로 다른
  워크로드에서 같은 결론(수명 분리가 쓰기 증폭을 없앤다)이 재현되었다는 점이 의미 있습니다

## 4. 드라이브 업체 쪽 수치

- ㉮ Kioxia XD8 시리즈 자료: FDP를 끄면 쓰기 증폭이 3을 조금 넘는 값으로 점근하지만, FDP를 켜면
  1 근처가 가능하다고 제시합니다. 호스트 쓰기 1 회당 낸드 쓰기 3 회가 1 회로 줄어드는 셈입니다
- ㉯ Samsung, FADU, Silicon Motion(MonTitan Gen5 플랫폼), DapuStor 등이 FDP 지원 제품과 시연을
  내놓았습니다. 특정 업체 전용 기능이 아니라 조달 가능한 표준 기능이 되었다는 뜻입니다
- ㉰ 업체 자료의 개선폭(3 에서 1)이 이번 Meta 슬라이드의 개선폭(1.8 에서 1.1)보다 큽니다. 업체
  수치는 임의 쓰기 위주의 불리한 기준선을 쓰는 경우가 많고, Meta 실험은 1 MB 에서 8 MB 큰 블록
  쓰기라 기준선 자체가 이미 좋습니다. 두 숫자를 직접 비교하면 안 됩니다

## 5. 리눅스 지원 현황

LWN 기사 기준으로 정리하면 다음과 같습니다.

- ㉮ 배치 식별자는 16비트 태그이지만 실제 하드웨어가 지원하는 개수는 8개에서 수백 개 수준입니다.
  한 장치를 여러 파일 시스템과 응용이 나눠 쓰므로 태그는 아껴 써야 하는 자원입니다. 슬라이드의
  "버킷 개수 튜닝" 과제가 바로 이 제약과 맞물립니다
- ㉯ 초기 지원은 Linux 6.2 에서 들어갔습니다
- ㉰ 다만 커널 전반에 배선되지는 않았습니다. 현재는 NVMe 명령 통과 인터페이스와 io_uring 의
  write-stream 명령으로 직접 입출력 경로에서만 쓸 수 있습니다
- ㉱ 파일 시스템이 iomap 계층을 통해 힌트를 전달하는 문제는 아직 미해결입니다. 즉 지금 FDP의
  이득을 보려면 응용이 직접 입출력 경로를 다뤄야 합니다. Meta 처럼 저장 엔진을 직접 만드는 곳이
  먼저 이득을 보는 이유입니다
- ㉲ 사용자 공간 쪽은 xNVMe, SPDK, CacheLib 에 구현이 있습니다

## 6. 정리

- ㉮ 이번 발표의 위치: Meta 는 이미 QLC 도입을 결정했고(2025년 3월 블로그), 그 QLC의 최대 약점인
  쓰기 대역폭을 FDP로 메우는 단계에 있습니다. FMS 발표는 그 중간 실측 보고입니다
- ㉯ 검증된 것: TLC 드라이브에서 수명 분리로 WAF 1.8 에서 1.1 달성, 용량 쏠림 없음, 힌트 없이도
  10% 개선
- ㉰ 아직 열린 것: QLC 실기 검증(예비치 10% 에서 15%), 수명 버킷 개수 최적화, 파일 시스템 계층의
  일반적 지원

---

## 출처

- [Flexible data placement (LWN.net)](https://lwn.net/Articles/1018642/)
- [Towards Efficient Flash Caches with Emerging NVMe Flexible Data Placement SSDs (arXiv 2503.11665, EuroSys 2025)](https://arxiv.org/abs/2503.11665)
- [ACM DL: EuroSys 2025 논문 페이지](https://dl.acm.org/doi/10.1145/3689031.3696091)
- [A case for QLC SSDs in the data center (Engineering at Meta)](https://engineering.fb.com/2025/03/04/data-center-engineering/a-case-for-qlc-ssds-in-the-data-center/)
- [Ross Stenfort, QLC in the Real World (MSST 2025 Keynote, PDF)](https://msstconference.org/MSST-history/2025/Presentations/Day%203%20(September%2024th)/Keynote/MSST_QLC_Keynote_V5.pdf)
- [What Hyperscalers Need to Know About Flexible Data Placement (Samsung Semiconductor)](https://semiconductor.samsung.com/news-events/tech-blog/what-hyperscalers-need-to-know-about-flexible-data-placement-fdp/)
- [Hyperscalers Embrace Flexible Data Placement (FDP) to Increase Performance and Lower TCO (Samsung Semiconductor)](https://semiconductor.samsung.com/news-events/tech-blog/hyperscalers-embrace-flexible-data-placement-fdp-to-increase-performance-and-lower-tco/)
- [KIOXIA XD8 FDP Performance Brief (PDF)](https://americas.kioxia.com/content/dam/kioxia/en-us/business/ssd/data-center-ssd/asset/KIOXIA_XD8_FDP_Performance_Brief.pdf)
- [Hyperscale Innovation: Flexible Data Placement Mode (FDP) (NVM Express, PDF)](https://nvmexpress.org/wp-content/uploads/Hyperscale-Innovation-Flexible-Data-Placement-Mode-FDP.pdf)
- [Changes in NVM Express Specifications, Revision 2.1 (PDF)](https://nvmexpress.org/wp-content/uploads/NVM-Express-Revision-2.1-Changes-09_05_24.pdf)
- [Flexible Data Placement (xNVMe 문서)](https://xnvme.io/tutorial/fdp/index.html)
- [Maximizing Storage Efficiency while Minimizing Cost with FDP (FADU)](https://blogs.fadu.io/flexible-data-placement-reducing-write-amplification/)
- [Meta Makes the Case for QLC SSDs in the Data Center (StorageReview)](https://www.storagereview.com/news/meta-makes-the-case-for-qlc-ssds-in-the-data-center)
