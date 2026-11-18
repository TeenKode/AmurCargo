const fs=require('fs'),path=require('path'),os=require('os');
const cached=path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const pw=require(process.env.PLAYWRIGHT_MODULE||(fs.existsSync(cached)?cached:'playwright'));
const edge=['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Microsoft/Edge/Application/msedge.exe'].find(p=>fs.existsSync(p));
module.exports={...pw,browserExecutable:process.env.BROWSER_EXECUTABLE||edge};
