#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from collections import Counter, defaultdict
from html import escape

import pandas as pd

VOLTAGE_COL = 'rbAdc_DebugData_st.rbAdc_VbatVoltage_u16'
ERRORCOUNTER_COL = 'g_rbRsp_ErrorTableArm.m_value._0_.errorCounter'


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
                  text="说明: 选择Analy筛选结果的OUT目录，递归汇总所有异常结果CSV，生成HTML汇总报告，\n报告中可查看目录、文件及异常明细，并支持复制文件完整路径。",
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
                if f.lower().endswith('.csv'):
                    result_files.append(os.path.join(dirpath, f))

        if not result_files:
            self.log("OUT目录下未找到CSV结果文件")
            messagebox.showwarning("警告", "OUT目录下未找到CSV结果文件")
            return

        out_parent = os.path.dirname(os.path.abspath(self.out_folder))
        self.log(f"找到 {len(result_files)} 个结果CSV文件")

        records = []          # 明细记录
        per_file = []         # 文件级汇总
        fault_stats = Counter()
        sn_stats = defaultdict(lambda: {'count': 0, 'files': set(), 'faults': Counter()})

        for file_path in sorted(result_files):
            rel = os.path.relpath(file_path, self.out_folder)
            dir_rel = os.path.dirname(rel)
            fname = os.path.basename(file_path)
            # 原始数据位于OUT的同级目录下相同相对路径
            orig_path = os.path.join(out_parent, rel)
            orig_exists = os.path.isfile(orig_path)

            file_count = 0
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                self.log(f"读取 {rel} 失败: {e}")
                per_file.append({'rel': rel, 'dir': dir_rel, 'fname': fname, 'count': 0,
                                 'error': str(e), 'path': file_path, 'orig': orig_path, 'orig_ok': orig_exists})
                continue

            for _, row in df.iterrows():
                sn = str(row.get('SN', '')).lstrip('\t').strip() if pd.notna(row.get('SN', '')) else ''
                fault = str(row.get('故障', '')) if pd.notna(row.get('故障', '')) else ''
                time_val = row.get('time', '') if pd.notna(row.get('time', '')) else ''
                volt = row.get(VOLTAGE_COL, '') if VOLTAGE_COL in df.columns and pd.notna(row.get(VOLTAGE_COL, '')) else ''
                ec = row.get(ERRORCOUNTER_COL, '') if ERRORCOUNTER_COL in df.columns and pd.notna(row.get(ERRORCOUNTER_COL, '')) else ''

                records.append({'dir': dir_rel, 'fname': fname, 'time': time_val, 'sn': sn,
                                'volt': volt, 'ec': ec, 'fault': fault,
                                'path': file_path, 'orig': orig_path, 'orig_ok': orig_exists})
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

            per_file.append({'rel': rel, 'dir': dir_rel, 'fname': fname, 'count': file_count,
                             'error': '', 'path': file_path, 'orig': orig_path, 'orig_ok': orig_exists})
            self.log(f"{rel}: {file_count}条异常")

        html_path = os.path.join(self.out_folder, '汇总报告.html')
        self.build_html(html_path, records, per_file, fault_stats, sn_stats)
        self.log(f"\n汇总报告已生成: {html_path}")
        messagebox.showinfo("完成", f"处理完成！\n异常记录共 {len(records)} 条\n\n报告位置: {html_path}")

    # ---------------- HTML 生成 ----------------

    def copy_btn(self, path, ok=True):
        """生成 复制路径 按钮"""
        if not ok:
            return '<span class="missing">缺失</span>'
        return f'<button class="copy" data-path="{escape(path)}" title="复制完整路径, 可粘贴到Excel打开">复制路径</button>'

    def fname_cell(self, path, name):
        """文件名单元格: 纯文本显示, 悬停提示完整路径"""
        return f'<span title="{escape(path)}">{escape(name)}</span>'

    def fault_html(self, fault):
        # Active故障标红, History标橙
        parts = []
        for item in fault.split('; '):
            item = item.strip()
            if not item:
                continue
            if '(Active)' in item:
                parts.append(f'<span class="fault-active">{escape(item)}</span>')
            elif '(History)' in item:
                parts.append(f'<span class="fault-history">{escape(item)}</span>')
            else:
                parts.append(escape(item))
        return '; '.join(parts)

    def build_html(self, html_path, records, per_file, fault_stats, sn_stats):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        files_with_error = sum(1 for f in per_file if f['count'] > 0)

        # 文件汇总表
        file_rows = ''
        for i, f in enumerate(per_file, 1):
            err = f'<br><span class="missing">读取失败:{escape(f["error"])}</span>' if f['error'] else ''
            count_cell = f'<span class="bad">{f["count"]}</span>' if f['count'] else '<span class="ok">0</span>'
            file_rows += f'''<tr>
<td>{i}</td><td>{escape(f['dir'])}</td>
<td>{self.fname_cell(f['path'], f['fname'])}{err}</td>
<td>{count_cell}</td>
<td>{self.copy_btn(f['orig'], f['orig_ok'])}</td>
<td>{self.copy_btn(f['path'])}</td>
</tr>'''

        # 故障类型统计
        fault_rows = ''
        for ftype, cnt in sorted(fault_stats.items(), key=lambda x: -x[1]):
            fault_rows += f'<tr><td>{escape(ftype)}</td><td>{cnt}</td></tr>'

        # SN统计
        sn_rows = ''
        for sn, info in sorted(sn_stats.items(), key=lambda x: -x[1]['count']):
            faults = ', '.join(f'{k}x{v}' for k, v in info['faults'].most_common())
            sn_rows += f'''<tr><td>{escape(sn)}</td><td>{info['count']}</td><td>{len(info['files'])}</td><td>{escape(faults)}</td></tr>'''

        # 异常明细
        detail_rows = ''
        for i, r in enumerate(records, 1):
            detail_rows += f'''<tr>
<td>{i}</td><td>{escape(r['dir'])}</td>
<td>{self.fname_cell(r['path'], r['fname'])}</td>
<td>{escape(str(r['time']))}</td><td>{escape(r['sn'])}</td>
<td>{escape(str(r['volt']))}</td><td>{escape(str(r['ec']))}</td>
<td>{self.fault_html(r['fault'])}</td>
</tr>'''

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>4T4R DV测试数据汇总报告</title>
<style>
body {{ font-family: "Microsoft YaHei", Arial, sans-serif; margin: 20px; background: #f5f6f8; color: #333; }}
h1 {{ font-size: 22px; }} h2 {{ font-size: 17px; margin-top: 30px; border-left: 4px solid #2d6cdf; padding-left: 8px; }}
.meta {{ color: #666; font-size: 13px; }}
.cards {{ display: flex; gap: 15px; margin: 15px 0; flex-wrap: wrap; }}
.card {{ background: #fff; border-radius: 8px; padding: 12px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); min-width: 120px; }}
.card .num {{ font-size: 26px; font-weight: bold; color: #2d6cdf; }}
.card .num.bad {{ color: #d93025; }}
.card .lbl {{ font-size: 13px; color: #777; }}
table {{ border-collapse: collapse; width: 100%; background: #fff; font-size: 13px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; vertical-align: top; }}
th {{ background: #2d6cdf; color: #fff; position: sticky; top: 0; }}
tr:nth-child(even) {{ background: #f9fafb; }}
button.copy {{ font-size: 12px; padding: 1px 8px; cursor: pointer; border: 1px solid #ccc; border-radius: 4px; background: #fff; }}
button.copy:hover {{ background: #f1f3f4; }}
.bad {{ color: #d93025; font-weight: bold; }} .ok {{ color: #188038; }}
.missing {{ color: #999; }}
.fault-active {{ color: #d93025; font-weight: bold; }}
.fault-history {{ color: #e8710a; }}
#filter {{ padding: 6px 10px; width: 300px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; }}
</style>
</head>
<body>
<h1>4T4R DV测试数据汇总报告</h1>
<p class="meta">生成时间: {now} &nbsp;|&nbsp; OUT目录: {escape(self.out_folder)}</p>

<div class="cards">
<div class="card"><div class="num">{len(per_file)}</div><div class="lbl">结果文件数</div></div>
<div class="card"><div class="num">{files_with_error}</div><div class="lbl">有异常文件数</div></div>
<div class="card"><div class="num bad">{len(records)}</div><div class="lbl">异常记录总数</div></div>
<div class="card"><div class="num">{len(sn_stats)}</div><div class="lbl">涉及SN数</div></div>
</div>

<h2>1. 文件汇总</h2>
<p class="meta">悬停文件名可查看完整路径；「复制路径」复制完整路径后可直接在Excel中打开。原始数据为OUT同级目录下相同相对路径的CSV。</p>
<table>
<tr><th>#</th><th>测试目录</th><th>结果文件</th><th>异常条数</th><th>原始数据</th><th>结果CSV</th></tr>
{file_rows}
</table>

<h2>2. 故障类型统计</h2>
<table>
<tr><th>故障类型</th><th>出现次数</th></tr>
{fault_rows if fault_rows else '<tr><td colspan="2">无</td></tr>'}
</table>

<h2>3. SN统计</h2>
<table>
<tr><th>SN</th><th>异常次数</th><th>涉及文件数</th><th>故障分布</th></tr>
{sn_rows if sn_rows else '<tr><td colspan="4">无</td></tr>'}
</table>

<h2>4. 异常明细</h2>
<input id="filter" type="text" placeholder="输入关键字过滤（如SN、EventID、目录名）..." onkeyup="filterRows()">
<table id="detail">
<tr><th>#</th><th>测试目录</th><th>文件</th><th>time</th><th>SN</th><th>电压</th><th>errorCounter</th><th>故障详情</th></tr>
{detail_rows if detail_rows else '<tr><td colspan="8">无异常记录</td></tr>'}
</table>

<script>
function filterRows() {{
  var kw = document.getElementById('filter').value.toLowerCase();
  var rows = document.querySelectorAll('#detail tr');
  for (var i = 1; i < rows.length; i++) {{
    rows[i].style.display = rows[i].innerText.toLowerCase().indexOf(kw) >= 0 ? '' : 'none';
  }}
}}
document.querySelectorAll('button.copy').forEach(function(btn) {{
  btn.addEventListener('click', function() {{
    var p = this.dataset.path;
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(p);
    }} else {{
      var ta = document.createElement('textarea');
      ta.value = p; document.body.appendChild(ta); ta.select();
      document.execCommand('copy'); document.body.removeChild(ta);
    }}
    var b = this; b.textContent = '已复制';
    setTimeout(function() {{ b.textContent = '复制路径'; }}, 1200);
  }});
}});
</script>
</body>
</html>'''

        with open(html_path, 'w', encoding='utf-8') as fp:
            fp.write(html)


def main():
    root = tk.Tk()
    app = SummaryReportApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
