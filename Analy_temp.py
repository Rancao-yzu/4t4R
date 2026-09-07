import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import glob
from pathlib import Path
import threading

class TemperatureMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("4T4R DV Test - 温度监控系统 All")
        self.root.geometry("820x620")
        self.root.minsize(720, 500)
        
        # 颜色方案
        self.colors = {
            'bg': '#fef7ee',
            'card': '#ffffff',
            'primary': '#faa85c',
            'primary_hover': "#fdbc80",
            'primary_light': '#ffedd5',
            'success': '#16a34a',
            'success_light': '#dcfce7',
            'danger': '#dc2626',
            'danger_light': '#fee2e2',
            'warning': '#d97706',
            'warning_light': '#fef3c7',
            'text': '#1e293b',
            'text_secondary': '#64748b',
            'border': '#fed7aa',
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # 设置样式
        style = ttk.Style()
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('Card.TFrame', background=self.colors['card'])
        style.configure('TLabelframe', background=self.colors['bg'], foreground=self.colors['text'])
        style.configure('TLabelframe.Label', background=self.colors['bg'], foreground=self.colors['text'],
                        font=('Microsoft YaHei UI', 10))
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['text'])
        style.configure('Card.TLabel', background=self.colors['card'], foreground=self.colors['text'])
        style.configure('TEntry', fieldbackground='white')
        
        # 进度条
        style.configure('orange.Horizontal.TProgressbar', background=self.colors['primary'],
                        troughcolor=self.colors['border'], borderwidth=0, lightcolor=self.colors['primary'],
                        darkcolor=self.colors['primary'])
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="0")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ====== 顶部标题栏 ======
        header_frame = tk.Frame(main_frame, bg=self.colors['primary'], height=60)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E))
        header_frame.grid_propagate(False)
        
        tk.Label(header_frame, text="4T4R DV Test 温度监控工具",
                 font=('Microsoft YaHei UI', 16, 'bold'), fg='white', bg=self.colors['primary']).pack(side=tk.LEFT, padx=20, pady=12)
        
        tk.Label(header_frame, text="v1.0",
                 font=('Microsoft YaHei UI', 9), fg='#fed7aa', bg=self.colors['primary']).pack(side=tk.RIGHT, padx=20, pady=12)
        
        # ====== 文件选择区域 ======
        folder_frame = ttk.LabelFrame(main_frame, text=" 文件选择 ", padding="15")
        folder_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=12, padx=12)
        
        self.folder_path = tk.StringVar()
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path, width=55)
        self.folder_entry.grid(row=0, column=0, padx=(0, 8), pady=2, sticky=(tk.W, tk.E))
        
        self.browse_btn = tk.Button(folder_frame, text=" 选择文件夹 ", command=self.browse_folder,
                                    font=('Microsoft YaHei UI', 9),
                                    bg=self.colors['primary'], fg='white', relief='flat',
                                    cursor='hand2', padx=12, pady=4,
                                    activebackground=self.colors['primary_hover'], activeforeground='white')
        self.browse_btn.grid(row=0, column=1, padx=5)
        self.browse_btn.bind('<Enter>', lambda e: self.browse_btn.config(bg=self.colors['primary_hover']))
        self.browse_btn.bind('<Leave>', lambda e: self.browse_btn.config(bg=self.colors['primary']))
        
        # ====== 状态显示区域 ======
        status_frame = ttk.LabelFrame(main_frame, text=" 处理状态 ", padding="15")
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 12), padx=12)
        
        # 进度条容器
        progress_container = tk.Frame(status_frame, bg=self.colors['card'])
        progress_container.pack(fill=tk.X, pady=(0, 8))
        
        self.progress_label = tk.Label(progress_container, text="就绪", font=('Microsoft YaHei UI', 9),
                                       fg=self.colors['text_secondary'], bg=self.colors['card'], anchor=tk.W)
        self.progress_label.pack(fill=tk.X, pady=(0, 4))
        
        self.progress = ttk.Progressbar(progress_container, mode='indeterminate', style='orange.Horizontal.TProgressbar')
        self.progress.pack(fill=tk.X)
        
        # 状态文本
        text_container = tk.Frame(status_frame, bg=self.colors['border'], highlightthickness=1,
                                  highlightcolor=self.colors['border'], highlightbackground=self.colors['border'])
        text_container.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = tk.Text(text_container, height=14, wrap=tk.WORD,
                                   font=('Consolas', 10),
                                   bg='#fafafa', fg=self.colors['text'],
                                   relief='flat', borderwidth=0, padx=10, pady=8)
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 日志颜色标记
        self.status_text.tag_config('info', foreground=self.colors['text'])
        self.status_text.tag_config('success', foreground=self.colors['success'])
        self.status_text.tag_config('error', foreground=self.colors['danger'])
        self.status_text.tag_config('warning', foreground=self.colors['warning'])
        self.status_text.tag_config('highlight', foreground=self.colors['primary'])
        
        # 滚动条
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        # ====== 底部按钮区域 ======
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        button_frame.grid(row=3, column=0, columnspan=3, pady=(0, 15))
        
        btn_style = {
            'font': ('Microsoft YaHei UI', 10),
            'relief': 'flat',
            'cursor': 'hand2',
            'padx': 20, 'pady': 6,
        }
        
        self.process_btn = tk.Button(button_frame, text=" 开始处理 ", command=self.start_processing,
                                     state='disabled',
                                     bg=self.colors['border'], fg='#94a3b8',
                                     activebackground=self.colors['primary_hover'], activeforeground='white',
                                     **btn_style)
        self.process_btn.pack(side=tk.LEFT, padx=4)
        self.process_btn.bind('<Enter>', lambda e: self._on_btn_hover(self.process_btn))
        self.process_btn.bind('<Leave>', lambda e: self._on_btn_leave(self.process_btn))
        
        self.clear_btn = tk.Button(button_frame, text=" 清除日志 ", command=self.clear_log,
                                   bg='#64748b', fg='white',
                                   activebackground='#475569', activeforeground='white',
                                   **btn_style)
        self.clear_btn.pack(side=tk.LEFT, padx=4)
        self.clear_btn.bind('<Enter>', lambda e: self.clear_btn.config(bg='#475569'))
        self.clear_btn.bind('<Leave>', lambda e: self.clear_btn.config(bg='#64748b'))
        
        self.exit_btn = tk.Button(button_frame, text=" 退出程序 ", command=self.exit_app,
                                  bg=self.colors['danger'], fg='white',
                                  activebackground='#b91c1c', activeforeground='white',
                                  **btn_style)
        self.exit_btn.pack(side=tk.LEFT, padx=4)
        self.exit_btn.bind('<Enter>', lambda e: self.exit_btn.config(bg='#b91c1c'))
        self.exit_btn.bind('<Leave>', lambda e: self.exit_btn.config(bg=self.colors['danger']))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        folder_frame.columnconfigure(0, weight=1)
        
    def _on_btn_hover(self, btn):
        if btn['state'] != 'disabled':
            btn.config(bg=self.colors['primary_hover'])
    
    def _on_btn_leave(self, btn):
        if btn['state'] != 'disabled':
            btn.config(bg=self.colors['primary'])
        
    def browse_folder(self):
        folder = filedialog.askdirectory(title="选择包含CSV文件的文件夹")
        if folder:
            self.folder_path.set(folder)
            self.process_btn.config(state='normal', bg=self.colors['primary'], fg='white')
            self.progress_label.config(text="已选择文件夹，点击「开始处理」运行", fg=self.colors['success'])
            self.log_message("已选择文件夹: " + folder, 'success')
    
    def log_message(self, message, tag='info'):
        self.status_text.insert(tk.END, message + '\n', tag)
        self.status_text.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        """清除日志"""
        self.status_text.delete(1.0, tk.END)
    
    def start_processing(self):
        if not self.folder_path.get():
            messagebox.showwarning("警告", "请先选择文件夹")
            return
        
        self.process_btn.config(state='disabled', bg=self.colors['border'], fg='#94a3b8')
        self.browse_btn.config(state='disabled')
        
        self.progress_label.config(text="正在处理中...", fg=self.colors['primary'])
        self.progress.start()
        
        thread = threading.Thread(target=self.process_files)
        thread.start()
    
    def process_files(self):
        """处理文件的逻辑"""
        try:
            input_folder = self.folder_path.get()
            
            # 创建output文件夹
            output_folder = Path(input_folder) / 'output'
            output_folder.mkdir(exist_ok=True)
            
            # 查找所有包含AllData的文件
            csv_files = glob.glob(os.path.join(input_folder, '*All*.csv'))
            
            if not csv_files:
                self.log_message("在 " + input_folder + " 中没有找到包含'AllData'的CSV文件", 'error')
                return
            
            self.log_message("找到 " + str(len(csv_files)) + " 个包含'AllData'的文件", 'success')
            
            processed_count = 0
            for csv_file in csv_files:
                self.log_message("处理文件: " + os.path.basename(csv_file), 'highlight')
                
                try:
                    df = pd.read_csv(csv_file)
                    
                    if 'Time' in df.columns:
                        original_count = len(df)
                        df = df[df['Time'].notna()]
                        skipped_count = original_count - len(df)
                        if skipped_count > 0:
                            self.log_message("  跳过了 " + str(skipped_count) + " 行 (Time为NaN)", 'warning')
                    else:
                        self.log_message("  警告: 文件中没有'Time'列", 'warning')
                    
                    if len(df) == 0:
                        self.log_message("  跳过: 没有有效数据行", 'warning')
                        continue
                    
                    temp_columns = []
                    for col in df.columns:
                        if 'temp' in col.lower():
                            temp_columns.append(col)
                    
                    if not temp_columns:
                        self.log_message("  没有找到包含'Temp'的列", 'warning')
                        continue
                    
                    self.log_message("  找到 " + str(len(temp_columns)) + " 个温度相关列", 'info')
                    
                    sn_cols = [f'rbPda_SlogSubBlockDataRamBuffer_au8._{i}_' for i in range(29, 69)]
                    sn_str = ''
                    if all(col in df.columns for col in sn_cols):
                        first_row = df.iloc[0]
                        sn_chars = []
                        for col in sn_cols:
                            val = first_row[col]
                            if pd.notna(val):
                                sn_chars.append(chr(int(val)))
                            else:
                                sn_chars.append('')
                        sn_str = '\t' + ''.join(sn_chars)
                    else:
                        self.log_message("  未找到SN相关列", 'warning')
                    
                    result_dict = {'time': [], 'SN': []}
                    
                    for col in temp_columns:
                        mean_col_name = f"{col}_mean"
                        max_col_name = f"{col}_max"
                        
                        mean_value = df[col].mean()
                        max_value = df[col].max()
                        
                        result_dict[mean_col_name] = [mean_value]
                        result_dict[max_col_name] = [max_value]
                    
                    result_dict['time'] = ['Summary']
                    result_dict['SN'] = [sn_str]
                    
                    result_df = pd.DataFrame(result_dict)
                    
                    output_filename = output_folder / os.path.basename(csv_file)
                    result_df.to_csv(output_filename, index=False)
                    
                    self.log_message("  已保存: " + str(output_filename), 'success')
                    
                    for col in temp_columns:
                        self.log_message("    " + col + ": 平均值=" + f"{df[col].mean():.2f}" + ", 最大值=" + f"{df[col].max():.2f}", 'info')
                    
                    processed_count += 1
                    
                except Exception as e:
                    self.log_message("  处理出错: " + str(e), 'error')
            
            self.log_message("处理完成! 成功处理 " + str(processed_count) + "/" + str(len(csv_files)) + " 个文件", 'success')
            self.log_message("结果保存在: " + str(output_folder), 'highlight')
            messagebox.showinfo("完成", "处理完成!\n成功处理 " + str(processed_count) + " 个文件")
            
        except Exception as e:
            self.log_message("处理过程中出错: " + str(e), 'error')
            messagebox.showerror("错误", "处理过程中出错:\n" + str(e))
        
        finally:
            self.progress.stop()
            self.progress_label.config(text="处理结束", fg=self.colors['text_secondary'])
            
            self.process_btn.config(state='normal', bg=self.colors['primary'], fg='white')
            self.browse_btn.config(state='normal')
    
    def exit_app(self):
        if messagebox.askyesno("确认", "确定要退出程序吗？"):
            self.root.quit()
            self.root.destroy()

def main():
    root = tk.Tk()
    app = TemperatureMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()