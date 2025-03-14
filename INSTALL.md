## 安装指南

### 依赖环境
- Python 3.8+
- Tkinter 图形库

### EXE打包命令
```bash
pyinstaller --onefile --windowed --noconsole --add-data "Data;Data/" codes.py
