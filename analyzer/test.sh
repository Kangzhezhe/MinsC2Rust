python c_project_analyzer.py 
python c_project_reconstructor.py
# cd /home/mins/MinsC2Rust/temp/reconstructed_c_algorithm/build && rm -rf ./* 2>/dev/null || true && cmake .. && make
python symbol_dependency_analyzer.py
python demo_visualization.py
# python topo_sort_dependencies.py --node-type non_functions
python topo_sort_dependencies.py
python symbol_batching.py