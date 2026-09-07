# -*- mode: python ; coding: utf-8 -*-

# 程序实际依赖: pandas(→numpy/dateutil/pytz/tzdata/packaging) + tkinter + 标准库
# 以下excludes按环境pip清单裁剪, 防止pandas钩子顺带拉入无关大库

a = Analysis(
    ['Analy_show.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 绘图/图像/科学计算: pandas钩子会顺带拉入matplotlib(+PIL/contourpy等)
        'matplotlib',
        'PIL',                 # pillow 的导入名
        'scipy',
        'contourpy',
        # 样式模板: 仅pandas.io.formats.style使用, 本工具不导出styled表格
        'jinja2',
        # GUI框架(已有tkinter)
        'IPython',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',
        # Web框架(fastapi全家桶)
        'fastapi', 'uvicorn', 'starlette', 'rich', 'pydantic',
        # CAN/诊断类车载库(pip里装了但本工具不用)
        'pyxcp',               # 导入名 pyxcp, 依赖Mako/uptime
        'can',                 # python-can 的导入名, 依赖serial/usb/can_isotp
        'can_isotp',           # can-isotp 的导入名
        'serial',              # pyserial 的导入名
        'usb',                 # pyusb 的导入名
        'canlib',
        'cantools',
        # 开发/调试工具类
        'bandit', 'stevedore', 'line_profiler', 'line_profiler_pycharm',
        'pyelftools', 'altgraph', 'pefile', 'psutil', 'pyreadline3',
        'traitlets', 'wrapt',
        # pandas Excel写出(本工具只用read_csv)
        'xlsxwriter',
        # 标准库中不需要的大模块
        'sqlite3', 'ssl', 'pydoc_data', 'lib2to3', 'test',
        'setuptools', 'pkg_resources',
        # PyInstaller钩子包仅构建期使用, 无需打入
        'pyinstaller_hooks_contrib',
    ],
    noarchive=False,
    optimize=0,                # 不能设为2: 会剥离docstring, numpy启动即崩(TypeError: add_docstring)
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Analy_show',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
