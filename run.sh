set -euo pipefail

if [ -d output ]; then
	rm -r output
fi
cd analyzer && ./test.sh
cd ..
python analyzer/build_rust_skeleton.py
python element_translation.py
python fill_unimplemented.py