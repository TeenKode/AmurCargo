from pathlib import Path
import zipfile,json,sys
R=Path(__file__).resolve().parents[1];target=R/'tools/project_export_check';target.mkdir(exist_ok=True)
with zipfile.ZipFile(R/'tools/exported_project_test.zip') as z:
 assert z.testzip() is None
 assert set(z.namelist())=={'RadialRobot/'+s for s in ('RadialRobot.ino','RobotConfig.h','RobotHardware.h','RadialCore.h','Settings.h','README.txt')}
 z.extractall(target)
header=(target/'RadialRobot/RobotConfig.h').read_text(encoding='utf-8')
for line in ('s.v[P_DROP_RAY]=3;','s.v[P_DRIVE_PWM]=104;','s.zone[1][3][Z_OUT_MIN_MS]=777;','s.searchCount=3;','s.search[0]=7;','s.search[1]=3;','s.search[2]=1;'):assert line in header,line
script=(R/'tools/compile_radial_avr.py').read_text(encoding='utf-8')
script=script.replace("OUT=R/'simulator';SK=R/'firmware/RadialRobot';BUILD=R/'tools/radial_avr_build'", "OUT=R/'tools/project_export_check';SK=OUT/'RadialRobot';BUILD=OUT/'build'")
sys.argv=['compile_export','uno'];exec(compile(script,str(R/'tools/compile_radial_avr.py'),'exec'),{'__file__':str(R/'tools/compile_radial_avr.py')})
print(json.dumps(dict(exported_zip_valid=True,all_five_source_files_present=True,live_settings_verified=True,avr_project_compiled=True,physical_upload_tested=False)))
