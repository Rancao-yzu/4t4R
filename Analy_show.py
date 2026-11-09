#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import Counter, defaultdict

import pandas as pd

VOLTAGE_COL = 'rbAdc_DebugData_st.rbAdc_VbatVoltage_u16'
ERRORCOUNTER_COL = 'g_rbRsp_ErrorTableArm.m_value._0_.errorCounter'
OUTPUT_NAMES = {'文件汇总.csv', '汇总.csv', '明细.csv'}   # 输出文件, 扫描时跳过
CHUNK_SIZE = 5000            # 结果CSV分块读取行数, 降低内存占用
DETAIL_COLS = ['序号', '测试目录', '文件', 'time', 'SN', '电压', 'errorCounter', '故障详情']
NEEDED_COLS = ['SN', 'time', '故障', VOLTAGE_COL, ERRORCOUNTER_COL]


class SummaryReportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("4T4R DV测试数据汇总展示工具 @Weifu tools")
        self.root.geometry("640x480")

        self.out_folder = ""
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="OUT文件夹:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.out_entry = ttk.Entry(main_frame, width=60)
        self.out_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="浏览", command=self.select_out_folder).grid(row=0, column=2, pady=5)

        ttk.Label(main_frame,
                  text="说明: 选择Analy筛选结果的OUT目录，递归汇总所有异常结果CSV，生成3个CSV文件：\n文件汇总.csv、汇总.csv（故障类型统计+SN统计）、明细.csv。",
                  foreground='gray').grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=15)
        ttk.Button(button_frame, text="生成汇总报告", command=self.generate_report).pack(side=tk.LEFT, padx=5)

        ttk.Label(main_frame, text="处理日志:", font=('Arial', 10, 'bold')).grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=10)
        self.log_text = tk.Text(main_frame, height=18, width=85)
        self.log_text.grid(row=4, column=0, columnspan=3, pady=5)
        log_scrollbar = ttk.Scrollbar(main_frame, command=self.log_text.yview)
        log_scrollbar.grid(row=4, column=3, sticky=(tk.N, tk.S))
        self.log_text['yscrollcommand'] = log_scrollbar.set

    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def select_out_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.out_folder = folder
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, folder)

    def generate_report(self):
        if not self.out_folder:
            messagebox.showerror("错误", "请选择OUT文件夹")
            return

        # 递归查找OUT下所有结果CSV
        result_files = []
        for dirpath, _, filenames in os.walk(self.out_folder):
            for f in filenames:
                if f.lower().endswith('.csv') and f not in OUTPUT_NAMES:
                    result_files.append(os.path.join(dirpath, f))

        if not result_files:
            self.log("OUT目录下未找到CSV结果文件")
            messagebox.showwarning("警告", "OUT目录下未找到CSV结果文件")
            return

        out_parent = os.path.dirname(os.path.abspath(self.out_folder))
        self.log(f"找到 {len(result_files)} 个结果CSV文件")

        per_file = []         # 文件级汇总
        fault_stats = Counter()
        sn_stats = defaultdict(lambda: {'count': 0, 'files': set(), 'faults': Counter()})

        # 明细边处理边写盘, 避免把全部记录堆在内存里
        detail_path = os.path.join(self.out_folder, '明细.csv')
        detail_written = False
        total = 0

        with open(detail_path, 'w', encoding='utf-8-sig', newline='') as detail_fp:
            for file_path in sorted(result_files):
                rel = os.path.relpath(file_path, self.out_folder)
                dir_rel = os.path.dirname(rel)
                fname = os.path.basename(file_path)
                # 原始数据位于OUT的同级目录下相同相对路径
                orig_path = os.path.join(out_parent, rel)
                orig_exists = os.path.isfile(orig_path)

                file_count = 0
                error = ''
                try:
                    header = pd.read_csv(file_path, nrows=0).columns
                    usecols = [c for c in NEEDED_COLS if c in header]
                    reader = pd.read_csv(file_path, usecols=usecols or None, chunksize=CHUNK_SIZE)
                    for chunk in reader:
                        rows = []
                        for _, row in chunk.iterrows():
                            sn = str(row.get('SN', '')).lstrip('\t').strip() if pd.notna(row.get('SN', '')) else ''
                            fault = str(row.get('故障', '')) if pd.notna(row.get('故障', '')) else ''
                            time_val = row.get('time', '') if pd.notna(row.get('time', '')) else ''
                            volt = row.get(VOLTAGE_COL, '') if pd.notna(row.get(VOLTAGE_COL, '')) else ''
                            ec = row.get(ERRORCOUNTER_COL, '') if pd.notna(row.get(ERRORCOUNTER_COL, '')) else ''

                            rows.append({'序号': total + len(rows) + 1, '测试目录': dir_rel, '文件': fname,
                                         'time': time_val, 'SN': sn, '电压': volt, 'errorCounter': ec,
                                         '故障详情': fault})
                            file_count += 1

                            for item in fault.split('; '):
                                item = item.strip()
                                if not item:
                                    continue
                                ftype = item.split(':')[0] if ':' in item else item
                                fault_stats[ftype] += 1
                                if sn:
                                    sn_stats[sn]['faults'][ftype] += 1
                            if sn:
                                sn_stats[sn]['count'] += 1
                                sn_stats[sn]['files'].add(rel)

                        if rows:
                            pd.DataFrame(rows, columns=DETAIL_COLS).to_csv(
                                detail_fp, index=False, header=not detail_written)
                            detail_written = True
                            total += len(rows)
                except Exception as e:
                    error = str(e)
                    self.log(f"读取 {rel} 失败: {e}")

                per_file.append({'rel': rel, 'dir': dir_rel, 'fname': fname, 'count': file_count,
                                 'error': error, 'path': file_path, 'orig': orig_path, 'orig_ok': orig_exists})
                if not error:
                    self.log(f"{rel}: {file_count}条异常")

        csv_paths = self.build_csvs(per_file, fault_stats, sn_stats, detail_path, detail_written)
        for p in csv_paths:
            self.log(f"已生成: {p}")
        messagebox.showinfo("完成",
                            f"处理完成！\n异常记录共 {total} 条\n\n输出文件:\n" + "\n".join(csv_paths))

    # ---------------- CSV 生成 ----------------

    def build_csvs(self, per_file, fault_stats, sn_stats, detail_path, detail_written):
        paths = []

        # 1. 文件汇总
        file_df = pd.DataFrame(
            [{'序号': i, '测试目录': f['dir'], '结果文件': f['fname'], '异常条数': f['count'],
              '原始数据路径': f['orig'] if f['orig_ok'] else '', '结果CSV路径': f['path'],
              '备注': f['error']} for i, f in enumerate(per_file, 1)],
            columns=['序号', '测试目录', '结果文件', '异常条数', '原始数据路径', '结果CSV路径', '备注'])
        p = os.path.join(self.out_folder, '文件汇总.csv')
        file_df.to_csv(p, index=False, encoding='utf-8-sig')
        paths.append(p)

        # 2. 汇总: 故障类型统计 + SN统计(同一文件内两段)
        fault_df = pd.DataFrame(
            [{'故障类型': k, '出现次数': v} for k, v in sorted(fault_stats.items(), key=lambda x: -x[1])],
            columns=['故障类型', '出现次数'])
        sn_df = pd.DataFrame(
            [{'SN': sn, '异常次数': info['count'], '涉及文件数': len(info['files']),
              '故障分布': ', '.join(f'{k}x{v}' for k, v in info['faults'].most_common())}
             for sn, info in sorted(sn_stats.items(), key=lambda x: -x[1]['count'])],
            columns=['SN', '异常次数', '涉及文件数', '故障分布'])
        p = os.path.join(self.out_folder, '汇总.csv')
        with open(p, 'w', encoding='utf-8-sig', newline='') as fp:
            fp.write(fault_df.to_csv(index=False))
            fp.write('\n')
            fp.write(sn_df.to_csv(index=False))
        paths.append(p)

        # 3. 异常明细: 已在处理过程中分块写入, 无数据时补表头
        if not detail_written:
            pd.DataFrame(columns=DETAIL_COLS).to_csv(detail_path, index=False, encoding='utf-8-sig')
        paths.append(detail_path)

        return paths


def main():
    root = tk.Tk()
    app = SummaryReportApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
