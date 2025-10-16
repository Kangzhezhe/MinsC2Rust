cd /home/mins/MinsC2Rust/analyzer && python c_project_analyzer.py 
cd /home/mins/MinsC2Rust/analyzer && python c_project_reconstructor.py
# cd /home/mins/MinsC2Rust/temp/reconstructed_c_algorithm/build && rm -rf ./* 2>/dev/null || true && cmake .. && make
cd /home/mins/MinsC2Rust/analyzer && python symbol_dependency_analyzer.py
cd /home/mins/MinsC2Rust/analyzer && python demo_visualization.py
# cd /home/mins/MinsC2Rust/analyzer && python topo_sort_dependencies.py --node-type non_functions
cd /home/mins/MinsC2Rust/analyzer && python topo_sort_dependencies.py
cd /home/mins/MinsC2Rust/analyzer && python symbol_batching.py