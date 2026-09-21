#!/bin/bash

# 특정 Job ID 이상의 모든 job 정지 (상태 무관)
# 사용법: stop_after.sh <MIN_JOBID>
if [ -z "$1" ]; then
    echo "사용법: $0 <MIN_JOBID>   (이 번호 이상인 job을 모두 정지)"
    exit 1
fi
MIN_JOBID="$1"

targets=$(bjobs -noheader -a | awk -v min="$MIN_JOBID" '$1+0 >= min { print $1 }' | sort -rn)
if [ -z "$targets" ]; then
    echo "정지할 job 없음 (ID >= $MIN_JOBID)"
    exit 0
fi
echo "정지 대상 job:"
echo "$targets"
read -r -p "계속할까요? [y/N] " answer
if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
    echo "취소"
    exit 0
fi
echo "$targets" | xargs -I{} bstop {}

echo "Done: stopped all jobs with ID >= $MIN_JOBID"
