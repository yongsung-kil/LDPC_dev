#!/bin/bash

# 현재 RUN 상태인 job ID 출력 + 최대 Job ID 표시
bjobs -noheader | awk '$3 == "RUN" {print $1; if ($1+0 > max) max=$1+0} END {if (max) print "\nMax Job ID: " max}'
