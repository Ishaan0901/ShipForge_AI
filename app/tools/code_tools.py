import os
import sys
import docker
import subprocess


#   A function to save the code into a new file....
def save_code(code,run_dir):
    code=code.replace('```python','').replace('```','').strip()
    path=os.path.join(run_dir,'main.py')

    with open(path,'w',encoding='utf-8') as c:
        c.write(code)

    return path



#   A function to run the saved code...
def run_code_local(file_path):

    abs_path=os.path.abspath(file_path)
    folder=os.path.dirname(abs_path)

    try:
        result=subprocess.run([sys.executable,abs_path],
                   timeout=10,
                   capture_output=True,
                   text=True,
                   cwd=folder)

        final_result=(result.returncode,result.stderr,result.stdout)
        
        return final_result
    
    except Exception as e:
        returncode=-1
        stderr=f'Code execution failed due to {e}'
        stdout=''

        final_result=(returncode,stderr,stdout)
        return final_result





def run_code(file_path):
    abs_path = os.path.abspath(file_path)
    folder = os.path.dirname(abs_path)
    filename = os.path.basename(abs_path)

    container = None
    try:
        client = docker.from_env()
        container = client.containers.run(
            'python:3.12-slim',
            ['python', filename],
            volumes={folder: {'bind': '/app', 'mode': 'rw'}},
            working_dir='/app',
            network_disabled=True,
            mem_limit='128m',
            nano_cpus=500000000,
            detach=True,
        )
        try:
            result = container.wait(timeout=10)
        except Exception:
            container.kill()
            return (-1, 'Timeout: code ran longer than 10 seconds', '')

        stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='ignore')
        stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='ignore')
        return (result['StatusCode'], stderr, stdout)

    except Exception as e:
        return (-1, f'Docker run failed: {e}', '')

    finally:
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass