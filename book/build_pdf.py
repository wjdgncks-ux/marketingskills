#!/usr/bin/env python3
"""웹 책(book.html)에서 인쇄용 PDF를 만든다."""
import asyncio
import html as H
import re
import unicodedata
from pathlib import Path

BASE = Path("/tmp/claude-0/-home-user-marketingskills/4c2177e6-845c-5208-8f12-3c53b0af5beb/scratchpad")
SRC = BASE / "book.html"
TMP = BASE / "book-print.html"
OUT = BASE / "돌아올자리-첫5년실행매뉴얼.pdf"

src = SRC.read_text(encoding="utf-8")
main = re.search(r"<main>(.*)</main>", src, re.S).group(1)

# 표지 섹션은 인쇄용으로 다시 만든다
main = re.sub(r'<section id="top" class="cover">.*?</section>', "", main, flags=re.S)
# 웹 전용 요소 제거
main = re.sub(r'<p class="resume".*?</p>', "", main, flags=re.S)
# "돌아가기: 목차 · 색인" 같은 웹 내비게이션 줄 제거
main = re.sub(r'<hr>\s*<p><strong>돌아가기</strong>.*?</p>', "", main, flags=re.S)
# 체크박스는 인쇄용 네모로
main = main.replace('<input type="checkbox" class="box">', '<span class="box">☐</span>')

# 제목 바로 앞의 구분선은 이중 신호다 — 제목이 이미 단락을 나눈다
main = re.sub(r"(?:\s*<hr>)+(\s*<h[345])", r"\1", main)
# 장 끝에 겹친 구분선은 빈 페이지를 만든다 — h2/섹션 앞의 <hr>은 지운다
main = re.sub(r"(?:\s*<hr>)+(\s*(?:</section>|<section|<h2))", r"\1", main)
main = re.sub(r"(?:<hr>\s*){2,}", "<hr>\n", main)
# "→ 다음: …" 한 줄이 홀로 다음 쪽으로 넘어가지 않게 앞 내용에 붙인다
main = re.sub(r"<p>(→ 다음:.*?)</p>", r'<p class="nx">\1</p>', main)

TOP = re.compile(r"^\s*┌─+┐\s*$")
BOT = re.compile(r"^\s*└─+┘\s*$")


def _unframe(m):
    """전체를 감싼 ┌─┐ 프레임은 CSS 테두리로 대체하고 지운다."""
    lines = m.group(1).split("\n")
    body = [l for l in lines if l.strip()]
    if not (body and TOP.match(body[0]) and BOT.match(body[-1])):
        return m.group(0)
    out = []
    for l in lines:
        if TOP.match(l) or BOT.match(l):
            continue
        l = re.sub(r"^(\s*)│", r"\1", l)
        l = re.sub(r"│\s*$", "", l)
        out.append(l.rstrip())
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return "<pre>" + "\n".join(out) + "</pre>"


# 「📌 요약 3줄」은 제목과 목록이 쪽 경계로 갈라지지 않게 한 덩어리로 묶는다
main = re.sub(r"(<p><strong>📌[^<]*</strong></p>\s*<ol>.*?</ol>)",
              r'<div class="sum">\1</div>', main, flags=re.S)

main = re.sub(r"<pre>(.*?)</pre>", _unframe, main, flags=re.S)


# --- 아스키 도표(냉장고 시트) 정렬 보정 ---
# 원고는 박스 문자·기호를 반각(1칸)으로 계산해 그렸지만, 폰트는 이들을 전각(2칸)으로
# 렌더링해 프레임이 어긋난다. 해당 문자만 가로 50%로 눌러 원고의 칸 수와 맞춘다.

def _halfwidth(m):
    inner, out, i = m.group(1), [], 0
    while i < len(inner):
        c = inner[i]
        if c == "<":                      # 태그는 그대로 통과
            j = inner.find(">", i)
            out.append(inner[i:j + 1]); i = j + 1; continue
        if c == "&":                      # 엔티티는 그대로 통과
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


main = re.sub(r"<pre>(.*?)</pre>", _halfwidth, main, flags=re.S)

# 목차 생성
toc_rows = []
for m in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>', main, re.S):
    title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
    kind = "ch" if m.group(1).startswith("ch-") else ("apx" if m.group(1).startswith("apx-") else "front")
    toc_rows.append(f'<li class="{kind}"><a href="#{m.group(1)}">{H.escape(title)}</a></li>')
