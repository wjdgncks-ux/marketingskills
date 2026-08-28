#!/usr/bin/env python3
"""Build a single-file HTML book from the markdown chapters in book/."""
import html
import os
import re

SRC = "/home/user/marketingskills/book"
OUT = "/tmp/claude-0/-home-user-marketingskills/4c2177e6-845c-5208-8f12-3c53b0af5beb/scratchpad/book.html"

# (filename, part label or None)
ORDER = [
    ("00-how-to-read.md",          "시작"),
    ("00-opening.md",              None),
    ("00-timeline.md",             None),
    ("part1.md",                   "1부 판 읽기"),
    ("part2-ch05-four-beats.md",   "2부 도구함"),
    ("part2-ch06-emotion.md",      None),
    ("part2-ch07-discipline.md",   None),
    ("part2-ch08-environment.md",  None),
    ("part2-ch09-play-language.md",None),
    ("part3-ch10-prep.md",         "3부 시기별 적용"),
    ("part3-ch11-0-3m.md",         None),
    ("part3-ch12-4-6m.md",         None),
    ("part3-ch13-7-12m.md",        None),
    ("part3-ch14-13-24m.md",       None),
    ("part3-ch15-24-36m.md",       None),
    ("part3-ch16-3-5y.md",         None),
    ("part4-ch17-feeding.md",      "4부 몸의 일"),
    ("part4-ch18-solids.md",       None),
    ("part4-ch19-sleep.md",        None),
    ("part4-ch20-fever.md",        None),
    ("part4-ch21-illness.md",      None),
    ("part4-ch22-emergency.md",    None),
    ("part4-ch23-skin-teeth.md",   None),
    ("part5.md",                   "5부 나를 지킨다"),
    ("part6.md",                   "6부 제도를 쓴다"),
    ("part7.md",                   "7부 확인한다"),
    ("appendix.md",                "부록"),
    ("index-ko.md",                None),
]

SLUG = {fn: "sec-" + re.sub(r"[^a-z0-9]+", "-", fn[:-3].lower()).strip("-") for fn, _ in ORDER}
SLUG["README.md"] = "top"

CHARS_PER_MIN = 500  # 한국어 읽기 속도 기준


def anchor_for(title):
    """장/부록 제목에서 안정적인 앵커 id를 만든다."""
    m = re.match(r"^(\d+)장", title)
    if m:
        return "ch-" + m.group(1)
    m = re.match(r"^부록\s+([A-Z])", title)
    if m:
        return "apx-" + m.group(1)
    if "닫는 글" in title:
        return "closing"
    if title.startswith("여는 글"):
        return "opening"
    if title.startswith("이 책을 읽는 법"):
        return "howto"
    if title.startswith("첫 5년 타임라인"):
        return "timeline"
    m = re.match(r"^(\d)부", title)
    if m:
        return "part-" + m.group(1)
    return None


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", t)

    def link(m):
        label, target = m.group(1), m.group(2)
        if target.endswith(".md"):
            return f'<a href="#{SLUG.get(target, "top")}">{label}</a>'
        if target.startswith(("http", "#")):
            return f'<a href="{target}" target="_blank" rel="noopener">{label}</a>'
        return label

    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, t)
    t = t.replace("[ ]", '<input type="checkbox" class="box">')
    t = t.replace("[강함]", '<span class="ev s">강함</span>')
    t = t.replace("[보통]", '<span class="ev m">보통</span>')
    t = t.replace("[관행]", '<span class="ev w">관행</span>')
    return t


