#!/usr/bin/env python3
"""별도 배포용 PDF 두 개를 만든다.

1) 응급대응-한장.pdf   — 22장의 ✂️⑥ 시트 + 부록 E 양식 (본문에서 추출, 중복 없음)
2) 한눈요약-케어행동학습.pdf — extra-summary.md
"""
import asyncio
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import build  # convert() 재사용

OUTDIR = Path("/tmp/claude-0/-home-user-marketingskills/4c2177e6-845c-5208-8f12-3c53b0af5beb/scratchpad")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

CSS = """
@page { size: A4; margin: 16mm 15mm; }
*{box-sizing:border-box}
body{margin:0;color:#141a20;background:#fff;
font-family:"NanumGothic","NanumBarunGothic",sans-serif;
font-size:10.5pt;line-height:1.62;word-break:keep-all;
orphans:2;widows:2}
h1{font-family:"NanumMyeongjo",serif;font-size:21pt;line-height:1.2;margin:0 0 4mm;
padding-bottom:2.5mm;border-bottom:1.5pt solid #141a20}
h1:not(:first-of-type){page-break-before:always}
h2{font-size:14pt;font-weight:700;margin:6mm 0 2mm;page-break-after:avoid;
border-left:3pt solid #1c3a68;padding-left:2.5mm}
h3{font-size:11.5pt;font-weight:700;margin:4mm 0 1.5mm;page-break-after:avoid}
p{margin:1.6mm 0;color:#3d4750}
strong{color:#141a20}
em{font-style:italic}
ul,ol{margin:1.5mm 0;padding-left:5.5mm;color:#3d4750}
li{margin:.7mm 0}
hr{border:none;border-top:.5pt solid #e2e7e3;margin:3.5mm 0}
blockquote{margin:2.5mm 0;padding:2.4mm 3.6mm;background:#f7f9f7;
border-left:2pt solid #1c3a68;page-break-inside:avoid}
blockquote p{margin:1mm 0}
table{border-collapse:collapse;width:100%;font-size:9pt;line-height:1.5;table-layout:fixed;margin:2mm 0}
th,td{text-align:left;padding:1.3mm 2mm;border-bottom:.4pt solid #e2e7e3;
vertical-align:top;color:#3d4750;word-break:keep-all;overflow-wrap:anywhere}
thead th{font-size:7.6pt;letter-spacing:.06em;color:#6d7780;background:#f7f9f7;
border-bottom:.8pt solid #c9d0cb}
tbody tr{page-break-inside:avoid}
.scroll{margin:0}
.sheet.form pre{font-size:10.8pt;line-height:1.5}
.sheet pre{background:#fff;border:1.2pt dashed #6d7780;padding:6mm 7mm;
font-family:"NanumGothicCoding",monospace;font-size:13pt;line-height:1.62;
white-space:pre;overflow:hidden;color:#2b333a;page-break-inside:avoid;margin:3mm 0}
pre .hw{display:inline-block;width:.5em;transform:scaleX(.5);transform-origin:left center}
pre .hw2{display:inline-block;width:.5em;transform:scaleX(.58);transform-origin:left center}
code{font-family:"NanumGothicCoding",monospace;font-size:.9em;background:#e6ecf5;color:#1c3a68;padding:0 .8mm}
.ev{font-size:7.4pt;padding:0 1mm;font-weight:700;white-space:nowrap;border-radius:1pt}
.ev.s{background:#e5efe8;color:#356048}
.ev.m{background:#e6ecf5;color:#1c3a68}
.ev.w{background:#e2e7e3;color:#6d7780}
input.box{display:none}
.foot{margin-top:5mm;padding-top:2mm;border-top:.5pt solid #e2e7e3;
font-size:8pt;color:#6d7780}
"""

FOOT = ('<p class="foot">『돌아올 자리 — 첫 5년 실행 매뉴얼』에서 발췌 · '
        '교육 목적의 정리본이며 진단·치료를 대체하지 않습니다 · '
        '아이 상태의 판단은 소아청소년과 전문의와 상의하세요</p>')


