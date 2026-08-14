#!/bin/bash

# 현재 RUN 중인 최대 Job ID를 구하고, 그보다 큰 ID의 job을 모두 정지

MAX_JOBID=$(bjobs -noheader | awk '$3 == "RUN" {if ($1+0 > max) max=$1+0} END {print max}')

if [ -z "$MAX_JOBID" ]; then
    echo "Error: RUN 상태 job 없음"
    exit 1
fi

echo "현재 RUN 최대 Job ID: $MAX_JOBID"
echo "Job ID > $MAX_JOBID 정지 중..."

bjobs -noheader -a | awk -v max="$MAX_JOBID" '$1+0 > max { print $1 }' | sort -rn | xargs -I{} bstop {}

echo "Done: stopped all jobs with ID > $MAX_JOBID"
