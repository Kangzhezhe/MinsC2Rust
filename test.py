import subprocess

def get_system_include_paths():
    cmd = ['gcc', '-E', '-Wp,-v', '-']
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = proc.communicate(input=b'')
    lines = stderr.decode().splitlines()
    start = False
    paths = []
    for line in lines:
        if line.strip() == '#include <...> search starts here:':
            start = True
            continue
        if line.strip() == 'End of search list.':
            break
        if start:
            paths.append(line.strip())
    return paths

print(get_system_include_paths())