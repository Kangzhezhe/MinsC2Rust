cd Tool
bash ./run.sh Tool_py/configs/config_c_algorithm.ini 
bash ./run_post_process.sh Tool_py/configs/config_c_algorithm.ini

bash ./run.sh Tool_py/configs/config_crown.ini 
bash ./run_post_process.sh Tool_py/configs/config_crown.ini

cd ../Output
python3 ./merge_metrics.py
