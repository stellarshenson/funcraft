#!/bin/bash
# waits for the queue of run-two-walks.sh, then renders banner 10 again on GPU 1, with the Mad Cat's cloth under its pelvis
cd /home/lab/workspace/funcraft/mech-design
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
until grep -qa "^=== ALL DONE\|FAILED" wip/logs/procession-make-two-walks.log; do sleep 15; done
echo "=== start $(date +%H:%M:%S)"
make procession-marauder || { echo "=== procession-marauder FAILED"; exit 1; }
echo "=== procession-marauder done $(date +%H:%M:%S)"
echo "=== ALL DONE $(date +%H:%M:%S)"
