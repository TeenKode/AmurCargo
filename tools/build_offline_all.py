"""Build a single file with all user-facing AmurCargo pages, no external assets.

Run after rebuild_site.py creates the simulator and guides. The result can be
opened with file:// without a web server, including on an offline computer.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "OFFLINE.html"
START_TEMPLATE = ROOT / "tools/start_page_template.html"
START_OUTPUT = ROOT / "START.html"
STYLE_GUIDE = """body{font:16px/1.6 "Segoe UI",Arial,sans-serif;background:#eef3f7;color:#20374a;margin:0}
main{max-width:850px;background:#fff;margin:24px auto;padding:28px 36px;border-radius:14px}
h1{font-size:27px;margin:0 0 20px}h2{font-size:18px;margin:22px 0 7px}p{margin:8px 0}
@media(max-width:600px){main{margin:0;padding:18px;border-radius:0}}"""
SOURCES = [
    ("sim", "3D-симулятор", "simulator/Open_Simulation_3D.html"),
    ("assembly", "Сборка и подключение", "simulator/Assembly_Guide_RU.html"),
    ("purchase", "Список покупок", "simulator/Purchase_List_RU.html"),
]
GUIDES = [
    ("quick", "Как начать", "tools/quick_guide_body.html"),
    ("calibration", "Калибровка", "tools/calibration_guide_body.html"),
]


def wrap_guide(title, body):
    return ('<!doctype html><html lang="ru"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + title + '</title><style>' + STYLE_GUIDE +
            '</style></head><body><main>' + body + '</main></body></html>')


def build():
    version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
    if not re.fullmatch(r"(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)", version):
        raise ValueError("Invalid project version in package.json")
    start_template = START_TEMPLATE.read_text(encoding="utf-8")
    if "__PROJECT_VERSION__" not in start_template:
        raise ValueError("START template has no version placeholder")
    START_OUTPUT.write_text(start_template.replace("__PROJECT_VERSION__", version), encoding="utf-8")
    pages = {}
    for name, title, file in SOURCES:
        pages[name] = {"title": title, "filename": Path(file).name,
                       "html": (ROOT / file).read_text(encoding="utf-8")}
    for name, title, file in GUIDES:
        pages[name] = {"title": title, "filename": name + ".html",
                       "html": wrap_guide(title, (ROOT / file).read_text(encoding="utf-8"))}
    for name, page in pages.items():
        source = page["html"]
        if not re.search(r"<!doctype html>", source, re.I):
            raise ValueError("Page has no doctype: " + name)
        if re.search(r'<script\b[^>]*\bsrc\s*=', source, re.I):
            raise ValueError("External script: " + name)
        if re.search(r'<link\b[^>]*\bhref\s*=', source, re.I):
            raise ValueError("External stylesheet/resource: " + name)
        # Existing external links to datasheets are references, not dependencies.
    # Escaping every '<' prevents child </script> tags from ending this JSON block.
    payload = json.dumps(pages, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    shell = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AmurCargo — полный автономный комплект</title>
<style>
:root{color-scheme:light;--navy:#17364c;--blue:#245ad5;--border:#d7e2eb}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;font:15px/1.45 "Segoe UI",Arial,sans-serif;color:var(--navy);background:#edf3f8}
.appbar{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:10px 18px;background:#fff;border-bottom:1px solid var(--border)}
.brand{font-weight:750;font-size:17px;letter-spacing:.2px}.sub{font-size:11px;color:#678195}.version-badge{border:1px solid #cbd9e5;border-radius:999px;background:#f1f6fb;color:#315a76;padding:4px 10px;font-size:11px;font-weight:700;white-space:nowrap}
nav{display:flex;gap:5px;overflow-x:auto;flex:1;white-space:nowrap;scrollbar-width:thin}
nav button,.toolbar button{font:inherit;cursor:pointer;border:1px solid transparent;border-radius:9px;padding:9px 12px;background:transparent;color:#395a73;white-space:nowrap}
nav button[aria-current=page]{color:#fff;background:var(--blue)}
nav button:hover:not([aria-current=page]),.toolbar button:hover{background:#eaf2fb}
.toolbar{display:flex;align-items:center;gap:6px;background:white;border-bottom:1px solid var(--border);padding:5px 18px;min-height:40px}
#sectionLabel{font-size:12px;color:#607b90;font-weight:600;flex:1}
.toolbar button{border-color:var(--border);font-size:12px;padding:6px 10px}
.toolbar button:disabled{opacity:.45;cursor:default}
.workspace{width:100%;min-height:calc(100dvh - 112px);position:relative}
.workspace iframe{display:block;width:100%;height:calc(100dvh - 112px);min-height:570px;border:0;background:#fff}
.workspace iframe[hidden]{display:none}
.home{max-width:850px;margin:36px auto;padding:35px 40px;background:white;border:1px solid var(--border);border-radius:18px}
.home h1{font-size:29px;margin:0 0 10px}.home p{color:#5b7689;font-size:16px}
.home-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:23px}
.home-grid button{cursor:pointer;text-align:left;border:1px solid var(--border);border-radius:12px;background:#f5f9fe;padding:17px;color:var(--navy);font:inherit;font-weight:650}
.home-grid button:hover{border-color:var(--blue)}.home-grid small{display:block;margin-top:6px;color:#678195;font-weight:400}
.fine{font-size:12px!important;margin-top:22px}
@media(max-width:780px){.appbar{gap:7px;padding:10px}.brand{width:100%}.toolbar{padding:5px 10px}.home{border-radius:0;margin:0;padding:23px 18px}.workspace iframe{height:calc(100dvh - 158px)}}
@media print{.appbar,.toolbar{display:none}.workspace iframe{min-height:100vh;height:100vh}}
</style></head>
<body>
<header class="appbar"><div class="brand">ПОГРУЗЧИК <span class="sub">· AmurCargo · офлайн</span></div><span class="version-badge" data-project-version="__PROJECT_VERSION__">v__PROJECT_VERSION__</span>
<nav aria-label="Разделы проекта">
<button type="button" data-section="home" aria-current="page">Главная</button>
<button type="button" data-section="sim">3D-симулятор</button>
<button type="button" data-section="assembly">Сборка</button>
<button type="button" data-section="purchase">Покупки</button>
<button type="button" data-section="quick">Как начать</button>
<button type="button" data-section="calibration">Калибровка</button>
</nav></header>
<div class="toolbar"><span id="sectionLabel">Автономный комплект: все страницы в одном файле</span>
<button type="button" id="printPage" disabled>Печать раздела</button>
<button type="button" id="downloadPage" disabled>Скачать раздел отдельно</button></div>
<main class="workspace" id="workspace">
<section class="home" id="home">
<h1>ПОГРУЗЧИК</h1>
<p>Все страницы AmurCargo находятся прямо в этом HTML-файле. Откройте его в Chrome или Edge — интернет и веб-сервер не нужны.</p>
<div class="home-grid">
<button type="button" data-section="sim">3D-симулятор<small>Поле, движение, настройка, Arduino и сохранение настроек</small></button>
<button type="button" data-section="assembly">Сборка и подключение<small>Пошаговая иллюстрированная инструкция, схемы и проверка узлов</small></button>
<button type="button" data-section="purchase">Список покупок<small>Наличие, количество, полезные ссылки и печать</small></button>
<button type="button" data-section="quick">Как начать<small>Краткий план первой настройки и заезда</small></button>
<button type="button" data-section="calibration">Калибровка<small>Как согласовать симуляцию с настоящим роботом</small></button>
</div>
<p class="fine">Симуляция, встроенные рисунки и инструкции доступны без сети. Ссылки на сайты производителей требуют интернета. Для USB-прошивки нужен поддерживающий Web Serial браузер; если браузер ограничивает доступ из встроенной страницы, нажмите «Скачать раздел отдельно» и откройте его HTML напрямую.</p>
</section></main>
<script id="bundleData" type="application/json">__PAGE_JSON__</script>
<script>
(()=>{'use strict';
const pages=JSON.parse(document.getElementById('bundleData').textContent);
const workspace=document.getElementById('workspace'),home=document.getElementById('home');
const frames=Object.create(null),buttons=[...document.querySelectorAll('[data-section]')];
const label=document.getElementById('sectionLabel'),printBtn=document.getElementById('printPage'),downloadBtn=document.getElementById('downloadPage');
let active='home';
function open(id){
  if(id!=='home'&&!Object.prototype.hasOwnProperty.call(pages,id))id='home';
  active=id;
  home.hidden=id!=='home';
  for(const [key,frame] of Object.entries(frames))frame.hidden=key!==id;
  if(id!=='home'&&!frames[id]){
    const frame=document.createElement('iframe');
    frame.title=pages[id].title;
    frame.setAttribute('allow','serial; usb');
    frame.setAttribute('referrerpolicy','no-referrer');
    frame.hidden=false;
    frames[id]=frame;
    workspace.appendChild(frame);
    frame.srcdoc=pages[id].html;
  }
  for(const button of buttons){
    const selected=button.dataset.section===id;
    if(button.closest('nav')){if(selected)button.setAttribute('aria-current','page');else button.removeAttribute('aria-current');}
  }
  label.textContent=id==='home'?'Автономный комплект: все страницы в одном файле':pages[id].title;
  printBtn.disabled=downloadBtn.disabled=id==='home';
  if(id!=='home'){
    const frame=frames[id];
    requestAnimationFrame(()=>{try{frame.contentWindow.dispatchEvent(new Event('resize'));}catch(_){}});
  }
}
function navigate(id){if(location.hash==='#'+id)open(id);else location.hash=id;}
buttons.forEach(btn=>btn.addEventListener('click',()=>navigate(btn.dataset.section)));
window.addEventListener('hashchange',()=>open(decodeURIComponent(location.hash.slice(1))));
printBtn.addEventListener('click',()=>{if(active!=='home')frames[active].contentWindow.print();});
downloadBtn.addEventListener('click',()=>{
  if(active==='home')return;
  const page=pages[active],url=URL.createObjectURL(new Blob([page.html],{type:'text/html;charset=utf-8'}));
  const link=document.createElement('a');link.href=url;link.download=page.filename;document.body.appendChild(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),60000);
});
open(decodeURIComponent(location.hash.slice(1))||'home');
})();
</script></body></html>
"""
    text = shell.replace("__PAGE_JSON__", payload).replace("__PROJECT_VERSION__", version)
    OUTPUT.write_text(text, encoding="utf-8")
    print("Built", OUTPUT.relative_to(ROOT), OUTPUT.stat().st_size, "bytes, sections:", ", ".join(pages))


if __name__ == "__main__":
    build()
