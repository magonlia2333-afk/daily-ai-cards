import base64, datetime as dt, json, os, re, textwrap, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path
import requests
from openai import OpenAI
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TODAY = dt.datetime.now(dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=8)))
SLOT = os.getenv("RUN_SLOT", "morning")
CONTENT_TYPE = "news" if SLOT == "morning" else "skills"
OUT = ROOT / "generated" / TODAY.strftime("%Y-%m-%d") / SLOT
OUT.mkdir(parents=True, exist_ok=True)
GH_HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "ai-card-workflow"}
if os.getenv("GH_TOKEN"):
    GH_HEADERS["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"

def get_json(url):
    r = requests.get(url, headers=GH_HEADERS, timeout=30); r.raise_for_status(); return r.json()

def collect_evidence():
    config = json.loads((ROOT / "config/sources.json").read_text(encoding="utf-8"))
    evidence = []
    seen = set()
    recent = (TODAY - dt.timedelta(days=30)).date().isoformat()
    for query in config["github_queries"] if CONTENT_TYPE == "skills" else []:
        query = query.replace("{recent}", recent)
        data = get_json("https://api.github.com/search/repositories?" + urllib.parse.urlencode({"q": query, "sort": "updated", "order": "desc", "per_page": 20}))
        for x in data.get("items", []):
            if x["full_name"] in seen: continue
            seen.add(x["full_name"])
            evidence.append({"kind":"github", "name":x["full_name"], "description":x.get("description") or "", "url":x["html_url"], "stars":x.get("stargazers_count",0), "forks":x.get("forks_count",0), "language":x.get("language") or "", "license":(x.get("license") or {}).get("spdx_id") or "unknown", "updated_at":x.get("pushed_at") or x.get("updated_at")})
    for feed in config.get("official_news_feeds", []) if CONTENT_TYPE == "news" else []:
        try:
            root = ET.fromstring(requests.get(feed, timeout=20).content)
            for item in root.findall(".//item")[:10]:
                title = item.findtext("title") or ""; link = item.findtext("link") or ""; pub = item.findtext("pubDate") or item.findtext("published") or ""
                if title and link: evidence.append({"kind":"official_news", "name":title, "description":"", "url":link, "published_at":pub})
        except Exception as e: print(f"feed skipped: {feed}: {e}")
    return evidence

def ask_model(evidence):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=os.getenv("OPENAI_BASE_URL") or None)
    if CONTENT_TYPE == "news":
        brief = "这是新闻线：只选一条较新的、可核验的 AI 新闻，优先国产模型、国产工作台或重要产品更新。输出1个 item，内容要适合一张长图：发生了什么、为什么重要、对普通用户有什么用、下一步怎么跟进。不要写成新闻联播，也不要堆太多背景。"
        count = "只能输出1个 item"
    else:
        brief = "这是技能线：只选 GitHub 上真正可用的 AI skill、工作流、工具或 Codex/AI coding 技巧。输出3到6个 item，每个 item 必须是一项可以照着做的技巧，写清楚步骤、适用场景、限制和预期结果，不要只介绍项目。"
        count = "输出3到6个 item"
    prompt = f"""你是严谨的中文科技自媒体编辑。{brief} 只能使用 EVIDENCE 中出现的事实，禁止补写未提供的 Star、日期、功能、性能或融资数字。国产项目必须以官方来源或项目原始仓库为准。每个项目必须有可核验 source_url，source_type 只能是 github 或 official_news。{count}。输出严格 JSON：{{\"theme\":\"...\",\"items\":[{{\"title\":\"...\",\"repo\":\"...\",\"why\":\"...\",\"how\":\"...\",\"audience\":\"...\",\"facts\":[\"...\"],\"source_url\":\"...\",\"source_type\":\"github|official_news\",\"updated_at\":\"...\"}}],\"post_title\":\"...\",\"post_body\":\"...\",\"hashtags\":[\"...\"]}}。EVIDENCE=""" + json.dumps(evidence, ensure_ascii=False)
    res = client.chat.completions.create(model=os.getenv("OPENAI_MODEL","gpt-5.6-terra"), temperature=0.2, response_format={"type":"json_object"}, messages=[{"role":"system","content":"你输出可审计、克制、准确的编辑结果。"},{"role":"user","content":prompt}])
    return json.loads(res.choices[0].message.content)

