from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
import io
import random
import string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 从环境变量读取secret_key，如果没有则生成一个随机的（仅用于开发）
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'tianzige_secret_key_change_in_production')

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 注册楷体字体（兼容Windows和Linux路径）
FONT_FILENAME = 'simkai.ttf'
FONT_PATH = os.path.join(BASE_DIR, FONT_FILENAME)

try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont('KaiTi', FONT_PATH))
    else:
        # 尝试常见的中文字体路径（Linux系统）
        common_font_paths = [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # 文泉驿正黑
            '/usr/share/fonts/truetype/arphic/uming.ttc',    # AR PL UMing
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', # 文泉驿微米黑
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Noto Sans CJK
        ]
        font_registered = False
        for font_path in common_font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('KaiTi', font_path))
                    font_registered = True
                    print(f"使用系统字体: {font_path}")
                    break
                except Exception as e:
                    print(f"尝试注册字体 {font_path} 失败: {e}")
                    continue
        
        if not font_registered:
            print(f"警告: 未找到字体文件 {FONT_PATH}")
            print("程序将继续运行，但可能无法正确显示中文字符。")
            print("请将 simkai.ttf 字体文件放置在程序目录下，或安装中文字体。")
except Exception as e:
    print(f"注册字体时出错: {e}")
    print("程序将继续运行，但可能无法正确显示中文字符。")

