# -*- coding: utf-8 -*-
"""
build_cv.py — renders cv.html into the two downloadable PDFs, then audits them.

    py tools/build_cv.py

Produces:
    CV/CV_Dawid_Majewski.pdf      (PL — cv.html)
    CV/CV_Dawid_Majewski_EN.pdf   (EN — cv.html?lang=en)

WHY THIS SCRIPT EXISTS INSTEAD OF "print to PDF from the browser":
  1. Chrome's own print dialog adds headers/footers and its own margins; --no-pdf-header-footer
     with @page{margin:0} is the only way to get an edge-to-edge A4 that matches the design.
  2. Chrome cannot write PDF metadata. /Title and /Author are what a recruiter's file manager,
     an ATS and Acrobat show instead of the file name — pypdf stamps them afterwards.
  3. The audit at the end is not decoration. It is the regression test for the one defect that
     silently destroys this document: Polish characters that extract as "Wyra ż am zgod ę".
     If it ever prints MISS, the fonts have been switched back to a webfont/<link> — read the
     comment at the top of cv.html before touching anything else.

REQUIREMENTS: Google Chrome, pypdf  (py -m pip install pypdf)
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "cv.html")
OUT_DIR = os.path.join(ROOT, "CV")

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

BUILDS = [
    {
        "lang": "pl",
        "query": "",
        "pdf": "CV_Dawid_Majewski.pdf",
        "title": "CV — Dawid Majewski",
        "subject": "CV — student informatyki II stopnia (SI i uczenie maszynowe), "
                   "infrastruktura IT, sieci, ERP",
        "keywords": ("Dawid Majewski, CV, informatyka, sztuczna inteligencja, uczenie maszynowe, "
                     "machine learning, YOLOv8, Raspberry Pi, Python, SQL, Power BI, ERP, helpdesk, "
                     "infrastruktura IT, LAN/WAN, Microsoft 365, junior IT"),
        # every one of these must survive text extraction, diacritics intact
        "checks": ["Wyrażam zgodę", "Doświadczenie", "Umiejętności", "Wykształcenie",
                   "dawid.majewski.it@gmail.com", "607 250 449", "YOLOv8n", "Raspberry Pi",
                   "ERP", "Python", "Merito", "art. 6 ust. 1 lit. a RODO"],
    },
    {
        "lang": "en",
        "query": "?lang=en",
        "pdf": "CV_Dawid_Majewski_EN.pdf",
        "title": "CV — Dawid Majewski",
        "subject": "CV — MSc Computer Science student (AI & Machine Learning), "
                   "IT infrastructure, networks, ERP",
        "keywords": ("Dawid Majewski, CV, resume, computer science, artificial intelligence, "
                     "machine learning, YOLOv8, Raspberry Pi, Python, SQL, Power BI, ERP, helpdesk, "
                     "IT infrastructure, LAN/WAN, Microsoft 365, junior IT"),
        "checks": ["I consent to the processing", "Professional experience", "Education",
                   "dawid.majewski.it@gmail.com", "607 250 449", "YOLOv8n", "Raspberry Pi",
                   "ERP", "Python", "Merito", "Article 6(1)(a) GDPR"],
    },
]


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.isfile(p):
            return p
    sys.exit("Chrome not found. Edit CHROME_CANDIDATES in this script.")


def render(chrome, query, out_pdf):
    url = "file:///" + SRC.replace("\\", "/") + query
    subprocess.run(
        [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--force-color-profile=srgb", "--run-all-compositor-stages-before-draw",
         # the fonts are local files; give the load a real budget or Chrome prints
         # the fallback face and every line breaks somewhere else
         "--virtual-time-budget=10000",
         "--no-pdf-header-footer", "--print-to-pdf=" + out_pdf, url],
        check=True, capture_output=True,
    )


def stamp(pdf_path, spec):
    from pypdf import PdfReader, PdfWriter
    r = PdfReader(pdf_path)
    w = PdfWriter()
    for page in r.pages:
        w.add_page(page)
    w.add_metadata({
        "/Title": spec["title"],
        "/Author": "Dawid Majewski",
        "/Subject": spec["subject"],
        "/Keywords": spec["keywords"],
        "/Creator": "cv.html",
        "/Producer": "Chrome (Skia/PDF) + pypdf",
    })
    with open(pdf_path, "wb") as fh:
        w.write(fh)


def audit(pdf_path, spec):
    from pypdf import PdfReader
    r = PdfReader(pdf_path)
    ok = True

    pages = len(r.pages)
    print(f"    pages          : {pages} {'OK' if pages == 1 else '<-- FAIL, must be 1'}")
    ok &= pages == 1

    page = r.pages[0]
    fonts = page.get("/Resources", {}).get("/Font", {})
    type3 = []
    for k in list(fonts.keys()):
        f = fonts[k].get_object()
        if f.get("/Subtype") == "/Type3":
            type3.append(str(f.get("/BaseFont", "?")))
    print(f"    embedded fonts : {len(fonts)}"
          + (f"  <-- FAIL: {len(type3)} Type3 (no Unicode map)" if type3 else "  (all Type0)"))
    ok &= not type3

    links = 0
    for a in page.get("/Annots", []) or []:
        if a.get_object().get("/A", {}).get("/URI"):
            links += 1
    print(f"    live links     : {links} (mailto / tel / github / linkedin / portfolio)")

    text = page.extract_text() or ""
    flat = re.sub(r"\s+", " ", text)
    missing = [c for c in spec["checks"] if c.lower() not in flat.lower()]
    if missing:
        ok = False
        print("    text extraction: FAIL — an ATS cannot find:")
        for m in missing:
            print(f"                       MISS  {m!r}")
    else:
        print(f"    text extraction: OK — all {len(spec['checks'])} key strings found, "
              f"diacritics intact ({len(text)} chars)")
    return ok


def main():
    chrome = find_chrome()
    os.makedirs(OUT_DIR, exist_ok=True)
    all_ok = True

    for spec in BUILDS:
        out_pdf = os.path.join(OUT_DIR, spec["pdf"])
        print(f"\n[{spec['lang'].upper()}] {spec['pdf']}")
        render(chrome, spec["query"], out_pdf)
        stamp(out_pdf, spec)
        all_ok &= audit(out_pdf, spec)
        print(f"    size           : {os.path.getsize(out_pdf) / 1024:.0f} KB")

    print("\n" + ("BUILD OK" if all_ok else "BUILD FAILED — see the FAILs above"))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