TOC = "<ol class='toc'>" + "".join(toc_rows) + "</ol>"

CSS = """
@page { size: A4; margin: 20mm 17mm 18mm; }
*{box-sizing:border-box}
html{--ink:#141a20;--ink-2:#3d4750;--ink-3:#6d7780;--rule:#c9d0cb;--rule-soft:#e2e7e3;
--card:#f7f9f7;--navy:#1c3a68;--navy-soft:#e6ecf5;--stamp:#9c2f22;--stamp-soft:#fbeae6;
--sage:#356048;--sage-soft:#e5efe8;--warm:#8a4f30;--warm-bg:#fbf2ec;--warm-line:#e8d6c9}
body{margin:0;color:var(--ink);background:#fff;
font-family:"NanumGothic","NanumBarunGothic",sans-serif;
font-size:10pt;line-height:1.6;word-break:keep-all;text-align:left;
orphans:2;widows:2}
.serif{font-family:"NanumMyeongjo",serif}

/* ---- 표지 ---- */
.cover{height:247mm;display:flex;flex-direction:column;justify-content:center;
page-break-after:always;text-align:left;border-left:3pt solid var(--ink);padding-left:12mm}
.cover .eyebrow{font-size:8.5pt;letter-spacing:.18em;color:var(--ink-3);margin-bottom:10mm}
.cover h1{font-family:"NanumMyeongjo",serif;font-size:44pt;line-height:1.1;margin:0 0 6mm;
letter-spacing:-.02em;font-weight:700}
.cover .sub{font-size:13pt;color:var(--ink-2);margin:0 0 18mm;line-height:1.5}
.cover .meta{font-size:9pt;color:var(--ink-3);line-height:1.9;border-top:.5pt solid var(--rule);padding-top:5mm}
.cover .note{margin-top:14mm;font-size:8.5pt;color:var(--ink-3);line-height:1.7;
border-left:2pt solid var(--rule);padding-left:4mm}

/* ---- 목차 ---- */
.tocpage{page-break-after:always}
.tocpage h2{font-family:"NanumMyeongjo",serif;font-size:20pt;margin:0 0 8mm;
border-bottom:1.5pt solid var(--ink);padding-bottom:3mm}
ol.toc{list-style:none;padding:0;margin:0;column-count:2;column-gap:9mm}
ol.toc li{font-size:8.6pt;padding:.72mm 0;break-inside:avoid;color:var(--ink-2)}
ol.toc li a{color:var(--ink-2);text-decoration:none}
ol.toc li.front{font-weight:700;color:var(--ink)}
ol.toc li.apx{color:var(--ink-3)}

/* ---- 본문 ---- */
h2{font-family:"NanumMyeongjo",serif;font-size:19pt;line-height:1.25;font-weight:700;
margin:0 0 4mm;padding-bottom:2.5mm;border-bottom:1.5pt solid var(--ink);
page-break-after:avoid;letter-spacing:-.01em}
h2[id]{page-break-before:always}
h3{font-size:12.5pt;font-weight:700;margin:5.5mm 0 1.5mm;page-break-after:avoid;
color:var(--ink);border-left:2.5pt solid var(--navy);padding-left:2.5mm}
h4{font-size:10.5pt;font-weight:700;margin:3.6mm 0 1.2mm;page-break-after:avoid}
h5{font-size:9.5pt;font-weight:700;margin:2.8mm 0 .8mm;color:var(--ink-2);page-break-after:avoid}
p{margin:1.5mm 0;color:var(--ink-2)}
p strong,li strong,td strong{color:var(--ink);font-weight:700}
a{color:var(--ink);text-decoration:none}
ul,ol{margin:1.5mm 0;padding-left:5.5mm;color:var(--ink-2)}
li{margin:.55mm 0}
ul.check{list-style:none;padding-left:1mm}
ul.check label{display:block}
.box{color:var(--ink-3);margin-right:1.5mm}
hr{border:none;border-top:.5pt solid var(--rule-soft);margin:3.4mm 0}

blockquote{margin:2.4mm 0;padding:2.2mm 3.5mm;background:var(--card);
border-left:2pt solid var(--navy);page-break-inside:avoid}
blockquote p{margin:1mm 0}
pre{background:var(--card);border:.5pt solid var(--rule);padding:2.2mm 2.8mm;
font-family:"NanumGothicCoding",monospace;font-size:7.9pt;line-height:1.34;
white-space:pre;overflow:hidden;color:var(--ink-2);page-break-inside:avoid;margin:2.4mm 0}
pre .hw{display:inline-block;width:.5em;transform:scaleX(.5);transform-origin:left center}
pre .hw2{display:inline-block;width:.5em;overflow:visible;text-indent:-.25em}
code{font-family:"NanumGothicCoding",monospace;font-size:.9em;
background:var(--navy-soft);color:var(--navy);padding:0 .8mm;border-radius:1pt}

.scroll{border:.5pt solid var(--rule);margin:2.4mm 0;page-break-inside:auto}
table{border-collapse:collapse;width:100%;font-size:8.4pt;line-height:1.45;table-layout:fixed}
th,td{text-align:left;padding:1.15mm 1.9mm;border-bottom:.4pt solid var(--rule-soft);
vertical-align:top;color:var(--ink-2);word-break:keep-all;overflow-wrap:anywhere}
thead th{font-size:7.4pt;letter-spacing:.06em;color:var(--ink-3);font-weight:700;
background:var(--card);border-bottom:.8pt solid var(--rule)}
tbody tr{page-break-inside:avoid}
tbody tr:last-child td{border-bottom:none}

.ev{font-size:7pt;padding:0 .8mm;border-radius:1pt;font-weight:700;white-space:nowrap}
.ev.s{background:var(--sage-soft);color:var(--sage)}
.ev.m{background:var(--navy-soft);color:var(--navy)}
.ev.w{background:var(--rule-soft);color:var(--ink-3)}

.warm{background:var(--warm-bg);border:.5pt solid var(--warm-line);
border-left:2.5pt solid var(--warm);padding:2.5mm 3.5mm;margin:3.6mm 0;page-break-inside:avoid}
.warm h3,.warm h4{color:var(--warm);border:none;padding-left:0;margin-top:.8mm;font-size:11pt}
.warm blockquote{background:#fff;border-left-color:var(--warm)}
.sum{page-break-inside:avoid;margin-top:3mm}
.nx{page-break-before:avoid;margin-top:4mm;font-size:9pt;color:var(--ink-3)}
.rt{display:none}
section{page-break-before:auto}
"""

