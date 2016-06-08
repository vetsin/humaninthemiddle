#!/bin/bash
PORT=8001
echo "Listening on $PORT"
socat TCP-LISTEN:$PORT,fork stdout
