import tkinter as tk
from tkinter import ttk, messagebox
from tqdm import tqdm
import os
import shutil
import json

class FileSyncApp:
    def __init__(self, master):
        # 添加Treeview样式
        style = ttk.Style()
        style.configure("Treeview", 
                    rowheight=20, 
                    font=('微软雅黑', 9))
        style.configure("Treeview.Heading", 
                    font=('微软雅黑', 9, 'bold'))

        self.master = master
        master.title("安卓TEST：Data资源同步工具 v1.2.1")

        # 初始化配置
        self.schemes = {}
        self.current_scheme = "默认"
        self.config_file = os.path.join("Data", "schemes.json")
        self.path_config_file = os.path.join("Data", "path_config.json")

        # 加载配置
        self.load_schemes()
        self.load_path_config()  # 改为从文件加载路径配置
        
        # 创建界面组件
        self.create_widgets()

        # 如果本地有方案，默认使用第一个方案
        if self.schemes:
            self.current_scheme = next(iter(self.schemes))
            self.scheme_combo.set(self.current_scheme)
            self.load_scheme()



    def create_widgets(self):
        # 主容器
        main_frame = ttk.Frame(self.master, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 方案管理部分
        scheme_frame = ttk.Frame(main_frame)
        scheme_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(scheme_frame, text="方案:").pack(side=tk.LEFT, padx=5)
        self.scheme_combo = ttk.Combobox(
            scheme_frame, 
            values=list(self.schemes.keys()),
            state="readonly"
        )
        self.scheme_combo.pack(side=tk.LEFT, padx=5)
        self.scheme_combo.set(self.current_scheme)
        self.scheme_combo['state'] = 'normal'  # 设置为可编辑状态
        self.scheme_combo.bind("<<ComboboxSelected>>", self.load_scheme)
        
        save_btn = ttk.Button(
            scheme_frame, 
            text="保存方案", 
            command=self.save_scheme
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        # 路径输入部分
        input_frame = ttk.LabelFrame(main_frame, text="路径设置", padding=10)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Data路径:").grid(row=0, column=0, sticky="e", padx=5)
        self.data_entry = ttk.Entry(input_frame, width=50)
        self.data_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Label(input_frame, text="AS路径:").grid(row=1, column=0, sticky="e", padx=5)
        self.as_entry = ttk.Entry(input_frame, width=50)
        self.as_entry.grid(row=1, column=1, sticky="ew", padx=5)

        # 路径选择部分
        select_frame = ttk.LabelFrame(main_frame, text="选择同步路径", padding=10)
        select_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建复选框网格布局
        for i, config in enumerate(self.path_config):
            row = i // 2
            col = i % 2
            
            # 生成AS路径描述
            as_rel_path = os.path.join(*config["dst_rel"]).replace(os.sep, '/')
            display_text = f"{config['name']}\n(AS路径/{as_rel_path})"
            
            # 创建主容器框架
            cell_frame = ttk.Frame(select_frame)
            cell_frame.grid(row=row, column=col, sticky="w", padx=10, pady=2)
            
            # 创建复选框
            cb = ttk.Checkbutton(
                cell_frame,
                text=display_text,
                variable=config["var"],
                command=lambda c=config: self.toggle_subdir_display(c),
                onvalue=True,
                offvalue=False
            )
            cb.pack(anchor="w")
            
            # 创建子文件夹显示区域
            config["subdir_frame"] = ttk.Frame(cell_frame)
            config["subdir_tree"] = ttk.Treeview(config["subdir_frame"], 
                                                height=4, 
                                                show="headings",
                                                columns=("check", "name"),
                                                selectmode="none")
            scroll = ttk.Scrollbar(config["subdir_frame"], 
                                    orient="vertical",
                                    command=config["subdir_tree"].yview)
            config["subdir_tree"].configure(yscrollcommand=scroll.set)
            
            # 添加列
            config["subdir_tree"].column("check", width=20, anchor="w")
            config["subdir_tree"].column("name", width=200, anchor="w")
            config["subdir_tree"].heading("check", text="")
            config["subdir_tree"].heading("name", text="子文件夹名称")
            
            scroll.pack(side="right", fill="y")
            config["subdir_tree"].pack(side="left", fill="both", expand=True)
            
            # 初始化隐藏
            config["subdir_frame"].pack_forget()

        # 操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        self.sync_btn = ttk.Button(btn_frame, text="开始导入", command=self.start_sync)
        self.sync_btn.pack(side=tk.LEFT, padx=5)


    def load_schemes(self):
        """加载保存的方案"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.schemes = json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"加载方案失败: {str(e)}")

    def save_schemes(self):
        """保存方案到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.schemes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存方案失败: {str(e)}")

    def save_scheme(self):
        """保存当前配置为方案"""
        scheme_combo = self.scheme_combo.get().strip()
        if not scheme_combo:
            messagebox.showwarning("提示", "请输入方案名称")
            return
        
        # 收集当前配置
        config = {
            "data_path": self.data_entry.get(),
            "as_path": self.as_entry.get(),
            "selections": {
                cfg["name"]: cfg["var"].get() for cfg in self.path_config
            },
            "subdir_selections": {
                cfg["name"]: {subdir_name: subdir_var.get() for subdir_name, subdir_var in cfg["subdir_vars"].items()}
                for cfg in self.path_config if "subdir_vars" in cfg
            }
        }
        
        # 检查是否覆盖已有方案
        if scheme_combo in self.schemes:
            if not messagebox.askyesno("确认", "方案已存在，是否覆盖？"):
                return
        
        # 更新方案数据
        self.schemes[scheme_combo] = config
        self.save_schemes()
        
        # 更新下拉框
        self.scheme_combo["values"] = list(self.schemes.keys())
        self.scheme_combo.set(scheme_combo)
        self.current_scheme = scheme_combo
        messagebox.showinfo("提示", "方案保存成功")

    def load_scheme(self, event=None):
        """加载选定方案"""
        print("load_scheme--------------------")
        scheme_combo = self.scheme_combo.get()
        if not scheme_combo or scheme_combo not in self.schemes:
            return
        
        config = self.schemes[scheme_combo]
        
        # 更新路径输入
        self.data_entry.delete(0, tk.END)
        self.data_entry.insert(0, config["data_path"])
        
        self.as_entry.delete(0, tk.END)
        self.as_entry.insert(0, config["as_path"])
        
        # 更新复选框状态
        for cfg in self.path_config:
            main_var = config["selections"].get(cfg["name"], False)
            cfg["var"].set(main_var)
            
            # 恢复子文件夹选择状态
            subdir_selections = config.get("subdir_selections", {}).get(cfg["name"], {})
            for subdir, value in subdir_selections.items():
                if subdir in cfg["subdir_vars"]:
                    cfg["subdir_vars"][subdir].set(value)
                        
                # 重新加载子文件夹到TreeView
                self.load_subdirs(cfg)

            # 如果配置项被选中且配置项有子文件夹，则显示子文件夹
            if cfg["var"].get() and cfg.get("isShow", False):
                self.toggle_subdir_display(cfg)
        
        self.current_scheme = scheme_combo

    def start_sync(self):
        data_path = self.data_entry.get()
        as_path = self.as_entry.get()
        
        # 构建完整路径
        processed_config = []
        for config in self.path_config:
            if config["var"].get():  # 只处理选中的路径
                src = os.path.join(data_path, *config["src_rel"])
                dst = os.path.join(as_path, *config["dst_rel"])
                subdir_vars = config.get("subdir_vars", None)
                processed_config.append({
                    "src": src,
                    "dst": dst,
                    "mode": config["mode"],
                    "subdir_vars": subdir_vars
                })

        # 计算总的文件数
        total_files = sum(self.count_selected_files(config["src"], config["subdir_vars"]) for config in processed_config)


        # 打开进度条窗口
        self.progress_window = tk.Toplevel(self.master)
        self.progress_window.title("同步进度")
        self.progress_window.geometry("800x60") 
        
        # self.progress_var = tk.DoubleVar(value=0)
        # self.progress_bar = ttk.Progressbar(self.progress_window, variable=self.progress_var, maximum=100)
        # self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.current_file_label = ttk.Label(self.progress_window, text="当前文件路径：")
        self.current_file_label.pack(fill=tk.X, padx=5)
        
        current_file_count = 0

        try:
            # 第一步：清理目标目录（仅限default模式）
            for config in processed_config:
                if config["mode"] == "default":
                    self.clean_directory(config["dst"],config["subdir_vars"])

            # 同步逻辑
            for config in processed_config:
                if config["mode"] == "default":
                    current_file_count = self.copy_contents_with_progress(
                        config["src"], 
                        config["dst"], 
                        data_path, 
                        total_files, 
                        current_file_count, 
                        config["subdir_vars"]
                    )
                elif config["mode"] == "libs":
                    current_file_count = self.sync_libs_with_progress(
                        config["src"], 
                        config["dst"], 
                        data_path, 
                        total_files, 
                        current_file_count, 
                        config["subdir_vars"]
                    )

            messagebox.showinfo("完成", "资源导入完成！")
        except Exception as e:
            messagebox.showerror("错误", f"操作失败: {str(e)}")
        
        # 完成同步后，重置进度条
        # self.progress_var.set(0)
        self.current_file_label.config(text="当前文件路径：")
        # self.master.update_idletasks()
        self.progress_window.destroy()

    def count_selected_files(self, directory, subdir_vars=None):
        """计算当前选中的子目录下的文件总数"""
        count = 0
        for root, dirs, files in os.walk(directory):
            # 检查子文件夹是否被选中
            if subdir_vars:
                subdirs_to_keep = [d for d in dirs if subdir_vars.get(d, True)]
                # 更新 dirs 列表以只包含选中的子文件夹
                dirs[:] = subdirs_to_keep
            
            count += len(files)
        return count

    def copy_contents_with_progress(self, src, dst, data_path, total_files, current_file_count, subdir_vars=None):
        """复制源目录内容到目标目录，并更新进度条"""
        if not os.path.exists(src):
            raise FileNotFoundError(f"源目录不存在: {src}")

        os.makedirs(dst, exist_ok=True)
        
        for item in os.listdir(src):
            src_path = os.path.join(src, item)
            dst_path = os.path.join(dst, item)

            # 检查子文件夹是否被选中
            if subdir_vars and item in subdir_vars and not subdir_vars[item].get():
                continue

            relative_path = os.path.relpath(src_path, data_path)  # 计算相对路径
            
            if os.path.isdir(src_path):
                current_file_count = self.copy_contents_with_progress(
                    src_path, dst_path, data_path, total_files, current_file_count, subdir_vars
                )
            else:
                shutil.copy2(src_path, dst_path)
                current_file_count += 1
                # self.update_progress(relative_path, total_files, current_file_count)
                self.current_file_label.config(text=f"当前文件路径：{relative_path}")
                self.master.update_idletasks()
        
        return current_file_count

    def sync_libs_with_progress(self, src, dst, data_path, total_files, current_file_count, subdir_vars=None):
        """智能同步libs目录，并更新进度条"""
        for root, dirs, files in os.walk(src):
            rel_path = os.path.relpath(root, src)
            dst_root = os.path.join(dst, rel_path)

            # 创建目标目录
            os.makedirs(dst_root, exist_ok=True)

            for dir_name in dirs:
                if subdir_vars and dir_name in subdir_vars and not subdir_vars[dir_name].get():
                    continue  # 跳过未选中的子文件夹

            # 同步文件
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dst_root, file)
                if os.path.exists(dst_file):
                    shutil.copy2(src_file, dst_file)
                    relative_path = os.path.relpath(src_file, data_path)
                    current_file_count += 1
                    # self.update_progress(relative_path, total_files, current_file_count)
                    self.current_file_label.config(text=f"当前文件路径：{relative_path}")
                    self.master.update_idletasks()

        return current_file_count

    def update_progress(self, file_path, total_files, current_file_count):
        """更新进度条和当前文件路径"""
        self.current_file_label.config(text=f"当前文件路径：{file_path}")
        # progress = (current_file_count / total_files) * 100
        # self.progress_var.set(progress)
        # self.master.update_idletasks()

    def clean_directory(self, path,subdir_vars):
        """清空目录但保留目录结构"""
        if os.path.exists(path):
            for item in os.listdir(path):
                # 检查子文件夹是否被选中
                if subdir_vars and item in subdir_vars and not subdir_vars[item].get():
                    continue
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                else:
                    shutil.rmtree(item_path)
        else:
            os.makedirs(path, exist_ok=True)
        
    def copy_contents(self, src, dst):
        """复制源目录内容到目标目录"""
        if not os.path.exists(src):
            raise FileNotFoundError(f"源目录不存在: {src}")

        os.makedirs(dst, exist_ok=True)
        
        for item in os.listdir(src):
            src_path = os.path.join(src, item)
            dst_path = os.path.join(dst, item)
            
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dst_path)

    def sync_libs(self, src, dst):
        """智能同步libs目录"""
        # 遍历目标目录的所有现有文件
        for root, dirs, files in os.walk(dst):
            rel_path = os.path.relpath(root, dst)
            src_root = os.path.join(src, rel_path)
            
            # 仅覆盖已存在的文件
            for file in files:
                src_file = os.path.join(src_root, file)
                dst_file = os.path.join(root, file)
                if os.path.exists(src_file):
                    shutil.copy2(src_file, dst_file)

    def load_path_config(self):
        """从文件加载路径配置"""
        try:
            if os.path.exists(self.path_config_file):
                with open(self.path_config_file, 'r', encoding='utf-8') as f:
                    raw_config = json.load(f)
                    self.path_config = []
                    for item in raw_config:
                        # 添加isShow配置项，默认False
                        item["isShow"] = item.get("isShow", False)
                        item["var"] = tk.BooleanVar(value=item.get("default_value", True))
                        item["subdir_vars"] = {}  # 新增子文件夹同步状态字典
                        self.path_config.append(item)
            else:
                # 配置文件不存在时创建默认配置
                default_config = [
                    {
                        "name": "assets",
                        "src_rel": ["unityLibrary", "src", "main", "assets"],
                        "dst_rel": ["app", "src", "main", "assets"],
                        "mode": "default",
                        "default_value": True,
                        "isShow": True
                    },
                    {
                        "name": "jniLibs",
                        "src_rel": ["unityLibrary", "src", "main", "jniLibs"],
                        "dst_rel": ["app", "src", "main", "jniLibs"],
                        "mode": "default",
                        "default_value": True,
                        "isShow": False
                    },
                    {
                        "name": "libs (智能同步)",
                        "src_rel": ["unityLibrary", "libs"],
                        "dst_rel": ["app", "libs", "main"],
                        "mode": "libs",
                        "default_value": True,
                        "isShow": False
                    }
                    # 其他默认配置项...
                ]
                with open(self.path_config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2)
                self.load_path_config()
                
        except Exception as e:
            messagebox.showerror("错误", f"加载路径配置失败: {str(e)}")
            self.path_config = []  # 防止程序崩溃

    def toggle_subdir_display(self, config):
        """切换子目录显示"""
        if config["var"].get() and config["isShow"]:
            self.load_subdirs(config)
            config["subdir_frame"].pack(anchor="w", pady=5)
        else:
            config["subdir_frame"].pack_forget()

    def load_subdirs(self, config):
        """加载子目录，并显示为可选项"""
        data_path = self.data_entry.get()
        src_path = os.path.join(data_path, *config["src_rel"])
        schemeConfig = self.schemes[self.scheme_combo.get()]

        # 清空旧数据
        for widget in config.get("subdir_frame", {}).winfo_children():
            widget.destroy()

        if os.path.exists(src_path):
            try:
                config["subdir_vars"] = {}   # 用于存储子文件夹的变量

                for entry in os.scandir(src_path):
                    if entry.is_dir():
                        var = tk.BooleanVar(value=schemeConfig["subdir_selections"][config["name"]].get(entry.name, True))  # 使用保存的选中状态
                        subdir_cb = ttk.Checkbutton(
                            config["subdir_frame"], 
                            text=entry.name, 
                            variable=var
                        )
                        subdir_cb.pack(anchor="w", padx=10)
                        config["subdir_vars"][entry.name] = var
            except Exception as e:
                error_msg = f"加载子目录失败: {str(e)}"
                print(f"[ERROR] {error_msg}")  # 错误日志
                messagebox.showerror("错误", error_msg)
        else:
            error_msg = f"路径不存在: {src_path}"
            print(f"[ERROR] {error_msg}")  # 错误日志
            messagebox.showerror("错误", error_msg)



if __name__ == "__main__":
    root = tk.Tk()
    app = FileSyncApp(root)
    root.geometry("600x800")
    root.mainloop()
