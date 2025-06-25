import os
import sys
import datetime
import pandas as pd
from datetime import timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
from reportlab.lib import colors


def draw_layout(pdf_path, csv_parent_dir):
    # Register Audiowide font
    script_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(script_dir, 'Audiowide.ttf')
    if os.path.isfile(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Audiowide', font_path))
        except:
            pass

    # Initialize PDF canvas
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Title: Satake Enpresor Data Report
    title_size = 24
    x_center = width / 2
    satake = "Satake "
    enpresor = "Enpresor"
    data_rep = " Data Report"
    font_default = 'Helvetica-Bold'
    font_enpresor = 'Audiowide' if 'Audiowide' in pdfmetrics.getRegisteredFontNames() else font_default
    w_sat = c.stringWidth(satake, font_default, title_size)
    w_enp = c.stringWidth(enpresor, font_enpresor, title_size)
    w_dat = c.stringWidth(data_rep, font_default, title_size)
    start_x = x_center - (w_sat + w_enp + w_dat) / 2
    y_title = height - 50
    c.setFont(font_default, title_size)
    c.setFillColor(colors.black)
    c.drawString(start_x, y_title, satake)
    c.setFont(font_enpresor, title_size)
    c.setFillColor(colors.red)
    c.drawString(start_x + w_sat, y_title, enpresor)
    c.setFont(font_default, title_size)
    c.setFillColor(colors.black)
    c.drawString(start_x + w_sat + w_enp, y_title, data_rep)

    # Date stamp
    date_str = datetime.datetime.now().strftime('%m/%d/%Y')
    c.setFont('Helvetica', 10)
    c.setFillColor(colors.black)
    c.drawCentredString(x_center, height - 70, date_str)

    # Layout margins
    margin = 40
    content_offset = 100
    x0, y0 = margin, margin
    x1, y1 = width - margin, height - content_offset
    total_w, total_h = x1 - x0, y1 - y0

    # Section dimensions and splits
    h1 = total_h * 0.1
    h2 = total_h * 0.3
    h3 = total_h * 0.15 * 0.8  # Section 4 height reduced by 20%
    h4 = total_h - (h1 + h2 + h3)
    y_sec1 = y0 + total_h - h1
    y_sec2 = y_sec1 - h2
    y_sec3 = y_sec2 - h3
    w_left = total_w * 0.4
    w_right = total_w * 0.6

    # Aggregate 24h data across all machines
    machines = sorted([d for d in os.listdir(csv_parent_dir)
                       if os.path.isdir(os.path.join(csv_parent_dir, d)) and d.isdigit()])
    total_processed = total_accepts = total_rejects = 0
    for m in machines:
        path = os.path.join(csv_parent_dir, m, 'last_24h_metrics.csv')
        if os.path.isfile(path):
            df = pd.read_csv(path)
            total_processed += df['capacity'].sum() if 'capacity' in df.columns else 0
            ac = next((col for col in df.columns if col.lower()=='accepts'), None)
            rj = next((col for col in df.columns if col.lower()=='rejects'), None)
            if ac: total_accepts += df[ac].sum()
            if rj: total_rejects += df[rj].sum()

    # Section 1: Production totals
    c.setFillColor(colors.HexColor('#1f77b4'))
    c.rect(x0, y_sec1, total_w, h1, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 10)
    c.drawString(x0+10, y_sec1+h1-14, '24hr Production Totals:')
    labels = ['Processed:', 'Accepted:', 'Rejected:']
    values = [f"{int(total_processed):,} lbs", f"{int(total_accepts):,} lbs", f"{int(total_rejects):,} lbs"]
    third = total_w/3
    c.setFont('Helvetica-Bold', 12)
    for i, lab in enumerate(labels):
        lw = c.stringWidth(lab, 'Helvetica-Bold', 12)
        x_lab = x0 + third*i + (third - lw)/2
        y_lab = y_sec1 + h1/2 - 4
        c.drawString(x_lab, y_lab, lab)
    c.setFont('Helvetica-Bold', 14)
    for i, val in enumerate(values):
        vw = c.stringWidth(val, 'Helvetica-Bold', 14)
        x_val = x0 + third*i + (third - vw)/2
        y_val = y_sec1 + h1/2 - 22
        c.drawString(x_val, y_val, val)

    # Section 4: Counts
    c.setFillColor(colors.HexColor('#1f77b4'))
    c.rect(x0, y_sec3, total_w, h3, stroke=0, fill=1)
    total_objects = total_removed = 0
    for m in machines:
        path = os.path.join(csv_parent_dir, m, 'last_24h_metrics.csv')
        if os.path.isfile(path):
            df = pd.read_csv(path)
            total_objects += df['objects_per_min'].sum() if 'objects_per_min' in df.columns else 0
            for i in range(1,13):
                col = next((c for c in df.columns if c.lower()==f'counter_{i}'), None)
                if col: total_removed += df[col].sum()
    c.setFillColor(colors.white); c.setFont('Helvetica-Bold', 10)
    c.drawString(x0+10, y_sec3+h3-14, 'Counts:')
    labels4 = ['Total Objects Processed:', 'Total Impurities Removed:']
    values4 = [f"{int(total_objects):,}", f"{int(total_removed):,}"]
    half = total_w/2
    c.setFont('Helvetica-Bold', 12)
    for idx, lab in enumerate(labels4):
        lw = c.stringWidth(lab, 'Helvetica-Bold', 12)
        x_lab = x0 + half*idx + (half-lw)/2
        c.drawString(x_lab, y_sec3+h3/2+8, lab)
    c.setFont('Helvetica-Bold', 14)
    for idx, val in enumerate(values4):
        vw = c.stringWidth(val, 'Helvetica-Bold', 14)
        x_val = x0 + half*idx + (half-vw)/2
        c.drawString(x_val, y_sec3+h3/2-14, val)
    c.setFillColor(colors.black)

    # Section 5: First machine pie
    if machines:
        first = machines[0]
        path = os.path.join(csv_parent_dir, first, 'last_24h_metrics.csv')
        if os.path.isfile(path):
            df0 = pd.read_csv(path)
            ac0 = next((col for col in df0.columns if col.lower()=='accepts'), None)
            rj0 = next((col for col in df0.columns if col.lower()=='rejects'), None)
            accepts0 = df0[ac0].sum() if ac0 else 0
            rejects0 = df0[rj0].sum() if rj0 else 0
            x5, y5 = x0, y0; w5, h5 = w_left, h4
            c.setFont('Helvetica-Bold', 12); c.setFillColor(colors.black)
            c.drawString(x5+10, y5+h5-15, f"Machine {first}")
            pad5, ts5 = 10, 20
            aw5, ah5 = w5-2*pad5, h5-2*pad5-ts5
            psz5 = min(aw5, ah5)*0.8
            px5 = x5+pad5 + (aw5-psz5)/2
            py5 = y5+pad5 + ts5 + (ah5-psz5)/2
            if accepts0 + rejects0 > 0:
                d5 = Drawing(psz5, psz5); p5 = Pie()
                p5.x = p5.y = 0; p5.width = p5.height = psz5
                p5.data = [accepts0, rejects0]; p5.labels=['Accepts','Rejects']
                p5.slices[0].fillColor=colors.green; p5.slices[1].fillColor=colors.red
                p5.sideLabels=True; d5.add(p5); renderPDF.draw(d5, c, px5, py5)

    # Draw section borders
    c.setStrokeColor(colors.black)
    c.rect(x0, y_sec1, total_w, h1)
    c.rect(x0, y_sec2, w_left, h2)
    c.rect(x0 + w_left, y_sec2, w_right, h2)
    c.rect(x0, y_sec3, total_w, h3)
    c.rect(x0, y0, w_left, h4)
    rt_h = h4/2
    c.rect(x0 + w_left, y0 + rt_h, w_right, rt_h)
    c.rect(x0 + w_left, y0, w_right, rt_h)

    c.showPage(); c.save()
    print(f"Layout saved at: {os.path.abspath(pdf_path)}")

if __name__ == '__main__':
    sd = os.path.dirname(os.path.abspath(__file__))
    pdf_arg = sys.argv[1] if len(sys.argv)>1 else 'layout.pdf'
    exp_arg = sys.argv[2] if len(sys.argv)>2 else os.path.join(sd,'exports')
    pdf_path = pdf_arg if os.path.isabs(pdf_arg) else os.path.join(sd,pdf_arg)
    draw_layout(pdf_path, exp_arg)
