cd /home/mins/MinsC2Rust && python c_project_analyzer.py 
cd /home/mins/MinsC2Rust && python c_project_reconstructor.py
cd /home/mins/MinsC2Rust/temp/reconstructed_c_algorithm/build && rm -rf ./* 2>/dev/null || true && cmake .. && make