# Improving QLC write efficiency using FDP

> FMS(Flash Memory Summit) QLC 세션에서 Meta가 발표한 슬라이드의 받아쓰기입니다.
> 원문 표기를 유지하고 철자 오류만 바로잡았습니다. 해석과 검토는 [해설 문서](fms_meta_해설.md)에 있습니다.

## Page 1. IO supply and WAF

**01. IO Supply & BW**
- At Meta, IO supply is typically represented as BW.
- For write to Flash, BW is split into two components:
  - User Write BW
    - Dedicated to standard host operation
  - Garbage Collection BW
    - Required for NAND management

**02. GC Models**
- Meta utilizes two distinct garbage collection architectures:
  - Older Model
    - GC is handled entirely at the host level, consuming computational overhead
  - Newer Implementation
    - GC is mostly offloaded and left directly to the SSDs

**03. WAF & Read Impact**
- Write Amplification Factor (WAF) combines overall GC writes, incorporating both host and device level activity.
- WAF also severely impacts reads:
  - Memory BW
    - Host GC consumes memory BW, limiting overall read capability
  - Read Latency
    - Drive GC causes latency spikes, forcing retries & reconstruction in upper stack layers

## Page 2. WAF Cost in the QLC IO Model

**1. QLC IO Capacity Model**
- R + 4W >= 32 MB/s/usable-TB
  - Writes are 4x costlier
    - Peak write is 8 MB/s/usable-TB when Read(R) = 0
  - WAF of 2.0 assumed
    - Exactly half of the total write BW is consumed by GC
  - Meta's QLC Deployment
    - Scaling at 2-3 PB of usable-TB per server
- WAF Cost > 20 GB/sec per server

**2. Read MB/s/usable-TB vs Write MB/s/usable-TB**
- (0, 8) 과 (32, 0) 을 직선으로 잇는 그래프. Allowed Operating Region (R + 4W >= 32)
- Capacity Boundary: R + 4W >= 32

## Page 3. Introduction to Flexible Data Placement

**How FDP Works**
- Host-Guided Placement
  - The host provides hints to the SSD about data lifetime, enabling smarter application-aware data organization on physical media
- Isolated Superblocks
  - The SSD uses the hints to segregate incoming data into separate physical superblocks based on expected longevity.
  - Without FDP, all data is mixed into a single superblock, causing heavy write amplification

**Key Operational Benefits**
- Reduced Fragmentation
  - Grouping data by lifetime ensures similarly-lived data gets deleted together, which dramatically decreases SSD fragmentation
- Minimized GC Overhead
  - By segregating data, FDP avoids mixing short-lived and long-lived blocks, reducing GC cycles and minimizing write amplification

## Page 4. FDP experiments - Setup

**Hardware & Configuration**
- Uses 8TB TLC drives.
- QLC drives with FDP were unavailable.
- High Fill Rate: 90%

**Operational Parameters**
- Lifetime Classification (PIDs)
  - HostGC(Cold) -> Hot: 4 hours -> Warm: 18 hours -> Cold (all others)
- Workload: Large block write (1M-8M)
  - 8x FDP Enabled: optimized superblock
  - 8x FDP Disabled: fragmented superblock

## Page 5. FDP experiments - Results

(그래프 2종, x축은 시간, y축 단위는 슬라이드에서 확인 불가)

- Disk Space Physical Util %
  - 그래프가 잘 보이지 않으나 우상향으로 상승하다가 포화. 16개 곡선이 한 다발로 뭉쳐 있음
- Write Amplification (NAND)
  - 아래쪽에서 우상향

**Key Takeaways**
- Balanced Utilization
  - Physical disk utilization is evenly distributed across all 16 SSDs
- WAF Reduction
  - Implementing FDP reduced the average WAF from ~1.8 down to ~1.1

## Page 6. Experimental data & future directions

**Experimental Insights**
- Lifetime Hints Evaluation
  - Disabling lifetime hints still demonstrated about 10% WAF improvement with FDP drives.
    - GC still maintained separate placement operations
- QLC Preliminary Results
  - Early experimental runs on QLC configurations show an encouraging 10% to 15% efficiency gain

**Future Directions**
- Bucket Tuning & Optimization
  - Fine tuning the number of allocation buckets remains a near-term objective
- Overall Target Expectations
  - WAF reduction
    - Decrease the default model's WAF significantly from 2.0 down to 1.5
  - Flexible baseline
    - Build a resilient framework where user driven write loads are capable of bursting past the baseline constraints
