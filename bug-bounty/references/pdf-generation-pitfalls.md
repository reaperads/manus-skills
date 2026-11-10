# PDF Generation Pitfalls (fpdf2)

Session-proven pitfalls when generating bug bounty reports as PDFs using fpdf2.

## 1. Unicode Bullets Break Core Fonts

**Error:** `FPDFUnicodeEncodingException: Character "•" at index 0 in text is outside the range of characters supported by the font used: "helvetica".`

**Cause:** `chr(8226)` (bullet "•") is Unicode. Core fonts (Helvetica, Courier, Times) only support Latin-1 (0-255).

**Fix:** Use ASCII alternatives:
```python
# WRONG
self.cell(8, 5.5, chr(8226))  # bullet

# CORRECT
self.cell(8, 5.5, " - ")      # ASCII dash
```

## 2. multi_cell Width After cell()

**Error:** `FPDFException: Not enough horizontal space to render a single character`

**Cause:** After `cell(indent, ...)`, the cursor X position shifts right. `multi_cell(0, ...)` with width=0 calculates from current X to page edge, which may be too narrow.

**Fix:** Calculate remaining width explicitly:
```python
# WRONG
self.cell(indent, 5.5, " - ")
self.multi_cell(0, 5.5, text)  # fails if cursor is far right

# CORRECT
self.cell(indent, 5.5, " - ")
remaining_width = self.w - self.r_margin - self.get_x()
self.multi_cell(remaining_width, 5.5, text)
```

## 3. No Unicode in Core Fonts

Helvetica, Courier, Times cannot render: bullets (•), em-dash (—), en-dash (–), non-breaking spaces (\xa0), curly quotes (' ' " "), emoji, CJK, etc.

**Blanket fix — replace ALL problematic chars before running:**
```python
replacements = {
    '\u2014': '--',  # em-dash
    '\u2013': '-',   # en-dash
    '\u2018': "'",   # left single quote
    '\u2019': "'",   # right single quote
    '\u201c': '"',   # left double quote
    '\u201d': '"',   # right double quote
    '\u2022': '-',   # bullet
    '\u2026': '...',  # ellipsis
    '\u00b7': '-',   # middle dot
}
for old, new in replacements.items():
    content = content.replace(old, new)
```

**Specific pitfall:** Em-dash `\u2014` is common in English text ("Target -- Aptos L1"). It silently breaks PDF generation with `FPDFUnicodeEncodingException`. Always do the blanket replacement pass on the ENTIRE script content before execution.

## 4. Forbidden Words Verification

After generating PDF, verify no AI/agent attribution leaked:
```python
import subprocess
r = subprocess.run(['pdftotext', 'output.pdf', '-'], capture_output=True, text=True)
text = r.stdout.lower()
forbidden = ["agent", "hermes", "qwen"]
for word in forbidden:
    if word in text:
        raise ValueError(f"FORBIDDEN WORD FOUND: {word}")
```

## 5. Screenshot Integration

```python
# Check if enough space for image + caption
if self.get_y() > 200:
    self.add_page()

self.image(path, x=(self.w - width) / 2, w=width)
self.ln(2)
self.set_font("Helvetica", "I", 9)
self.set_text_color(100, 100, 100)
self.cell(0, 5, caption, align="C", new_x="LMARGIN", new_y="NEXT")
```

## 6. Page Break Handling

```python
self.set_auto_page_break(auto=True, margin=20)
# Or manually:
if self.get_y() > 250:
    self.add_page()
```
