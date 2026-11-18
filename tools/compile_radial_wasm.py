from pathlib import Path
import json,re,subprocess,os,shutil
from firmware_artifacts import sha256, source_digest
R=Path(__file__).resolve().parents[1];O=R/'simulator'
src=(O/'WebAssembly.cpp').read_text(encoding='utf-8');exports=re.findall(r'\b(?:void|int)\s+([a-z_]+)\(',src)
env=os.environ.copy();env['ZIG_GLOBAL_CACHE_DIR']=str(R/'tools/radial_zig_cache')
compiler=os.environ.get('ZIG') or shutil.which('zig') or str(R/'tools/hostcompiler/ziglang/zig.exe')
args=[compiler,'c++','-target','wasm32-freestanding','-Oz','-nostdlib','-fno-exceptions','-fno-rtti','-fno-builtin-memset','-fno-builtin-memcpy','-Wl,--no-entry']+['-Wl,--export='+x for x in exports]+[str(O/'WebAssembly.cpp'),'-o',str(O/'FirmwareCore.wasm')]
subprocess.run(args,env=env,check=True);print('WASM bytes', (O/'FirmwareCore.wasm').stat().st_size,'exports',len(exports))

(O/'FirmwareCore.json').write_text(json.dumps(dict(
    sha256=sha256((O/'FirmwareCore.wasm').read_bytes()),
    source_sha256=source_digest('wasm'),
), indent=2)+'\n', encoding='utf-8')
