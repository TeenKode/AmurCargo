from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
output = root / 'outputs'
output.mkdir(exist_ok=True)
archive = output / 'AmurCargo_Full_Project.zip'
subprocess.run(
    ['git', 'archive', '--format=zip', '-o', str(archive), 'HEAD'],
    cwd=root, check=True,
)
print(archive)
