cd Tool
./run.sh Tool_py/configs/config_c_algorithm.ini
./run_post_process.sh Tool_py/configs/config_c_algorithm.ini

./run.sh Tool_py/configs/config_crown.ini 
./run_post_process.sh Tool_py/configs/config_crown.ini

cd ../Output
python3 ./merge_metrics.py