def esc(s): return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"','&quot;')
def wrap(s, width=29): return textwrap.wrap(s, width=width, break_long_words=False, break_on_hyphens=False)
def card_svg(item, index, total):
    lines=[]
    y=115
    def add(text, size=28, color="#25262a", weight="400", gap=43):
        nonlocal y
        for line in wrap(text, 31 if size>=27 else 38):
            lines.append(f'<text x="100" y="{y}" font-family="Microsoft YaHei, Arial, sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{esc(line)}</text>'); y+=gap
    add(f"{index:02d}  {item.get('title','未命名项目')}", 42 if CONTENT_TYPE == "skills" else 48, "#191a1d", "800", 62)
    add("发生了什么" if CONTENT_TYPE == "news" else "解决什么问题", 24, "#b08325", "700", 38); add(item.get("why",""), 28, gap=43)
    y+=12; add("为什么值得关注" if CONTENT_TYPE == "news" else "怎么提升效率", 24, "#b08325", "700", 38); add(item.get("how",""), 28, gap=43)
    y+=12; add("对谁有用" if CONTENT_TYPE == "news" else "适合谁", 24, "#b08325", "700", 38); add(item.get("audience",""), 28, gap=43)
    y+=18; add("可核验事实", 24, "#b08325", "700", 38)
    for fact in item.get("facts",[])[:3]: add("· "+fact, 25, "#34363b", gap=38)
    source_type = "GitHub" if item.get("source_type")=="github" else "官方新闻"
    source = item.get("source_url","")
    height = 2100 if CONTENT_TYPE == "news" else 1600
    footer_y = height - 150
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}"><rect width="1200" height="{height}" fill="#f6f2ea"/><rect x="34" y="34" width="1132" height="{height-68}" rx="8" fill="none" stroke="#1e2024" stroke-width="2"/><text x="80" y="90" font-family="Arial, Microsoft YaHei" font-size="24" fill="#51565b" letter-spacing="2">AI {('新闻长图' if CONTENT_TYPE == 'news' else '技能卡片')} · {TODAY.strftime('%Y.%m.%d')} · {SLOT.upper()}</text><line x1="80" y1="120" x2="1120" y2="120" stroke="#1e2024" stroke-width="2"/>{''.join(lines)}<line x1="80" y1="{footer_y}" x2="1120" y2="{footer_y}" stroke="#1e2024" stroke-width="2"/><text x="80" y="{footer_y+50}" font-family="Arial, Microsoft YaHei" font-size="21" fill="#555b60">来源：{source_type} · 更新时间：{esc(item.get('updated_at','未提供'))}</text><text x="80" y="{footer_y+88}" font-family="Arial, Microsoft YaHei" font-size="16" fill="#777b7d">{esc(source[:105])}</text><text x="1120" y="{footer_y+50}" text-anchor="end" font-family="Arial, Microsoft YaHei" font-size="20" fill="#b08325">{index}/{total}</text></svg>'''
    return svg

def render(items):
    import cairosvg
    for i,item in enumerate(items,1):
        svg=card_svg(item,i,len(items)); (OUT/f"card-{i}.svg").write_text(svg,encoding="utf-8")
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(OUT/f"card-{i}.png"), output_width=1200, output_height=(2100 if CONTENT_TYPE == "news" else 1600))

def send_email(result):
    headers={"Authorization":"Bearer "+os.environ["RESEND_API_KEY"],"Content-Type":"application/json"}
    items=result.get("items",[])
    for index,item in enumerate(items,1):
        image=OUT/f"card-{index}.png"
        body=f"<h2>{esc(item.get('title','AI 实用发现'))}</h2><p><b>解决什么问题：</b>{esc(item.get('why',''))}</p><p><b>怎么提升效率：</b>{esc(item.get('how',''))}</p><p><b>适合谁：</b>{esc(item.get('audience',''))}</p><p><b>事实：</b>{'<br>'.join(esc(x) for x in item.get('facts',[]))}</p><p>来源：<a href=\"{esc(item.get('source_url',''))}\">{esc(item.get('source_url',''))}</a></p>"
        payload={"from":os.environ["MAIL_FROM"],"to":[os.environ["MAIL_TO"]],"subject":f"{index}/{len(items)} · {item.get('title','AI 实用发现')}","html":body,"attachments":[{"filename":image.name,"content":base64.b64encode(image.read_bytes()).decode()}]}
        r=requests.post("https://api.resend.com/emails",headers=headers,json=payload,timeout=60); r.raise_for_status()

if __name__ == "__main__":
    evidence=collect_evidence(); (OUT/"evidence.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
    result=ask_model(evidence); items=result.get("items",[])
    expected = (len(items) == 1) if CONTENT_TYPE == "news" else (3 <= len(items) <= 6)
    if not expected: raise RuntimeError(f"{CONTENT_TYPE} 输出数量不符合约束：{len(items)}")
    for item in items:
        if not item.get("source_url") or not item.get("facts"): raise RuntimeError("存在缺少来源或事实的卡片")
    (OUT/"post.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8"); render(items); send_email(result)
    print(f"generated {len(items)} cards in {OUT}")
