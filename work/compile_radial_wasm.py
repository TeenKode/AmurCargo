from pathlib import Path
import re,subprocess,os,shutil
R=Path(__file__).resolve().parents[1];O=R/'outputs/AmurCargo_Radial'
src=(O/'WebAssembly.cpp').read_text(encoding='utf-8');exports=re.findall(r'\b(?:void|int)\s+([a-z_]+)\(',src)
env=os.environ.copy();env['ZIG_GLOBAL_CACHE_DIR']=str(R/'work/radial_zig_cache')
compiler=os.environ.get('ZIG') or shutil.which('zig') or str(R/'work/hostcompiler/ziglang/zig.exe')
args=[compiler,'c++','-target','wasm32-freestanding','-Oz','-nostdlib','-fno-exceptions','-fno-rtti','-fno-builtin-memset','-fno-builtin-memcpy','-Wl,--no-entry']+['-Wl,--export='+x for x in exports]+[str(O/'WebAssembly.cpp'),'-o',str(O/'FirmwareCore.wasm')]
subprocess.run(args,env=env,check=True);print('WASM bytes', (O/'FirmwareCore.wasm').stat().st_size,'exports',len(exports))
