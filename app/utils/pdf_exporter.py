from fpdf import FPDF

class PDF(FPDF):

    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'FDIS Report', border=0, ln=1, align='C')
        self.ln(5)

    def section_title(self, title):
        self.ln(4)
        self.set_font('Arial', 'B', 12)

        title = clean_text(title)

        self.cell(0, 8, title, ln=True)
    def section_text(self, text):
        self.set_font('Arial', '', 10)
        self.set_x(10)

        text = clean_text(text)

        self.multi_cell(0, 6, text)
        self.ln(2)

    # reset posisi biar aman
        self.set_x(10)

    # pastikan teks string
        text = str(text)

    # potong kalau terlalu panjang (anti crash)
        if len(text) > 5000:
            text = text[:5000] + "..."

        self.multi_cell(0, 6, text)
        self.ln(2)

def create_pdf():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    return pdf

def clean_text(text):
    if not text:
        return ""

    text = str(text)

    replacements = {
        "–": "-",   # en dash
        "—": "-",   # em dash
        "“": '"',
        "”": '"',
        "’": "'",
        "‘": "'",
        "•": "-",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    # hapus karakter aneh lainnya
    return text.encode('latin-1', 'ignore').decode('latin-1')