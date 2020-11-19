#!/bin/sh -ex

# chown $UID:$GID $DATA_DIR/*

sudo -Eu $USER_NAME "$@"
