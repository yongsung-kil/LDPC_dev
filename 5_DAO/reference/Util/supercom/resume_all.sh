#!/bin/bash

# 모든 suspend 상태 job 재개 (USUSP, SSUSP, PSUSP)
#
# bresume으로 재개 가능한 상태:
#   USUSP  - 사용자가 bstop으로 정지한 job → bresume으로 재개 가능
#   SSUSP  - LSF 시스템이 리소스 부족으로 정지 → bresume 불가, 리소스 확보 시 자동 재개
#   PSUSP  - 관리자가 정지한 job → bresume 불가, 관리자(badmin)만 재개 가능
#
# 실질적으로 USUSP만 풀림. SSUSP/PSUSP에 bresume을 날려도 에러 없이 무시됨.
bjobs -noheader -a | awk '$3 ~ /SUSP/ {print $1}' | xargs -I{} bresume {}

echo "Done: resumed all suspended jobs"
