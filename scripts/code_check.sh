#!/bin/bash

SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$( cd "${SCRIPT_PATH}/.." >/dev/null 2>&1; pwd -P )"

pycodestyle --max-line-length=120 --max-doc-length=120 "${ROOT_PATH}/app"
