#!/bin/bash

echo $(cat "$1" | tr -d '[:space:]' | sha512sum | cut -c-128) $1