#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

class DataFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("4T4R DV测试数据筛选工具 @Weifu tools")
        self.root.geometry("666x600")
        
        # 默认白名单
        self.white_number_error = [0,9,11,12,13,16,74,77,78,86,108,139,140,141,142,153,154,156,159,166,168,169,170,174]
        
        # 存储选中的文件夹
        self.input_folder = ""
        self.output_folder = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 输入文件夹选择
        ttk.Label(main_frame, text="输入文件夹:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_entry = ttk.Entry(main_frame, width=60)
        self.input_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="浏览", command=self.select_input_folder).grid(row=0, column=2, pady=5)
        
        # 输出文件夹（自动为输入文件夹下的OUT，按子目录结构分别存放）
        ttk.Label(main_frame, text="输出文件夹:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_entry = ttk.Entry(main_frame, width=60, state='readonly')
        self.output_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(main_frame, text="自动(OUT)", foreground='gray').grid(row=1, column=2, pady=5, padx=5)
        
        # 白名单配置区域
        ttk.Label(main_frame, text="白名单配置,用英文逗号分隔):").grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        # 创建白名单编辑框和滚动区域
        whitelist_frame = ttk.Frame(main_frame)
        whitelist_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.whitelist_text = tk.Text(whitelist_frame, height=8, width=80)
        self.whitelist_text.grid(row=0, column=0)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(whitelist_frame, command=self.whitelist_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.whitelist_text['yscrollcommand'] = scrollbar.set
        
        # 初始显示白名单
        self.whitelist_text.insert('1.0', ', '.join(map(str, self.white_number_error)))
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="重置白名单", command=self.reset_whitelist).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="开始处理", command=self.process_files).pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        ttk.Label(main_frame, text="处理日志:", font=('Arial', 10, 'bold')).grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        self.log_text = tk.Text(main_frame, height=15, width=90)
        self.log_text.grid(row=6, column=0, columnspan=3, pady=5)
        
        log_scrollbar = ttk.Scrollbar(main_frame, command=self.log_text.yview)
        log_scrollbar.grid(row=6, column=3, sticky=(tk.N, tk.S))
        self.log_text['yscrollcommand'] = log_scrollbar.set
        
    def log(self, message):
        """添加日志信息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def select_input_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder = folder
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, folder)
            # 自动设置输出文件夹为输入文件夹下的OUT
            self.output_folder = os.path.join(folder, 'OUT')
            self.output_entry.configure(state='normal')
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, self.output_folder)
            self.output_entry.configure(state='readonly')
            
    def reset_whitelist(self):
        """重置白名单"""
        self.white_number_error = [0, 11, 9, 22, 12, 72, 65, 139, 168, 159, 170, 86, 169, 140, 141, 78, 16, 174, 153, 77, 108, 166, 156]
        self.whitelist_text.delete('1.0', tk.END)
        self.whitelist_text.insert('1.0', ', '.join(map(str, self.white_number_error)))
        self.log("白名单已重置为默认值")
        
    def process_files(self):
        """处理所有CSV文件（递归查找）"""
        if not self.input_folder:
            messagebox.showerror("错误", "请选择输入文件夹")
            return

        # 输出文件夹固定为输入顶层目录下的OUT（没有则自动创建）
        self.output_folder = os.path.join(self.input_folder, 'OUT')
        os.makedirs(self.output_folder, exist_ok=True)

        # 读取当前白名单配置
        whitelist_str = self.whitelist_text.get('1.0', tk.END).strip()
        try:
            self.white_number_error = [int(x.strip()) for x in whitelist_str.split(',') if x.strip()]
        except:
            messagebox.showerror("错误", "白名单格式错误，请使用逗号分隔的数字")
            return

        # 递归查找所有包含All的CSV文件（跳过OUT输出目录）
        out_abs = os.path.abspath(self.output_folder)
        csv_files = []
        for dirpath, dirnames, filenames in os.walk(self.input_folder):
            # 排除OUT输出目录，避免重复处理历史结果
            dirnames[:] = [d for d in dirnames
                           if os.path.abspath(os.path.join(dirpath, d)) != out_abs]
            for f in filenames:
                if f.lower().endswith('.csv') and 'All' in f:
                    csv_files.append(os.path.join(dirpath, f))

        if not csv_files:
            self.log("未找到包含'All'的CSV文件")
            messagebox.showwarning("警告", "未找到包含'All'的CSV文件")
            return

        self.log(f"递归找到 {len(csv_files)} 个文件需要处理")
        self.log(f"输出目录: {self.output_folder}")

        total_abnormal = 0
        for file_path in sorted(csv_files):
            rel_path = os.path.relpath(file_path, self.input_folder)
            self.log(f"\n正在处理文件: {rel_path}")
            try:
                # 输出子目录与输入子目录结构保持一致，分别存放结果
                rel_dir = os.path.dirname(rel_path)
                file_out_dir = self.output_folder if rel_dir == '.' else os.path.join(self.output_folder, rel_dir)
                os.makedirs(file_out_dir, exist_ok=True)
                abnormal_count = self.process_single_file(file_path, file_out_dir)
                total_abnormal += abnormal_count
            except Exception as e:
                self.log(f"处理文件 {rel_path} 时出错: {str(e)}")

        self.log(f"\n所有文件处理完成！共发现 {total_abnormal} 条异常数据")
        messagebox.showinfo("完成", f"处理完成！共发现 {total_abnormal} 条异常数据")
        
    def process_single_file(self, file_path, out_dir):
        """处理单个CSV文件，返回异常数据条数"""
        filename = os.path.basename(file_path)

        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 第1步：跳过Time为NaN的行
        if 'Time' in df.columns:
            df = df.dropna(subset=['Time'])
        else:
            self.log("警告: 文件中没有Time列")
            
        # 存储异常数据
        abnormal_rows = []
        
        # 预定义event列名
        event_cols = [f'rba_DemBfm_Records._{i}_.eventId' for i in range(20)]
        
        for idx, row in df.iterrows():
            is_abnormal = False
            fault_info = []
            
            # 获取20个eventId的值（无论是否异常都要获取）
            number_error_ids = []
            for col in event_cols:
                if col in df.columns:
                    event_id = row[col]
                    if pd.notna(event_id):
                        number_error_ids.append(event_id)
                    else:
                        number_error_ids.append(None)
                else:
                    number_error_ids.append(None)
            
            # 第2步：检查各项条件
            # 2.1 检查电压
            if 'rbAdc_DebugData_st.rbAdc_VbatVoltage_u16' in df.columns:
                voltage = row['rbAdc_DebugData_st.rbAdc_VbatVoltage_u16']
                if pd.notna(voltage) and voltage > 16 * 1000:  # 16*1000 = 16000
                    is_abnormal = True
                    fault_info.append(f"Voltage_High:{voltage}")
                    
            # 2.2 检查温度列
            temp_cols = [col for col in df.columns if 'temp' in col.lower()]
            for col in temp_cols:
                temp_val = row[col]
                if pd.notna(temp_val) and temp_val > 135 :
                    is_abnormal = True
                    fault_info.append(f"Temp_High:{col.split('.')[-1]}={temp_val}")
                    
            # 2.3 检查Pmic列
            pmic_cols = [col for col in df.columns if 'Pmic' in col]
            for col in pmic_cols:
                pmic_val = row[col]
                if pd.notna(pmic_val) and pmic_val != 0 and pmic_val != "0" and pmic_val != "NAN":
                    is_abnormal = True
                    fault_info.append(f"Pmic_NotZero:{col.split('.')[-1]}={pmic_val}")
                    
            # 2.4 检查errorCounter
            if 'g_rbRsp_ErrorTableArm.m_value._0_.errorCounter' in df.columns:
                error_counter = row['g_rbRsp_ErrorTableArm.m_value._0_.errorCounter']
                if pd.notna(error_counter) and error_counter != 0:
                    is_abnormal = True
                    fault_info.append(f"ErrorCounter_NotZero:{error_counter}")
            
            # 第3步：检查DemBfm事件ID是否在白名单
            # 找出不在白名单的事件ID
            abnormal_events = []
            for event_id in number_error_ids:
                if event_id is not None and event_id not in self.white_number_error:
                    abnormal_events.append(event_id)
            
            # 如果发现不在白名单的事件ID，进入第4步
            if abnormal_events:
                is_abnormal = True
                # 第4步：检查Dem_AllEventsStatusByte
                for event_id in abnormal_events:
                    # 检查Dem_AllEventsStatusByte
                    status_col = f'Dem_AllEventsStatusByte._{int(event_id)}_'
                    if status_col in df.columns:
                        status_value = row[status_col]
                        if pd.notna(status_value):
                            # 单数为当前故障，双数为历史故障
                            if status_value % 2 == 1:  # 单数
                                fault_type = "Active"
                            else:  # 双数
                                fault_type = "History"
                            fault_info.append(f"EventID_{int(event_id)}({fault_type})")
                        else:
                            fault_info.append(f"EventID_{int(event_id)}(Status_NA)")
                    else:
                        fault_info.append(f"EventID_{int(event_id)}(Status_Col_Missing)")
            
            # 如果满足第2步或第3步的条件，就记录异常
            if is_abnormal:
                abnormal_rows.append((idx, fault_info, number_error_ids))
                
        # 只输出异常数据
        if abnormal_rows:
            output_data = []
            for idx, fault_info, number_error_ids in abnormal_rows:
                row_dict = {}
                row_dict['time'] = df.loc[idx, 'Time'] if 'Time' in df.columns else ''
                row_dict['故障'] = '; '.join(fault_info) if fault_info else ''

                # 提取SN: 将rbPda_SlogSubBlockDataRamBuffer_au8._29_到._68_每列数值转ASCII后拼接
                sn_chars = []
                sn_cols = [f'rbPda_SlogSubBlockDataRamBuffer_au8._{i}_' for i in range(29, 69)]
                for col in sn_cols:
                    if col in df.columns:
                        val = df.loc[idx, col]
                        if pd.notna(val):
                            sn_chars.append(chr(int(val)))
                        else:
                            sn_chars.append('')
                    else:
                        sn_chars.append('')
                row_dict['SN'] = '\t' + ''.join(sn_chars)
                
                # 添加20个eventId列（白名单内赋值-1，否则赋值原始值）
                for i, val in enumerate(number_error_ids):
                    if val is not None and val in self.white_number_error:
                        row_dict[f'rba_DemBfm_Records._{i}_.eventId'] = -1
                    else:
                        row_dict[f'rba_DemBfm_Records._{i}_.eventId'] = val if val is not None else ''
                        
                # 添加电压列
                if 'rbAdc_DebugData_st.rbAdc_VbatVoltage_u16' in df.columns:
                    row_dict['rbAdc_DebugData_st.rbAdc_VbatVoltage_u16'] = df.loc[idx, 'rbAdc_DebugData_st.rbAdc_VbatVoltage_u16']
                    
                # 添加温度列
                temp_cols = [col for col in df.columns if 'temp' in col.lower()]
                for col in temp_cols:
                    row_dict[col] = df.loc[idx, col] if col in df.columns else ''
                    
                # 添加Pmic列
                pmic_cols = [col for col in df.columns if 'Pmic' in col]
                for col in pmic_cols:
                    row_dict[col] = df.loc[idx, col] if col in df.columns else ''
                    
                # 添加errorCounter
                if 'g_rbRsp_ErrorTableArm.m_value._0_.errorCounter' in df.columns:
                    row_dict['g_rbRsp_ErrorTableArm.m_value._0_.errorCounter'] = df.loc[idx, 'g_rbRsp_ErrorTableArm.m_value._0_.errorCounter']
                    
                output_data.append(row_dict)
                
            # 保存到输出文件
            output_df = pd.DataFrame(output_data)
            output_filename = os.path.join(out_dir, filename)
            output_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
            self.log(f"已保存异常数据到: {output_filename}, 共{len(output_data)}条异常记录")
            return len(output_data)
        else:
            self.log(f"文件 {filename} 无异常数据，不输出文件")
            return 0
            
def main():
    root = tk.Tk()
    app = DataFilterApp(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()