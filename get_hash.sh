#!/bin/bash

echo $(cat "$1" | tr -d '[:space:]' | sha512sum | cut -d' ' -f1) $1