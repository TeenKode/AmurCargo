// AmurCargo - removable-fork HW-511 cargo detector bracket (prototype v1).
// Millimetres. Local axes match tools/build_removable_forks.py:
// X across the forks, +Y towards cargo, +Z up; fork spine front = Y 4.
// Open with OpenSCAD, set view="part" for 3D printing.
$fn = 48;
view = "assembly"; // ["part", "assembly"]
fork_height = "low"; // ["low", "high"]
show_target = true;
show_sensor = true;

// Measure the actual HW-511 PCB before final printing; 48 x 10 is nominal.
pcb_length = 48;
pcb_width = 10;
pcb_thickness = 1.6;
pcb_bottom_z = 12;
foam_to_pcb = 0.8;
foam_to_spine = 1.0; // VHB/foam tape thickness between Y=4 and Y=5
mount_slot_width = 2.9; // M2.5 clearance; two HW-511 holes nominally 3 mm
// Slot accounts for differing hole pitches between HW-511 batches.
slot_z_min = 15;
slot_z_max = 31;

// Single-piece printable bracket. Two M2.5 fasteners in the long slot,
// or thin adhesive foam on the PCB back. Do not glue across the trimmer.
module bracket() {
  difference() {
    union() {
      // Adhesive foot sits on the undrilled central spine at Z=40..54.
      translate([-7.5, 5, 40]) cube([15, 3.2, 14]);
      // Thick neck moves the optical plane forward; no fork modification.
      translate([-4.5, 8.2, 44]) cube([9, 10.8, 6]);
      // Upright board tray; the optical components point towards +Y.
      translate([-7.4, 19, 10.5]) cube([14.8, 2.3, 51.5]);
      // Bottom stop supports PCB, without covering the optics.
      translate([-6.2, 21.3, 10.5]) cube([12.4, 2.5, 1.5]);
      // Short side guides leave pins, LEDs and potentiometer accessible.
      for (x = [-7.4, 5.35])
        translate([x, 21.3, 34]) cube([2.05, 2.5, 17]);
    }
    // Oblong bolt slot in the board tray; position determined by the
    // actual PCB holes, not assumed to be identical between manufacturers.
    hull() for (z = [slot_z_min,slot_z_max])
      translate([0, 18.8, z]) rotate([-90,0,0])
        cylinder(d=mount_slot_width, h=3.1);
    // Behind the soldered 3-pin header, remove plastic from the upper back.
    translate([-4.1, 20.5, 55]) cube([8.2, 1.0, 7.2]);
  }
}

// Visual-only representations; these are not printable parts.
module pcb_proxy() {
  color([0.06,0.21,0.13])
    translate([-pcb_width/2, 21.3+foam_to_pcb, pcb_bottom_z])
      cube([pcb_width,pcb_thickness,pcb_length]);
  color([0.8,0.82,0.88])
    for (z=[pcb_bottom_z+4,pcb_bottom_z+17])
      translate([0,21.3+foam_to_pcb-0.1,z])
        rotate([-90,0,0]) difference(){ cylinder(d=3.0,h=pcb_thickness+0.2); cylinder(d=2.2,h=pcb_thickness+0.3); }
  // Emit and receive side by side, not a distance-measuring device.
  for (x = [-2.4,2.4])
    color(x<0 ? [0.07,0.09,0.11] : [0.1,0.35,0.9])
      translate([x,23.7,pcb_bottom_z+10]) rotate([-90,0,0])
        cylinder(d=3.8,h=4.0);
  color([0.18,0.24,0.35])
    translate([-3.0,23.7,pcb_bottom_z+27]) cube([6,3.3,6]);
  for (x=[-2.54,0,2.54])
    color([0.73,0.72,0.61]) translate([x,22.4,pcb_bottom_z+pcb_length])
      cylinder(d=0.7,h=6);
}

// Simplified *context* derived from build_removable_forks.py; not a replacement
// for the actual 01_Removable_Fork_Spine.step/STL in AmurCargo.
module spine_proxy() {
  color([0.5,0.59,0.63,0.30]) difference() {
    union() {
      translate([-35,0,54]) cube([70,4,40]);
      translate([-8,0,0]) cube([16,4,58]);
      for (x=[-27.5,19.5]) translate([x,0,0]) cube([8,8,58]);
      for (x=[-19.5,9.5]) translate([x,0,0]) cube([10,2,58]);
      for (z=[0,30]) translate([-27.5,0,z]) cube([55,2,8]);
    }
    translate([-4.5,-0.5,12]) cube([9,5,8]);
    translate([-16,-0.5,70]) cube([32,5,8]);
  }
}
module fork_proxy() {
  dz = fork_height=="high" ? 26 : 0;
  color([0.85,0.60,0.16,0.85])
    for (x=[-19.5,9.5]) {
      translate([x,2,dz]) cube([10,6,27]);
      translate([x+0.5,8,dz]) cube([6,48,4]);
      translate([x+0.5,53,dz+4]) cube([6,3,2]);
    }
}
module assembly() {
  spine_proxy(); fork_proxy();
  color([0.95,0.65,0.21]) bracket();
  if (show_sensor) pcb_proxy();
  // Approximate cargo face in front of the optics (11 mm beyond lens).
  if (show_target) color([0.81,0.24,0.23,0.2])
    translate([-9,39,7]) cube([18,3,34]);
}
if (view=="part") bracket(); else assembly();
