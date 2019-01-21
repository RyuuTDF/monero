#!/bin/bash
# Assumes current working directory contains monderod
./monerod --detach --rpc-bind-ip 0.0.0.0 --confirm-external-bind --no-igd --log-level tud.connection:INFO,tud.tx:INFO,tud.block:INFO,tud.reason:INFO
