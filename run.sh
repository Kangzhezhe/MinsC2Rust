#!/usr/bin/env bash
set -euo pipefail

cd analyzer && ./test.sh
cd ..
python analyzer/build_rust_skeleton.py
python element_translation.py
python fill_unimplemented.py