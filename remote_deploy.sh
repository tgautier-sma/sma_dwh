#!/bin/sh
ssh -i ~/.ssh/id_ed25519 root@77.37.124.30 "cd /root/install/production/sma_dwh && git pull && ./deploy.sh"
