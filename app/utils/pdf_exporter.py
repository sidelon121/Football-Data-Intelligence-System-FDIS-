import os
import re
import tempfile
from fpdf import FPDF
from plotly import data

# 🔥 FIX: Biarkan Plotly (update_layout) yang menentukan ukuran asli, jangan dipaksa!
def save_chart_as_image(fig):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.write_image(temp.name) 
    return temp.name

# =======================================================
# SAFE TEXT (ANTI ERROR FPDF)
# =======================================================
def safe_text(text):
    if not text:
        return ""
    text = str(text)
    text = text.replace("•", "-").replace("\u2022", "-").replace("\u25CF", "-")
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# =======================================================
# 🏆 ARSITEKTUR KELAS PDF
# =======================================================
class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font("Arial", "B", 16)
            self.cell(0, 10, "FOOTBALL DATA REPORT", ln=True, align="C")
            self.set_font("Arial", "", 10)
            self.cell(0, 5, "by SIDELON121", ln=True, align="C")
            self.ln(10)
        self.ln(5)

    def watermark(self):
        self.set_text_color(220, 220, 220)
        self.set_font("Arial", "B", 50)
        page_width = self.w
        page_height = self.h
        current_x = self.get_x()
        current_y = self.get_y()

        self.set_xy(0, page_height / 2)
        self.cell(page_width, 10, "SIDELON121", align="C")

        self.set_xy(current_x, current_y)
        self.set_text_color(0, 0, 0)
        
        # 🔥 FIX: Kunci anti-font-leak! Wajib dikembalikan ke 10
        self.set_font("Arial", "", 10) 

    def add_page(self, *args, **kwargs):
        super().add_page(*args, **kwargs)
        self.watermark()

    def section_header(self, title):
        self.set_font("Arial", "B", 14)
        self.set_text_color(102, 126, 234)
        self.cell(0, 10, safe_text(title.upper()), ln=True)
        self.set_draw_color(102, 126, 234)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.set_text_color(0, 0, 0)
        self.ln(5)

    def section_title(self, title):
        self.ln(6)
        self.set_font("Arial", "B", 12)
        self.set_text_color(26, 26, 46)
        self.cell(0, 8, safe_text(title), ln=True, align="L")
        self.ln(2)

    def section_text(self, text):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, safe_text(text))
        self.ln(2)

    def stat_bar(self, label, home, away):
        total = home + away if (home + away) != 0 else 1

        home_width = 180 * (home / total)
        away_width = 180 * (away / total)

        self.set_font("Arial", "B", 10)
        self.cell(0, 4, label, ln=True)

        # Home (biru)
        self.set_fill_color(0, 123, 255)
        self.cell(home_width, 4, f"{round(home,2)}", fill=True)

        # Away (merah)
        self.set_fill_color(220, 53, 69)
        self.cell(away_width, 4, f"{round(away,2)}", fill=True)

        self.ln(6)
    def add_chart(self, image_path):
        if os.path.exists(image_path):
            self.ln(5)
            self.image(image_path, w=180)
    
    def stat_vs_bar(self, label, home, away):
        total = home + away if (home + away) != 0 else 1

        home_ratio = home / total
        away_ratio = away / total

        bar_width = 180
        bar_height = 3

        start_x = 20
        y = self.get_y()

        # Label
        self.set_font("Arial", "B", 8)
        self.set_xy(start_x, y)
        self.cell(bar_width, 3, label, align="C")
        self.ln(3)

        # Values``
        self.set_font("Arial", "", 8)
        y = self.get_y()
        self.set_xy(start_x, y)
        self.cell(11, 6, str(home), align="L")
        self.set_xy(start_x + bar_width - 10, y)
        self.cell(11, 6, str(away), align="R")

        # Bar background
        y_bar = y + 1
        self.set_fill_color(240, 240, 240)
        self.rect(start_x + 15, y_bar, bar_width - 30, bar_height, 'F')

        # Home Bar
        self.set_fill_color(102, 126, 234) # Primary
        self.rect(start_x + 15, y_bar, (bar_width - 30) * home_ratio, bar_height, 'F')

        # Away Bar
        self.set_fill_color(118, 75, 162) # Secondary
        self.rect(start_x + 15 + (bar_width - 30) * home_ratio, y_bar, (bar_width - 30) * away_ratio, bar_height, 'F')

        self.ln(5)


    def draw_table(self, headers, rows, col_widths):
        self.set_font("Arial", "B", 9)
        self.set_fill_color(245, 245, 245)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, str(h), border=1, fill=True, align="C")
        self.ln()

        self.set_font("Arial", "", 9)
        for row in rows:
            for i, val in enumerate(row):
                self.cell(col_widths[i], 7, str(val), border=1, align="C")
            self.ln()
        self.ln(5)

    # 🔥 FIX: Fungsi canggih untuk merender AI teks agar tebal (**) tercetak otomatis dan stabil
    def render_ai_analysis(self, text):
        text = str(text).replace('•', '-').replace('\u2022', '-').replace('\u25CF', '-')
        text = text.encode('latin-1', 'ignore').decode('latin-1')

        clean_text = text.replace("\r", "")
        analysis_lines = clean_text.split("\n")

        for line in analysis_lines:
            line = line.strip()
            if not line:
                self.ln(2)
                continue
            
            is_bullet = line.startswith("-") or line.startswith("*")
            is_header = line.startswith("**") and line.endswith("**") or line.endswith(":")
            clean_line = line.replace("**", "")

            if is_header:
                self.ln(3)
                self.set_font("Arial", "B", 11)
                self.set_text_color(26, 26, 46)
                self.multi_cell(0, 6, clean_line)
            elif is_bullet:
                self.set_font("Arial", "", 10)
                self.set_text_color(50, 50, 50) 
                self.set_x(15) 
                self.multi_cell(0, 5, f"- {clean_line.lstrip('-* ').strip()}")
            else:
                self.set_font("Arial", "", 10)
                self.set_text_color(50, 50, 50) 
                self.set_x(10)
                self.multi_cell(0, 5, clean_line)
            self.ln(1)

    def image(self, name, x=None, y=None, w=0, h=0, type='', link=''):
        super().image(name, x, y, w, h, type, link)

def create_pdf():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    return pdf