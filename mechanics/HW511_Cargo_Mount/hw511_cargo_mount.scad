// AmurCargo / HW-511 cargo detector mount. Parametric mechanical revision v2.
// Based on user's actual black HW-511 photo and a 42 x 10.5 mm board
// (Velleman, Pimoroni, Otronic dimensional photo).
// All coordinates are millimetres. Local fork axes: X across, +Y forward
// toward cargo, +Z upward. Removable fork spine front plane is Y = 4.
// Board component positions are photo-derived approximations, NOT OEM CAD.
$fn = 72;
view = "assembly"; // ["part", "board", "assembly"]
fork_height = "low"; // ["low", "high"]
show_cargo = true;
show_spine = true;
show_sensor = true;

// Verified board footprint; thickness and hole layout are estimated.
pcb_length = 42.0;           // from edge-to-edge drawing, excludes header pins
pcb_width = 10.5;
pcb_thickness = 1.6;        // nominal, verify with caliper
hole_diameter = 4.0;        // estimated from user's face-on photograph
hole_from_nose = [4.0, 15.0]; // hole centres approx +/-0.7 mm on user's board
pcb_bottom_z = 12.5;        // sensing tip of PCB; rear connector points upwards
pcb_back_y = 21.95;
insulation_gap = pcb_back_y - 21.3; // thin insulating tape/foam, not in STL
pcb_front_y = pcb_back_y + pcb_thickness;

// Mount bolts through an oblong slot do not assume a manufacturer's pitch.
bolt_clearance = 2.9;  // M2.5 screw clearance, with washers sized to actual holes
slot_first_z = 14.0;
slot_last_z = 30.0;

// Printable one-piece bracket; fits between 19 mm inner fork faces.
module bracket() {
  difference() {
    union() {
      // Adhesive rear pad: 15 x 14 mm, 1 mm off the spine face (double tape).
      translate([-7.5, 5.0, 40]) cube([15, 3.2, 14]);
      // Neck supports the board without drilling the existing fork spine.
      translate([-4.5, 8.2, 44]) cube([9, 10.8, 6]);
      // Upright carrier, PCB sits on its +Y face with a thin insulation pad.
      translate([-7.4, 19, 11]) cube([14.8, 2.3, 45]);
      // Bottom stop keeps PCB from sliding down during vibration.
      translate([-6.2, 21.3, 11]) cube([12.4, 2.7, 1.5]);
      // Outer rails never cover either round optical lens or front trimmer.
      for (x = [-7.4, 5.5]) {
        translate([x, 21.3, 31]) cube([1.9, 2.9, 20]);
        translate([x, 21.3, 13]) cube([1.9, 2.9, 6]);
      }
    }
    // Long through-slot for BOTH PCB holes, even when they vary by batch.
    hull() for (z = [slot_first_z, slot_last_z])
      translate([0, 18.85, z]) rotate([-90, 0, 0])
        cylinder(d=bolt_clearance, h=3.0);
    // Top-end connector solder clearance. This is behind the contacts.
    translate([-4.4, 20.65, 52]) cube([8.8, .8, 4.2]);
  }
}