def convert(md, toc=None):
    out, i, lines = [], 0, md.split("\n")
    while i < len(lines):
        ln = lines[i]

        if ln.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(html.escape(lines[i]))
                i += 1
            out.append('<div class="sheet"><pre>' + "\n".join(buf) + "</pre></div>")
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
            out.append(f"<blockquote>{convert(chr(10).join(buf))}</blockquote>")
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lv, title = len(m.group(1)), m.group(2)
            attr = ""
            if lv == 1 and toc is not None:
                a = anchor_for(title)
                if a:
                    attr = f' id="{a}"'
                    toc.append((a, title))
            out.append(f"<h{lv+1}{attr}>{inline(title)}</h{lv+1}>")
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
            items = "".join(
                ("<li><label>" + inline(b) + "</label></li>") if b.startswith("[ ]")
                else f"<li>{inline(b)}</li>"
                for b in buf)
            out.append(f"<ul{cls}>{items}</ul>")
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
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|\||>\s|```|---|\s*[-*]\s|\s*\d+\.\s)", lines[i]):
            buf.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")
    return "\n".join(out)


sections, nav = [], []
for fn, partname in ORDER:
    raw = open(os.path.join(SRC, fn), encoding="utf-8").read()
    toc = []
    body = convert(raw, toc)
    body = re.sub(r'(<h[234][^>]*>\s*💛.*?)(?=<hr>|$)', r'<div class="warm">\1</div>', body, flags=re.S)
    mins = max(1, round(len(re.sub(r"\s+", "", raw)) / CHARS_PER_MIN))
    sections.append(f'<section id="{SLUG[fn]}" data-min="{mins}">{body}</section>')
    if partname:
        nav.append(f'<div class="nav-part">{partname}</div>')
    for a, title in toc:
        nav.append(f'<a href="#{a}">{html.escape(title)}</a>')
    if not toc:
        nav.append(f'<a href="#{SLUG[fn]}">{html.escape(fn[:-3])}</a>')

CSS = """
:root{--paper:#F3F5F2;--card:#FBFCFA;--rule:#D6DCD6;--rule-soft:#E5EAE4;--ink:#182231;
--ink-2:#4A5462;--ink-3:#767E86;--navy:#1F3B6E;--navy-soft:#E3E9F3;--stamp:#A6392A;
--stamp-soft:#F6E5E1;--sage:#3F6B52;--sage-soft:#E2EDE5;--side:#EDF0EC;
--warm:#9A5B3C;--warm-bg:#F7EDE6;--warm-line:#E8D6C9}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#12161A;--card:#1A1F25;
--rule:#2C343C;--rule-soft:#232A31;--ink:#E7EBE8;--ink-2:#AFB8BF;--ink-3:#838C94;--navy:#9DB6E4;
--navy-soft:#1E2938;--stamp:#E39184;--stamp-soft:#2E1F1D;--sage:#8FBFA1;--sage-soft:#1B2620;
--side:#171C21;--warm:#D9A588;--warm-bg:#26201C;--warm-line:#3A2E27}}
:root[data-theme="dark"]{--paper:#12161A;--card:#1A1F25;--rule:#2C343C;--rule-soft:#232A31;
--ink:#E7EBE8;--ink-2:#AFB8BF;--ink-3:#838C94;--navy:#9DB6E4;--navy-soft:#1E2938;--stamp:#E39184;
--stamp-soft:#2E1F1D;--sage:#8FBFA1;--sage-soft:#1B2620;--side:#171C21;
--warm:#D9A588;--warm-bg:#26201C;--warm-line:#3A2E27}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);line-height:1.8;word-break:keep-all;
font-family:-apple-system,BlinkMacSystemFont,"Pretendard","Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",system-ui,sans-serif;
-webkit-font-smoothing:antialiased;font-size:16px}
.wrap{display:grid;grid-template-columns:17rem minmax(0,1fr)}
aside{position:sticky;top:0;height:100vh;overflow-y:auto;background:var(--side);
border-right:1px solid var(--rule);padding:1.1rem 0 4rem;display:flex;flex-direction:column}
.brand{padding:0 1.1rem .8rem;border-bottom:1px solid var(--rule);margin-bottom:.6rem}
.brand b{display:block;font-size:1.02rem;font-weight:800;letter-spacing:-.02em}
.brand span{display:block;font-size:.7rem;color:var(--ink-3);margin-top:.2rem;line-height:1.5}
.sbox{padding:0 1.1rem .6rem}
#q{width:100%;padding:.45rem .6rem;font:inherit;font-size:.84rem;background:var(--card);
color:var(--ink);border:1px solid var(--rule);border-radius:4px}
#q::placeholder{color:var(--ink-3)}
#q:focus{outline:2px solid var(--navy);outline-offset:1px}
.urgent{display:flex;gap:.3rem;padding:0 1.1rem .7rem;flex-wrap:wrap}
.urgent a{font-size:.72rem;padding:.2rem .5rem;border-radius:3px;background:var(--stamp-soft);
color:var(--stamp);text-decoration:none;font-weight:700;border:none}
.urgent a:hover{filter:brightness(.95)}
.navlist{overflow-y:auto;flex:1;min-height:0}
.nav-part{font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);
padding:.9rem 1.1rem .3rem;font-weight:700}
.navlist a{display:block;padding:.24rem 1.1rem;font-size:.81rem;color:var(--ink-2);
text-decoration:none;border-left:2px solid transparent;line-height:1.5}
.navlist a:hover{color:var(--ink);background:var(--card)}
.navlist a.on{color:var(--navy);border-left-color:var(--navy);font-weight:650;background:var(--card)}
.navlist a.hide{display:none}
.done{opacity:.55}
.done::after{content:" ✓";color:var(--sage);font-weight:700}
.foot{padding:.7rem 1.1rem 0;border-top:1px solid var(--rule);font-size:.7rem;color:var(--ink-3)}
.foot button{font:inherit;font-size:.7rem;color:var(--ink-2);background:var(--card);
border:1px solid var(--rule);border-radius:3px;padding:.2rem .45rem;cursor:pointer;margin-top:.4rem}
main{padding:2.6rem 2rem 8rem;max-width:56rem;margin:0 auto;min-width:0}
section{padding-bottom:2rem}
.rt{font-size:.72rem;color:var(--ink-3);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
margin:0 0 -1.5rem}
h2{font-size:clamp(1.7rem,4vw,2.3rem);line-height:1.2;letter-spacing:-.025em;font-weight:800;
margin:3.5rem 0 1rem;text-wrap:balance;padding-top:1rem;scroll-margin-top:1rem}
section:first-child h2{margin-top:0}
h3{font-size:1.3rem;font-weight:750;margin:2.5rem 0 .8rem;letter-spacing:-.01em;text-wrap:balance}
h4{font-size:1.02rem;font-weight:700;margin:1.9rem 0 .6rem}
h5{font-size:.9rem;font-weight:700;margin:1.4rem 0 .5rem;color:var(--ink-2)}
p{margin:.85rem 0;color:var(--ink-2)}
p strong,li strong,td strong{color:var(--ink);font-weight:680}
a{color:var(--navy);text-underline-offset:.2em}
ul,ol{margin:.85rem 0;padding-left:1.3rem;color:var(--ink-2)}
li{margin:.3rem 0}
ul.check{list-style:none;padding-left:.2rem}
ul.check li{margin:.15rem 0}
ul.check label{display:flex;gap:.6rem;align-items:flex-start;cursor:pointer;padding:.1rem 0}
ul.check label:hover{color:var(--ink)}
input.box{flex:none;width:1.05em;height:1.05em;margin:.4em 0 0;accent-color:var(--navy);cursor:pointer}
input.box:checked+*,label:has(input.box:checked){text-decoration:line-through;color:var(--ink-3)}
blockquote{margin:1.4rem 0;padding:.9rem 1.2rem;background:var(--card);border-left:3px solid var(--navy);
border-radius:0 3px 3px 0}
blockquote p{margin:.4rem 0}
blockquote h3,blockquote h4{margin:.3rem 0 .5rem}
.sheet{position:relative}
pre{background:var(--card);border:1px solid var(--rule);padding:1rem 1.15rem;overflow-x:auto;
font-size:.82rem;line-height:1.7;border-radius:3px;
font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:var(--ink-2);white-space:pre}
code{background:var(--navy-soft);color:var(--navy);padding:.08em .35em;border-radius:2px;font-size:.88em;
font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.scroll{overflow-x:auto;border:1px solid var(--rule);margin:1.3rem 0;background:var(--card);border-radius:3px}
table{border-collapse:collapse;width:100%;font-size:.88rem;min-width:22rem}
th,td{text-align:left;padding:.55rem .85rem;border-bottom:1px solid var(--rule-soft);vertical-align:top;color:var(--ink-2)}
thead th{font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);font-weight:650;
background:var(--paper);border-bottom:1px solid var(--rule)}
tbody tr:last-child td{border-bottom:none}
hr{border:none;border-top:1px solid var(--rule-soft);margin:2.5rem 0}
.ev{font-size:.68rem;padding:.05rem .4rem;border-radius:2px;font-weight:700;white-space:nowrap;vertical-align:.08em}
.ev.s{background:var(--sage-soft);color:var(--sage)}
.ev.m{background:var(--navy-soft);color:var(--navy)}
.ev.w{background:var(--rule-soft);color:var(--ink-3)}
.warm{background:linear-gradient(180deg,var(--warm-bg),transparent);border:1px solid var(--warm-line);
border-left:3px solid var(--warm);border-radius:0 4px 4px 0;padding:1.1rem 1.4rem 1.3rem;margin:2rem 0}
.warm h3,.warm h4{color:var(--warm);margin-top:.2rem;font-size:1.08rem}
.warm blockquote{background:var(--card);border-left-color:var(--warm)}
#top{border-bottom:2px solid var(--ink);padding-bottom:2rem;margin-bottom:1rem}
.cover .eyebrow{font-size:.7rem;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-3)}
.cover h1{font-size:clamp(2.2rem,7vw,3.6rem);line-height:1.12;letter-spacing:-.035em;font-weight:800;
margin:.7rem 0 .5rem;text-wrap:balance}
.cover .sub{font-size:1.05rem;color:var(--ink-2);margin:0 0 1.4rem}
.cover .meta{display:flex;flex-wrap:wrap;gap:.4rem .9rem;font-size:.78rem;color:var(--ink-3);
font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.menu{display:none;position:fixed;top:.7rem;left:.7rem;z-index:30;background:var(--card);
border:1px solid var(--rule);border-radius:4px;padding:.45rem .7rem;font-size:.85rem;color:var(--ink);cursor:pointer}
#res{position:absolute;left:0;right:0;top:100%;max-height:60vh;overflow-y:auto;background:var(--card);
border:1px solid var(--rule);border-radius:0 0 4px 4px;z-index:20;display:none}
#res a{display:block;padding:.4rem .7rem;font-size:.8rem;color:var(--ink-2);text-decoration:none;
border-bottom:1px solid var(--rule-soft);line-height:1.5}
#res a:hover,#res a:focus{background:var(--navy-soft);color:var(--navy)}
#res .cx{display:block;font-size:.72rem;color:var(--ink-3)}
#res .none{padding:.6rem .7rem;font-size:.8rem;color:var(--ink-3)}
mark{background:var(--sage-soft);color:var(--ink);padding:0 .1em}
@media(max-width:900px){
 .wrap{grid-template-columns:1fr}
 aside{position:fixed;left:0;top:0;width:16rem;z-index:20;transform:translateX(-100%);
 transition:transform .2s;box-shadow:0 0 40px rgba(0,0,0,.18)}
 aside.open{transform:none}
 .menu{display:block}
 main{padding:3.5rem 1.1rem 6rem}
}
@media print{
 aside,.menu,.rt{display:none}
 main{max-width:none;padding:0}
 h2{page-break-before:always}
 section:first-child h2,#top h1{page-break-before:auto}
 .scroll,pre,.warm,blockquote,table{page-break-inside:avoid}
 body.only-sheets main>*:not(#top){display:none}
 body.only-sheets .sheet{display:block!important}
}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = r"""
const side=document.querySelector('aside'),btn=document.querySelector('.menu');
btn.onclick=()=>side.classList.toggle('open');
const links=[...document.querySelectorAll('.navlist a')];
links.forEach(a=>a.addEventListener('click',()=>side.classList.remove('open')));

/* ---- 읽기 시간 ---- */
document.querySelectorAll('section[data-min]').forEach(s=>{
  const h=s.querySelector('h2');if(!h)return;
  const p=document.createElement('p');p.className='rt';
  p.textContent='읽는 데 약 '+s.dataset.min+'분';
  h.insertAdjacentElement('afterend',p);
});

/* ---- 체크박스 저장 ---- */
const KEY='dolawoljari.checks.v1';
let saved={};try{saved=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
document.querySelectorAll('input.box').forEach((b,i)=>{
  const sec=b.closest('section'); const k=(sec?sec.id:'x')+':'+i;
  b.dataset.k=k;
  if(saved[k])b.checked=true;
  b.addEventListener('change',()=>{
    saved[k]=b.checked;
    if(!b.checked)delete saved[k];
    try{localStorage.setItem(KEY,JSON.stringify(saved))}catch(e){}
  });
});

/* ---- 읽은 장 표시 + 마지막 위치 ---- */
const RK='dolawoljari.read.v1', PK='dolawoljari.pos.v1';
let read={};try{read=JSON.parse(localStorage.getItem(RK)||'{}')}catch(e){}
const mark=id=>{if(!id||read[id])return;read[id]=1;
  try{localStorage.setItem(RK,JSON.stringify(read))}catch(e){}
  links.forEach(l=>{if(l.getAttribute('href')==='#'+id)l.classList.add('done')})};
links.forEach(l=>{const id=l.getAttribute('href').slice(1);if(read[id])l.classList.add('done')});

const heads=[...document.querySelectorAll('h2[id]')];
const io=new IntersectionObserver(es=>{es.forEach(e=>{
  if(e.isIntersecting){
    const id=e.target.id;
    links.forEach(l=>l.classList.toggle('on',l.getAttribute('href')==='#'+id));
    const act=document.querySelector('.navlist a.on');
    if(act)act.scrollIntoView({block:'nearest'});
    try{localStorage.setItem(PK,id)}catch(e){}
    mark(id);
  }})},{rootMargin:'-8% 0px -80% 0px'});
heads.forEach(h=>io.observe(h));

/* 이어 읽기 */
(()=>{let last=null;try{last=localStorage.getItem(PK)}catch(e){}
 if(!last||location.hash)return;
 const el=document.getElementById(last);if(!el)return;
 const t=document.querySelector('.resume');if(!t)return;
 t.hidden=false;
 t.querySelector('b').textContent=el.textContent.trim().slice(0,24);
 t.querySelector('button').onclick=()=>{el.scrollIntoView();t.hidden=true};
})();

/* ---- 검색 ---- */
const q=document.getElementById('q'),res=document.getElementById('res');
let idx=null;
const build=()=>{
  if(idx)return idx;idx=[];
  document.querySelectorAll('main h2[id],main h3,main h4').forEach(h=>{
    let chap=h,cur=h;
    while(cur&&!(cur.tagName==='H2'&&cur.id)){cur=cur.previousElementSibling||cur.parentElement;
      if(cur&&cur.tagName==='SECTION')cur=cur.querySelector('h2[id]');}
    chap=cur||h;
    let txt='',n=h.nextElementSibling,c=0;
    while(n&&!/^H[234]$/.test(n.tagName)&&c<6){txt+=' '+n.textContent;n=n.nextElementSibling;c++}
    idx.push({t:h.textContent.trim(),b:txt.replace(/\s+/g,' ').slice(0,400),
      id:h.id||(chap&&chap.id)||'',ch:chap&&chap.id?chap.textContent.trim():'',el:h});
  });
  return idx;
};
let anchorSeq=0;
const run=()=>{
  const v=q.value.trim();
  if(v.length<1){res.style.display='none';links.forEach(a=>a.classList.remove('hide'));return}
  links.forEach(a=>a.classList.toggle('hide',!a.textContent.includes(v)));
  const hits=build().filter(e=>e.t.includes(v)||e.b.includes(v)).slice(0,25);
  res.innerHTML='';
  if(!hits.length){res.innerHTML='<div class="none">결과가 없습니다</div>';res.style.display='block';return}
  hits.forEach(e=>{
    if(!e.el.id)e.el.id='q'+(++anchorSeq);
    const a=document.createElement('a');a.href='#'+e.el.id;
    const pos=e.b.indexOf(v);
    const cx=pos>=0?e.b.slice(Math.max(0,pos-18),pos+42):'';
    a.innerHTML='<strong>'+e.t.replace(v,'<mark>'+v+'</mark>')+'</strong>'+
      (e.ch?'<span class="cx">'+e.ch+'</span>':'')+
      (cx?'<span class="cx">…'+cx.replace(v,'<mark>'+v+'</mark>')+'…</span>':'');
    a.onclick=()=>{res.style.display='none';side.classList.remove('open')};
    res.appendChild(a);
  });
  res.style.display='block';
};
q.addEventListener('input',run);
q.addEventListener('keydown',e=>{if(e.key==='Escape'){q.value='';run();q.blur()}});
document.addEventListener('click',e=>{if(!e.target.closest('.sbox'))res.style.display='none'});
document.addEventListener('keydown',e=>{
  if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();side.classList.add('open');q.focus()}});

/* ---- 인쇄 ---- */
document.querySelector('.pr-sheets').onclick=()=>{
  document.body.classList.add('only-sheets');print();
  setTimeout(()=>document.body.classList.remove('only-sheets'),300);
};
document.querySelector('.pr-all').onclick=()=>print();
"""

COVER = """<section id="top" class="cover">
<div class="eyebrow">근거 기반 영유아 발달·양육 실행 매뉴얼 · 0~5세</div>
<h1>돌아올 자리</h1>
<p class="sub">첫 5년, 무엇을 하고 무엇을 생각하고 무엇을 준비할 것인가</p>
<div class="meta"><span>40장 + 부록 A~M</span><span>전체 약 4시간 · 핵심 40분</span>
<span>AAP · CDC · WHO · 질병관리청 · 국민건강보험공단</span></div>
<p class="resume" hidden style="margin-top:1rem;font-size:.85rem">
마지막으로 읽던 곳: <b></b> <button style="font:inherit;cursor:pointer">이어 읽기</button></p>
</section>"""

doc = f"""<title>돌아올 자리 — 첫 5년 실행 매뉴얼</title>
<style>{CSS}</style>
<button class="menu">☰ 목차·검색</button>
<div class="wrap">
<aside>
<div class="brand"><b>돌아올 자리</b><span>첫 5년 실행 매뉴얼 · 0~5세</span></div>
<div class="sbox" style="position:relative">
  <input id="q" type="search" placeholder="증상·주제 검색 (예: 구토, 열)" aria-label="본문 검색">
  <div id="res"></div>
</div>
<div class="urgent">
  <a href="#ch-20">🌡 열</a><a href="#ch-21">🤒 흔한 병</a>
  <a href="#ch-22">🚑 응급처치</a><a href="#ch-37">🚩 경고 신호</a>
</div>
<nav class="navlist">
<a href="#top">표지</a>
{''.join(nav)}
</nav>
<div class="foot">진행 상황은 이 브라우저에 저장됩니다
<br><button class="pr-sheets">오려 쓰는 한 장만 인쇄</button>
<button class="pr-all">전체 인쇄</button></div>
</aside>
<main>
{COVER}
{''.join(sections)}
</main>
</div>
<script>{JS}</script>
"""

open(OUT, "w", encoding="utf-8").write(doc)
print(f"wrote {OUT} ({len(doc):,} chars, {len(sections)} sections, {len(nav)} nav rows)")