COVER = """
<div class="cover">
  <div class="eyebrow">근거 기반 영유아 발달·양육 실행 매뉴얼 · 0~5세</div>
  <h1>돌아올 자리</h1>
  <p class="sub">첫 5년, 무엇을 하고<br>무엇을 생각하고 무엇을 준비할 것인가</p>
  <div class="meta">
    40장 + 부록 A~M<br>
    AAP · CDC · WHO · 하버드 아동발달센터<br>
    질병관리청 · 국민건강보험공단(K-DST)
  </div>
  <div class="note">
    이 책은 교육 목적의 정리본이며 진단·치료를 대체하지 않습니다.<br>
    아이 상태에 대한 판단은 반드시 소아청소년과 전문의와 상의하세요.<br>
    예방접종 일정·검진 차수·정부 지원금은 정책 변경이 잦으므로
    40장의 공식 확인처에서 최신본을 확인하세요.
  </div>
</div>
"""

TOCPAGE = f'<div class="tocpage"><h2 class="serif">목차</h2>{TOC}</div>'

TMP.write_text(
    f'<!doctype html><html lang="ko" data-theme="light"><head><meta charset="utf-8">'
    f'<title>돌아올 자리 — 첫 5년 실행 매뉴얼</title><style>{CSS}</style></head>'
    f'<body>{COVER}{TOCPAGE}{main}</body></html>',
    encoding="utf-8")


async def main_():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
        pg = await b.new_page()
        await pg.goto(TMP.as_uri(), wait_until="load")
        await pg.emulate_media(media="print")
        await pg.pdf(
            path=str(OUT), format="A4", print_background=True,
            margin={"top": "20mm", "bottom": "18mm", "left": "17mm", "right": "17mm"},
            display_header_footer=True,
            header_template='<div style="font-size:1pt"></div>',
            footer_template=(
                '<div style="font-size:7.5pt;color:#8a9490;width:100%;padding:0 17mm;'
                'font-family:sans-serif;display:flex;justify-content:space-between">'
                '<span>돌아올 자리 · 첫 5년 실행 매뉴얼</span>'
                '<span class="pageNumber"></span></div>'),
        )
        await b.close()

asyncio.run(main_())
size = OUT.stat().st_size
print(f"wrote {OUT} ({size/1024/1024:.2f} MB)")
