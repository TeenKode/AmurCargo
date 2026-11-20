/* UNO R3, two DC gear motors + configured driver, SG90, 3 LDRs, HW-511 cargo sensor and one START button.
 * Navigation is identical to FirmwareCore.wasm in the simulator.
 * First tune RobotConfig.h and calibrate. Read README_RU.md before connecting hardware.
 * A long START hold arms the stationary robot; the next short press starts the mission.
 * Press START during motion to stop. No remote driving is accepted during a mission.
 */
#include "RobotHardware.h"
RobotHardware app;
void setup(){app.init();}
void loop(){app.tick();}