// Visual-only detailed model of the observed HW-511 revision. Board shape,
// sensor pair, IC, potentiometer, header, LEDs and two mounting holes.
module pcb_bare() {
  color([0.035, 0.05, 0.047])
  difference() {
    translate([-pcb_width/2, pcb_back_y, pcb_bottom_z])
      cube([pcb_width, pcb_thickness, pcb_length]);
    for (dz=hole_from_nose)
      translate([0, pcb_back_y - .1, pcb_bottom_z + dz])
        rotate([-90,0,0]) cylinder(d=hole_diameter,h=pcb_thickness+.2);
  }
  // Copper/gold annular rings, nominal only; not printed as part of mount.
  for (dz=hole_from_nose)
    color([.72,.62,.32])
      translate([0,pcb_front_y+.015,pcb_bottom_z+dz])
        rotate([-90,0,0]) difference() {
          cylinder(d=4.6,h=.05);
          translate([0,0,-.01]) cylinder(d=hole_diameter,h=.08);
        }
}
module pcb_components() {
  // Black reflective optical head, approx 9.0 wide x 6.0 long, in the nose.
  color([0.035,.034,.042])
    translate([-4.55,pcb_front_y,pcb_bottom_z+5.9]) cube([9.1,3.6,6.4]);
  for (x=[-2.15,2.15]) {
    color(x<0?[.045,.044,.050]:[.02,.19,.50])
      translate([x,pcb_front_y+3.58,pcb_bottom_z+9.1])
        rotate([-90,0,0]) cylinder(d=3.35,h=.55);
    color(x<0?[.0,.0,.0]:[.07,.39,.76])
      translate([x,pcb_front_y+4.13,pcb_bottom_z+9.1])
        rotate([-90,0,0]) cylinder(d=2.25,h=.07);
  }
  // Variable resistor: blue body and white slotted adjustment cap.
  color([.01,.23,.85])
    translate([-3.45,pcb_front_y,pcb_bottom_z+21]) cube([6.9,3.5,6.9]);
  color([.89,.88,.73])
    translate([0,pcb_front_y+3.5,pcb_bottom_z+24.45])
      rotate([-90,0,0]) cylinder(d=5.35,h=.27);
  color([.12,.15,.14])
    translate([-2.4,pcb_front_y+3.75,pcb_bottom_z+24.1])
      cube([4.8,.09,.7]);
  // LM393 eight-pin comparator and its silver pin ends.
  color([.05,.056,.068])
    translate([-2.2,pcb_front_y,pcb_bottom_z+31.2]) cube([4.4,1.4,5.9]);
  for (x=[-3.0,2.55],dz=[31.7,33.0,34.3,35.6])
    color([.68,.69,.69])
      translate([x,pcb_front_y+.15,pcb_bottom_z+dz]) cube([.48,.3,.58]);
  // SMD indicators/resistors in roughly the locations of the user's photo.
  for (x=[-3.9,3.9],dz=[20.2,29.9])
    color([.53,.54,.55])
      translate([x-.45,pcb_front_y,pcb_bottom_z+dz]) cube([.9,.48,1.55]);
  color([.95,.91,.77])
    translate([-4.0,pcb_front_y,pcb_bottom_z+38.2]) cube([2.5,.6,1.2]);
  color([.64,.59,.38])
    translate([3,pcb_front_y,pcb_bottom_z+19.1]) cube([1.9,.5,1.1]);
  // Straight 2.54 mm pin header and pin tails exit the rear/top PCB end.
  color([.025,.029,.035])
    translate([-4.65,pcb_front_y,pcb_bottom_z+39.6]) cube([9.3,1.85,2.5]);
  for (x=[-2.54,0,2.54])
    color([.74,.75,.67])
      translate([x,pcb_front_y+.87,pcb_bottom_z+41.1])
        cylinder(d=.76,h=7.8);
}
module detailed_board() { pcb_bare(); pcb_components(); }

// This scene gives mounting context, but is NOT the measured original STEP
// assembly. Precise moving-fork CAD is in ../Fork_Adapters/ for collision QA.
module spine_proxy() {
  color([.38,.53,.61,.34]) difference() {
    union() {
      translate([-35,0,54]) cube([70,4,40]);
      translate([-8,0,0]) cube([16,4,58]);
      for (x=[-27.5,19.5]) translate([x,0,0]) cube([8,8,58]);
      for (x=[-19.5,9.5]) translate([x,0,0]) cube([10,2,58]);
      for (z=[0,30]) translate([-27.5,0,z]) cube([55,2,8]);
    }
    translate([-4.5,-.5,12]) cube([9,5,8]);
    translate([-16,-.5,70]) cube([32,5,8]);
  }
}
module fork_proxy() {
  dz = fork_height=="high" ? 26 : 0;
  color([.93,.62,.19,.85]) for (x=[-19.5,9.5]) {
    translate([x,2,dz]) cube([10,6,27]);
    translate([x+.5,8,dz]) cube([6,48,4]);
    translate([x+.5,53,dz+4]) cube([6,3,2]);
  }
}
module scene() {
  if (show_spine) spine_proxy();
  fork_proxy();
  color([.91,.66,.19]) bracket();
  if (show_sensor) detailed_board();
  // Reflective surface 10-15mm ahead of sensing lenses, illustrative only.
  if (show_cargo) color([.78,.26,.24,.23])
    translate([-9,40,7]) cube([18,2,33]);
}
if (view == "part") bracket();
else if (view == "board") detailed_board();
else scene();