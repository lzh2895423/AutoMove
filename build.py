import os
import shutil
import subprocess

# 设置路径
project_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(project_dir, "Data")
output_dir = os.path.join(project_dir, "AutoMoveEXE")
exe_name = "AutoMove"

# 确保目标目录存在
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 打包命令
pyinstaller_cmd = [
    "pyinstaller",
    "--onefile",
    "--windowed",
    "--noconsole",
    f"--name={exe_name}",
    f"--add-data=Data{os.pathsep}Data/",
    "codes.py",
    f"--distpath={output_dir}"
]

# 执行 PyInstaller 打包
subprocess.run(pyinstaller_cmd, check=True)

# 复制数据文件夹
dest_data_dir = os.path.join(output_dir, "Data")
if os.path.exists(dest_data_dir):
    shutil.rmtree(dest_data_dir)
shutil.copytree(data_dir, dest_data_dir)

print(f"已完成打包，AutoMove.exe 及 Data 文件夹已保存到 {output_dir}")
