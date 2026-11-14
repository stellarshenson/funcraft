#!/bin/bash
# on GPU 1, with the march (its foot never points its toes down) and the bird walk of src/procession/gait.py:
# banner 10, banner 09 with the welcome page, banner 08
cd /home/lab/workspace/funcraft/mech-design
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
echo "=== start $(date +%H:%M:%S)"
make procession-marauder || { echo "=== procession-marauder FAILED"; exit 1; }
echo "=== procession-marauder done $(date +%H:%M:%S)"
make procession-column || { echo "=== procession-column FAILED"; exit 1; }
echo "=== procession-column done $(date +%H:%M:%S)"
make welcome || { echo "=== welcome FAILED"; exit 1; }
echo "=== welcome done $(date +%H:%M:%S)"
make procession-hips || { echo "=== procession-hips FAILED"; exit 1; }
echo "=== procession-hips done $(date +%H:%M:%S)"
echo "=== ALL DONE $(date +%H:%M:%S)"