def random_str(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def draw_tianzige(c, x, y, size, border_width: float = 2.0, dash_width: float = 1.0, dash_color=(0,0,0), mode=None):
    cx = x + size/2
    cy = y + size/2
    if mode == 'zitieborder':
        c.setLineWidth(dash_width)
        c.setStrokeColorRGB(*dash_color)
        segs = 5
        gap_ratio = 0.3
        for i in range(segs):
            seg_len = (size/2) / (segs + (segs-1)*gap_ratio)
            gap = seg_len * gap_ratio
            y1 = cy + i * (seg_len + gap)
            y2 = y1 + seg_len
            if y2 <= y + size:
                c.line(cx, y1, cx, y2)
        for i in range(segs):
            seg_len = (size/2) / (segs + (segs-1)*gap_ratio)
            gap = seg_len * gap_ratio
            y1 = cy - i * (seg_len + gap)
            y2 = y1 - seg_len
            if y2 >= y:
                c.line(cx, y1, cx, y2)
        for i in range(segs):
            seg_len = (size/2) / (segs + (segs-1)*gap_ratio)
            gap = seg_len * gap_ratio
            x1 = cx - i * (seg_len + gap)
            x2 = x1 - seg_len
            if x2 >= x:
                c.line(x1, cy, x2, cy)
        for i in range(segs):
            seg_len = (size/2) / (segs + (segs-1)*gap_ratio)
            gap = seg_len * gap_ratio
            x1 = cx + i * (seg_len + gap)
            x2 = x1 + seg_len
            if x2 <= x + size:
                c.line(x1, cy, x2, cy)
        c.setLineWidth(border_width)
        c.setStrokeColorRGB(0,0,0)
        c.rect(x, y, size, size)
        return
    dash = [8, 5]
    c.setLineWidth(dash_width)
    c.setStrokeColorRGB(*dash_color)
    for i in range(10):
        y1 = y + i * size / 10
        y2 = y + (i + 1) * size / 10
        c.setDash(dash)
        c.line(x + size/2, y1, x + size/2, y2)
    for i in range(10):
        x1 = x + i * size / 10
        x2 = x + (i + 1) * size / 10
        c.setDash(dash)
        c.line(x1, y + size/2, x2, y + size/2)
    c.setDash([])
    c.setLineWidth(border_width)
    c.setStrokeColorRGB(0,0,0)
    c.rect(x, y, size, size)

def draw_square(c, x, y, size, border_width: float = 2.0, border_color=(0,0,0)):
    c.setLineWidth(border_width)
    c.setStrokeColorRGB(*border_color)
    c.rect(x, y, size, size)
    c.setStrokeColorRGB(0,0,0)

def generate_single_page(chars):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 20
    size = min(width, height) - 2 * margin
    x = (width - size) / 2
    y = (height - size) / 2
    font_size = int(size * 0.725)
    for char in chars:
        draw_tianzige(c, x, y, size, border_width=4.0, dash_width=3.0, dash_color=(0.2,0.2,0.2))
        c.setFont("KaiTi", font_size)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(width/2, height/2 - size*0.25, char)
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def generate_zi_tie(chars):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    mm = 2.8346
    grid_size = 15 * mm
    gap = 2 * mm
    cols = 12
    rows = 15
    total_grid_h = rows * grid_size + (rows - 1) * gap
    total_grid_w = cols * grid_size
    margin_x = max((width - total_grid_w) / 2, 0)
    margin_y = max((height - total_grid_h) / 2, 0)
    font_size = int(grid_size * 0.725)
    chars = list(chars)
    page_count = (len(chars) + rows - 1) // rows
    char_idx = 0
    for page in range(page_count):
        for row in range(rows):
            if char_idx >= len(chars):
                break
            char = chars[char_idx]
            for col in range(cols):
                gx = margin_x + col * grid_size
                gy = height - margin_y - (row + 1) * grid_size - row * gap
                draw_tianzige(c, gx, gy, grid_size, border_width=2.0, dash_width=1.5, dash_color=(0.3,0.3,0.3), mode='zitieborder')
                if col == 0:
                    c.setFont("KaiTi", font_size)
                    c.setFillColorRGB(0, 0, 0)
                    c.drawCentredString(gx + grid_size/2, gy + grid_size/2 - grid_size*0.25, char)
            char_idx += 1
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def generate_name_per_page(text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(842, 595))
    width, height = 842, 595
    margin = 20
    names = [n.strip() for n in text.split() if n.strip()]
    for name in names:
        n_chars = len(name)
        if n_chars == 0:
            continue
        size = min((width - 2*margin) / n_chars, height - 2*margin)
        font_size = int(size * 0.725)
        y = (height - size) / 2
        start_x = (width - size * n_chars) / 2
        for i, char in enumerate(name):
            gx = start_x + i * size
            draw_tianzige(c, gx, y, size, border_width=4.0, dash_width=3.0, dash_color=(0.2,0.2,0.2))
            c.setFont("KaiTi", font_size)
            c.setFillColorRGB(0, 0, 0)
            c.drawCentredString(gx + size/2, height/2 - size*0.25, char)
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def generate_zi_tie_vertical(chars):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    mm = 2.8346
    grid_size = 15 * mm
    gap = 2 * mm
    cols = 12
    rows = 15
    total_grid_h = rows * grid_size + (rows - 1) * gap
    total_grid_w = cols * grid_size
    margin_x = max((width - total_grid_w) / 2, 0)
    margin_y = max((height - total_grid_h) / 2, 0)
    font_size = int(grid_size * 0.725)
    chars = list(chars)
    page_count = (len(chars) + cols - 1) // cols
    char_idx = 0
    for page in range(page_count):
        # 获取当前页的字符（最多12个）
        page_chars = []
        for col in range(cols):
            if char_idx < len(chars):
                page_chars.append(chars[char_idx])
                char_idx += 1
            else:
                page_chars.append('')  # 空字符占位
        # 绘制当前页
        for col in range(cols):
            char = page_chars[col]
            for row in range(rows):
                gx = margin_x + col * grid_size
                gy = height - margin_y - (row + 1) * grid_size - row * gap
                draw_tianzige(c, gx, gy, grid_size, border_width=2.0, dash_width=1.5, dash_color=(0.5,0.5,0.5), mode='zitieborder')
                # 在第1、6、11行显示范字（如果该列有字符）
                if char and (row == 0 or row == 5 or row == 10):
                    c.setFont("KaiTi", font_size)
                    c.setFillColorRGB(0, 0, 0)
                    c.drawCentredString(gx + grid_size/2, gy + grid_size/2 - grid_size*0.25, char)
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def generate_5x6_mode(chars):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    mm = 2.8346
    cols = 5  # 改为5列
    rows = 6  # 改为6行
    # 计算田字格大小，让总宽度贴边A4纸宽度
    gap = 1.5 * mm  # 间距
    # 计算田字格大小和边距，确保左右边距相等
    margin_x = 10 * mm  # 设置左右边距
    available_width = width - 2 * margin_x
    grid_size = (available_width - (cols - 1) * gap) / cols  # 计算田字格大小
    # 重新计算边距确保居中
    total_grid_width = cols * grid_size + (cols - 1) * gap
    margin_x = (width - total_grid_width) / 2  # 确保左右边距相等
    # 计算总高度和垂直边距
    total_grid_h = rows * grid_size + (rows - 1) * gap
    margin_y = max((height - total_grid_h) / 2, 15 * mm)
    font_size = int(grid_size * 0.725)
    chars = list(chars)
    page_count = (len(chars) + 29) // 30  # 每页30个格子
    char_idx = 0
    for page in range(page_count):
        # 先绘制所有田字格（6行5列）
        for row in range(rows):
            for col in range(cols):
                gx = margin_x + col * (grid_size + gap)
                gy = height - margin_y - (row + 1) * grid_size - row * gap
                # 加重框线、虚线和字体颜色
                draw_tianzige(c, gx, gy, grid_size, border_width=3.0, dash_width=2.5, dash_color=(0.2,0.2,0.2), mode='zitieborder')
        # 再填充字符（从左往右，从上往下）
        for row in range(rows):
            for col in range(cols):
                if char_idx < len(chars):
                    gx = margin_x + col * (grid_size + gap)
                    gy = height - margin_y - (row + 1) * grid_size - row * gap
                    c.setFont("KaiTi", font_size)
                    c.setFillColorRGB(0, 0, 0)  # 纯黑色字体
                    c.drawCentredString(gx + grid_size/2, gy + grid_size/2 - grid_size*0.25, chars[char_idx])
                    char_idx += 1
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def generate_zi_tie_square(chars):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    mm = 2.8346
    grid_size = 15 * mm
    gap = 2 * mm
    cols = 12
    rows = 15
    total_grid_h = rows * grid_size + (rows - 1) * gap
    total_grid_w = cols * grid_size
    margin_x = max((width - total_grid_w) / 2, 0)
    margin_y = max((height - total_grid_h) / 2, 0)
    font_size = int(grid_size * 0.725)
    chars = list(chars)
    page_count = (len(chars) + rows - 1) // rows
    char_idx = 0
    for page in range(page_count):
        for row in range(rows):
            if char_idx >= len(chars):
                break
            char = chars[char_idx]
            for col in range(cols):
                gx = margin_x + col * grid_size
                gy = height - margin_y - (row + 1) * grid_size - row * gap
                draw_square(c, gx, gy, grid_size, border_width=2.0, border_color=(0,0,0))
                if col == 0:
                    c.setFont("KaiTi", font_size)
                    c.setFillColorRGB(0, 0, 0)
                    c.drawCentredString(gx + grid_size/2, gy + grid_size/2 - grid_size*0.25, char)
            char_idx += 1
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        chars = request.form.get('chars', '').strip()
        mode = request.form.get('mode', '1')
        if not chars:
            flash('请输入要生成的汉字或名字！')
            return redirect(url_for('index'))
        if mode == '1':
            pdf_buffer = generate_single_page(chars)
        elif mode == '2':
            pdf_buffer = generate_zi_tie(chars)
        elif mode == '3':
            pdf_buffer = generate_name_per_page(chars)
        elif mode == '4':
            pdf_buffer = generate_zi_tie_vertical(chars)
        elif mode == '5':
            pdf_buffer = generate_5x6_mode(chars)
        elif mode == '6':
            pdf_buffer = generate_zi_tie_square(chars)
        else:
            flash('请选择生成模式！')
            return redirect(url_for('index'))
        # 文件名：前三个字+随机串
        base = chars[:3] if len(chars) >= 3 else chars
        filename = f"{base}{random_str(6)}.pdf"
        filename = secure_filename(filename)
        return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
    return render_template('index.html')

if __name__ == '__main__':
    # 从环境变量读取配置，便于Linux部署
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('FLASK_PORT', '5218'))
    host = os.environ.get('FLASK_HOST', '0.0.0.0')  # 0.0.0.0允许外部访问
    
    print(f"启动服务器: http://{host}:{port}")
    print(f"调试模式: {debug_mode}")
    
    app.run(debug=debug_mode, host=host, port=port) 