def halfwidth(html_text):
    """본편 인쇄판과 같은 방식으로 <pre> 안의 애매폭 문자를 보정한다."""
    import unicodedata

    def fix(m):
        inner, out, i = m.group(1), [], 0
        while i < len(inner):
            c = inner[i]
            if c == "<":
                j = inner.find(">", i)
                out.append(inner[i:j + 1]); i = j + 1; continue
            if c == "&":
                j = inner.find(";", i)
                if 0 < j - i < 10:
                    out.append(inner[i:j + 1]); i = j + 1; continue
            if unicodedata.east_asian_width(c) == "A":
                cls = "hw" if 0x2500 <= ord(c) <= 0x257F else "hw2"
                out.append(f'<span class="{cls}">{c}</span>')
            else:
                out.append(c)
            i += 1
        return "<pre>" + "".join(out) + "</pre>"

    return re.sub(r"<pre>(.*?)</pre>", fix, html_text, flags=re.S)


def sheet_from(fn, marker, cls="sheet"):
    """md 파일에서 marker가 붙은 절의 첫 ``` 블록을 뽑아온다."""
    src = (HERE / fn).read_text(encoding="utf-8")
    i = src.index(marker)
    block = re.search(r"```(.*?)```", src[i:], re.S).group(1).strip("\n")
    # 전체를 감싼 ┌─┐ 프레임은 CSS 점선과 겹치므로 걷어낸다
    lines = []
    for l in block.split("\n"):
        if re.match(r"^\s*[┌└]─+[┐┘]\s*$", l):
            continue
        l = re.sub(r"^(\s*)│", r"\1", l)
        l = re.sub(r"│\s*$", "", l)
        lines.append(l.rstrip())
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    import html as H
    return f'<div class="{cls}"><pre>' + H.escape("\n".join(lines)) + "</pre></div>"


def page(title, body_html, out_name):
    html_doc = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8">'
                f'<title>{title}</title><style>{CSS}</style></head>'
                f'<body>{halfwidth(body_html)}{FOOT}</body></html>')
    tmp = OUTDIR / (out_name + ".html")
    tmp.write_text(html_doc, encoding="utf-8")
    return tmp, OUTDIR / (out_name + ".pdf")


async def render(jobs):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME)
        pg = await b.new_page()
        for tmp, out in jobs:
            await pg.goto(tmp.as_uri(), wait_until="load")
            await pg.emulate_media(media="print")
            await pg.pdf(path=str(out), format="A4", print_background=True,
                         margin={"top": "16mm", "bottom": "16mm",
                                 "left": "15mm", "right": "15mm"})
            print(f"wrote {out} ({out.stat().st_size/1024:.0f} KB)")
        await b.close()


# ---- 1. 응급 한 장 ----
emg = (
    "<h1>응급 대응 — 한 장</h1>"
    "<p><strong>인쇄해서 냉장고·아이 방문에 붙이세요.</strong> "
    "1쪽은 응급 대응 요약, 2쪽은 우리 아이 정보를 적어 넣는 양식입니다. "
    "이 종이는 실습 교육(영유아 심폐소생술)을 전제로 한 기억용입니다.</p>"
    + sheet_from("part4-ch22-emergency.md", "오려 쓰는 한 장 ⑥")
    + "<h1>우리 아이 응급 양식 — 채워서 붙이세요</h1>"
    + sheet_from("appendix.md", "부록 E", cls="sheet form")
)

# ---- 2. 한눈 요약 ----
summary_md = (HERE / "extra-summary.md").read_text(encoding="utf-8")
summary = build.convert(summary_md)

jobs = [
    page("응급 대응 — 한 장", emg, "응급대응-한장"),
    page("한눈 요약 — 케어·행동·학습", summary, "한눈요약-케어행동학습"),
]
asyncio.run(render(jobs))
