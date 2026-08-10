#!/usr/bin/env python3
"""Build a single-file HTML book from the markdown chapters in book/."""
import html
import os
import re

SRC = "/home/user/marketingskills/book"
OUT = "/tmp/claude-0/-home-user-marketingskills/4c2177e6-845c-5208-8f12-3c53b0af5beb/scratchpad/book.html"

# (filename, sidebar label, part label or None)
ORDER = [
    ("00-opening.md",              "여는 글 — 약속",            "시작"),
    ("part1.md",                   "1~4장 · 판 읽기",           "1부 판 읽기"),
    ("part2-ch05-four-beats.md",   "5장 · 네 박자",             "2부 도구함"),
    ("part2-ch06-emotion.md",      "6장 · 감정 코칭",           None),
    ("part2-ch07-discipline.md",   "7장 · 훈육",                None),
    ("part2-ch08-environment.md",  "8장 · 환경 설계",           None),
    ("part2-ch09-play-language.md","9장 · 놀이와 말",           None),
    ("part3-ch10-prep.md",         "10장 · 임신 후기~출생",     "3부 시기별 적용"),
    ("part3-ch11-0-3m.md",         "11장 · 0~3개월",            None),
    ("part3-ch12-4-6m.md",         "12장 · 4~6개월",            None),
    ("part3-ch13-7-12m.md",        "13장 · 7~12개월",           None),
    ("part3-ch14-13-24m.md",       "14장 · 13~24개월",          None),
    ("part3-ch15-24-36m.md",       "15장 · 24~36개월",          None),
    ("part3-ch16-3-5y.md",         "16장 · 만 3~5세",           None),
    ("part4-ch17-feeding.md",      "17장 · 수유",               "4부 몸의 일"),
    ("part4-ch18-solids.md",       "18장 · 이유식·알레르기",    None),
    ("part4-ch19-sleep.md",        "19장 · 재우기",             None),
    ("part4-ch20-fever.md",        "20장 · 열",                 None),
    ("part4-ch21-illness.md",      "21장 · 흔한 병 12가지",     None),
    ("part4-ch22-emergency.md",    "22장 · 응급처치",           None),
    ("part4-ch23-skin-teeth.md",   "23장 · 피부·치아·약",       None),
    ("part5.md",                   "24~28장 · 나를 지킨다",     "5부 나를 지킨다"),
    ("part6.md",                   "29~36장 · 제도를 쓴다",     "6부 제도를 쓴다"),
    ("part7.md",                   "37~40장 · 확인한다",        "7부 확인한다"),
    ("appendix.md",                "부록 A~L",                  "부록"),
    ("index-ko.md",                "색인",                      None),
]

SLUG = {fn: "sec-" + re.sub(r"[^a-z0-9]+", "-", fn[:-3].lower()).strip("-") for fn, _, _ in ORDER}
SLUG["README.md"] = "top"


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)

    def link(m):
        label, target = m.group(1), m.group(2)
        if target.endswith(".md"):
            return f'<a href="#{SLUG.get(target, "top")}">{label}</a>'
        if target.startswith(("http", "#")):
            return f'<a href="{target}" target="_blank" rel="noopener">{label}</a>'
        return label

    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, t)
    t = t.replace("[ ]", '<span class="box"></span>').replace("[강함]", '<span class="ev s">강함</span>')
    t = t.replace("[보통]", '<span class="ev m">보통</span>').replace("[관행]", '<span class="ev w">관행</span>')
    return t


