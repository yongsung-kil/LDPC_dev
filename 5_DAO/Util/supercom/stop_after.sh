#!/bin/bash

# 특정 Job ID 이상의 모든 job 정지 (상태 무관)
# ===== 기준 Job ID =====
MIN_JOBID=123456
# ========================

bjobs -noheader -a | awk -v min="$MIN_JOBID" '$1+0 >= min { print $1 }' | sort -rn | xargs -I{} bstop {}

echo "Done: stopped all jobs with ID >= $MIN_JOBID"
