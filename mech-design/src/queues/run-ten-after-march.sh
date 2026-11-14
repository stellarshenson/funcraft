#!/bin/bash
# waits for the queue of run-march-all.sh (banners 09 and 08), then builds the welcome page with banner 09 and renders banner 10 on GPU 1
cd /home/lab/workspace/funcraft/mech-design
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
until grep -qa "^=== ALL DONE\|FAILED" wip/logs/procession-make-march-all.log; do sleep 20; done
grep -qa "FAILED" wip/logs/procession-make-march-all.log && { echo "=== earlier queue FAILED"; exit 1; }
make welcome || { echo "=== welcome FAILED"; exit 1; }
echo "=== welcome done $(date +%H:%M:%S)"
make procession-marauder || { echo "=== procession-marauder FAILED"; exit 1; }
echo "=== procession-marauder done $(date +%H:%M:%S)"
echo "=== ALL DONE $(date +%H:%M:%S)"
