#!/bin/sh -ex

mkdir -p /opt/hoover/metrics
chown -R 666:666 /opt/hoover/metrics

chown -R $UID:$GID $DATA_DIR/*

exec gosu $USER_NAME "$@"
# sudo -Eu $USER_NAME "$@"
