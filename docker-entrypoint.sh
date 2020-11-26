#!/bin/sh -ex

chown -R $UID:$GID $DATA_DIR

exec gosu $USER_NAME "$@"
