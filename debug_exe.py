
import subprocess
try:
    process = subprocess.run([r'.\src\backend\dist\origin_backend.exe'], capture_output=True, text=True, encoding='utf-8')
    print("STDOUT:", process.stdout)
    print("STDERR:", process.stderr)
except Exception as e:
    print("ERROR:", e)