def convert(md):
    out, i, lines = [], 0, md.split("\n")
    while i < len(lines):
        ln = lines[i]

        if ln.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(html.escape(lines[i]))
                i += 1
            out.append("<pre>" + "\n".join(buf) + "</pre>")
            i += 1
            continue

        if re.match(r"^\|.*\|\s*$", ln) and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and re.match(r"^\|.*\|\s*$", lines[i]):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            tb = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f'<div class="scroll"><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>')
            continue

        if ln.startswith("> "):
            buf = []
            while i < len(lines) and (lines[i].startswith("> ") or lines[i].strip() == ">"):
                buf.append(lines[i][2:] if len(lines[i]) > 1 else "")
                i += 1
            inner = convert("\n".join(buf))
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lv = len(m.group(1))
            out.append(f"<h{lv+1}>{inline(m.group(2))}</h{lv+1}>")
            i += 1
            continue

        if re.match(r"^(---|\*\*\*)\s*$", ln):
            out.append("<hr>")
            i += 1
            continue

        if re.match(r"^\s*[-*]\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                buf.append(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            cls = ' class="check"' if any(b.startswith("[ ]") for b in buf) else ""
            out.append(f"<ul{cls}>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ul>")
            continue

        if re.match(r"^\s*\d+\.\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                buf.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ol>")
            continue

        if ln.strip() == "":
            i += 1
            continue

        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|\||>\s|```|---|\s*[-*]\s|\s*\d+\.\s)", lines[i]):
            buf.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")
    return "\n".join(out)


sections, nav, part = [], [], None
for fn, label, partname in ORDER:
    body = convert(open(os.path.join(SRC, fn), encoding="utf-8").read())
    sections.append(f'<section id="{SLUG[fn]}">{body}</section>')
    if partname:
        nav.append(f'<div class="nav-part">{partname}</div>')
    nav.append(f'<a href="#{SLUG[fn]}">{label}</a>')

CSS = """
:root{--paper:#F3F5F2;--card:#FBFCFA;--rule:#D6DCD6;--rule-soft:#E5EAE4;--ink:#182231;
--ink-2:#4A5462;--ink-3:#767E86;--navy:#1F3B6E;--navy-soft:#E3E9F3;--stamp:#A6392A;
--stamp-soft:#F6E5E1;--sage:#3F6B52;--sage-soft:#E2EDE5;--side:#EDF0EC}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#12161A;--card:#1A1F25;
--rule:#2C343C;--rule-soft:#232A31;--ink:#E7EBE8;--ink-2:#AFB8BF;--ink-3:#838C94;--navy:#9DB6E4;
--navy-soft:#1E2938;--stamp:#E39184;--stamp-soft:#2E1F1D;--sage:#8FBFA1;--sage-soft:#1B2620;--side:#171C21}}
:root[data-theme="dark"]{--paper:#12161A;--card:#1A1F25;--rule:#2C343C;--rule-soft:#232A31;
--ink:#E7EBE8;--ink-2:#AFB8BF;--ink-3:#838C94;--navy:#9DB6E4;--navy-soft:#1E2938;--stamp:#E39184;
--stamp-soft:#2E1F1D;--sage:#8FBFA1;--sage-soft:#1B2620;--side:#171C21}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);line-height:1.8;word-break:keep-all;
font-family:-apple-system,BlinkMacSystemFont,"Pretendard","Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",system-ui,sans-serif;
-webkit-font-smoothing:antialiased;font-size:16px}
.wrap{display:grid;grid-template-columns:16.5rem minmax(0,1fr)}
aside{position:sticky;top:0;height:100vh;overflow-y:auto;background:var(--side);
border-right:1px solid var(--rule);padding:1.5rem 0 4rem}
.brand{padding:0 1.25rem 1rem;border-bottom:1px solid var(--rule);margin-bottom:.9rem}
.brand b{display:block;font-size:1.05rem;font-weight:800;letter-spacing:-.02em}
.brand span{display:block;font-size:.72rem;color:var(--ink-3);margin-top:.25rem;line-height:1.5}
.nav-part{font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);
padding:1.1rem 1.25rem .35rem;font-weight:700}
aside a{display:block;padding:.32rem 1.25rem;font-size:.84rem;color:var(--ink-2);text-decoration:none;
border-left:2px solid transparent}
aside a:hover{color:var(--ink);background:var(--card)}
aside a.on{color:var(--navy);border-left-color:var(--navy);font-weight:650;background:var(--card)}
main{padding:3rem 2rem 8rem;max-width:56rem;margin:0 auto;min-width:0}
section{padding-bottom:2rem}
h2{font-size:clamp(1.7rem,4vw,2.3rem);line-height:1.2;letter-spacing:-.025em;font-weight:800;
margin:3.5rem 0 1rem;text-wrap:balance;padding-top:1rem}
section:first-child h2{margin-top:0}
h3{font-size:1.3rem;font-weight:750;margin:2.5rem 0 .8rem;letter-spacing:-.01em;text-wrap:balance;
color:var(--ink)}
h4{font-size:1.02rem;font-weight:700;margin:1.9rem 0 .6rem;color:var(--ink)}
h5{font-size:.9rem;font-weight:700;margin:1.4rem 0 .5rem;color:var(--ink-2)}
p{margin:.85rem 0;color:var(--ink-2)}
p strong,li strong,td strong{color:var(--ink);font-weight:680}
a{color:var(--navy);text-underline-offset:.2em}
ul,ol{margin:.85rem 0;padding-left:1.3rem;color:var(--ink-2)}
li{margin:.3rem 0}
ul.check{list-style:none;padding-left:.2rem}
ul.check li{display:flex;gap:.6rem;align-items:flex-start}
.box{flex:none;width:1em;height:1em;border:1.5px solid var(--ink-3);border-radius:2px;margin-top:.42em}
blockquote{margin:1.4rem 0;padding:.9rem 1.2rem;background:var(--card);border-left:3px solid var(--navy);
border-radius:0 3px 3px 0}
blockquote p{margin:.4rem 0}
blockquote h3,blockquote h4{margin:.3rem 0 .5rem}
pre{background:var(--card);border:1px solid var(--rule);padding:1rem 1.15rem;overflow-x:auto;
font-size:.82rem;line-height:1.7;border-radius:3px;
font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:var(--ink-2);white-space:pre}
code{background:var(--navy-soft);color:var(--navy);padding:.08em .35em;border-radius:2px;font-size:.88em;
font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.scroll{overflow-x:auto;border:1px solid var(--rule);margin:1.3rem 0;background:var(--card);border-radius:3px}
table{border-collapse:collapse;width:100%;font-size:.88rem;min-width:22rem}
th,td{text-align:left;padding:.55rem .85rem;border-bottom:1px solid var(--rule-soft);vertical-align:top;
color:var(--ink-2)}
thead th{font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);font-weight:650;
background:var(--paper);border-bottom:1px solid var(--rule)}
tbody tr:last-child td{border-bottom:none}
hr{border:none;border-top:1px solid var(--rule-soft);margin:2.5rem 0}
.ev{font-size:.68rem;padding:.05rem .4rem;border-radius:2px;font-weight:700;white-space:nowrap;
vertical-align:.08em}
.ev.s{background:var(--sage-soft);color:var(--sage)}
.ev.m{background:var(--navy-soft);color:var(--navy)}
.ev.w{background:var(--rule-soft);color:var(--ink-3)}
#top{border-bottom:2px solid var(--ink);padding-bottom:2rem;margin-bottom:1rem}
.cover .eyebrow{font-size:.7rem;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-3)}
.cover h1{font-size:clamp(2.2rem,7vw,3.6rem);line-height:1.12;letter-spacing:-.035em;font-weight:800;
margin:.7rem 0 .5rem;text-wrap:balance}
.cover .sub{font-size:1.05rem;color:var(--ink-2);margin:0 0 1.4rem}
.cover .meta{display:flex;flex-wrap:wrap;gap:.4rem .9rem;font-size:.78rem;color:var(--ink-3);
font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.menu{display:none;position:fixed;top:.7rem;left:.7rem;z-index:30;background:var(--card);
border:1px solid var(--rule);border-radius:4px;padding:.45rem .7rem;font-size:.85rem;color:var(--ink);
cursor:pointer}
@media(max-width:900px){
 .wrap{grid-template-columns:1fr}
 aside{position:fixed;left:0;top:0;width:15.5rem;z-index:20;transform:translateX(-100%);
 transition:transform .2s;box-shadow:0 0 40px rgba(0,0,0,.18)}
 aside.open{transform:none}
 .menu{display:block}
 main{padding:3.5rem 1.1rem 6rem}
}
@media print{aside,.menu{display:none}main{max-width:none;padding:0}
 section{page-break-after:always}}
"""

JS = """
const side=document.querySelector('aside'),btn=document.querySelector('.menu');
btn.onclick=()=>side.classList.toggle('open');
side.querySelectorAll('a').forEach(a=>a.onclick=()=>side.classList.remove('open'));
const links=[...side.querySelectorAll('a')];
const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){
 links.forEach(l=>l.classList.toggle('on',l.getAttribute('href')==='#'+e.target.id));}})},
 {rootMargin:'-10% 0px -80% 0px'});
document.querySelectorAll('section').forEach(s=>io.observe(s));
"""

COVER = """<section id="top" class="cover">
<div class="eyebrow">근거 기반 영유아 발달·양육 실행 매뉴얼 · 0~5세</div>
<h1>돌아올 자리</h1>
<p class="sub">첫 5년, 무엇을 하고 무엇을 생각하고 무엇을 준비할 것인가</p>
<div class="meta"><span>40장 + 부록 A~L</span><span>AAP · CDC · WHO · 질병관리청 · 국민건강보험공단</span></div>
</section>"""

doc = f"""<title>돌아올 자리 — 첫 5년 실행 매뉴얼</title>
<style>{CSS}</style>
<button class="menu">☰ 목차</button>
<div class="wrap">
<aside>
<div class="brand"><b>돌아올 자리</b><span>첫 5년 실행 매뉴얼 · 0~5세</span></div>
<a href="#top">표지</a>
{''.join(nav)}
</aside>
<main>
{COVER}
{''.join(sections)}
</main>
</div>
<script>{JS}</script>
"""

open(OUT, "w", encoding="utf-8").write(doc)
print(f"wrote {OUT}  ({len(doc):,} chars, {len(sections)} sections)")
