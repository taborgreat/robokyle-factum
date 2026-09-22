// Robo Kyle EMG Band - v4: constant-thickness cuff, boards tangent to the arm
part = "all";
$fn = 64;

pico_l = 51;  pico_w = 21;  pico_hole_dx = 47; pico_hole_dy = 11.4;
batt_l = 50;  batt_w = 30.5; batt_h = 8.3;
chg_l = 19;   chg_w = 6.5;  chg_h = 7;   chg_pin = 8;   // measured; pins hang chg_pin below the board
strip_l = 60; strip_w = 25; strip_t = 1.6; hdr_base = 2.5;
imu_l = 24;   imu_w = 14.5; imu_h = 3.5;   // measured
motor_d = 10; button_hole = 7; led_d = 5.2; sw_slot = [7, 3.2];
elec_l = 38;  elec_w = 22;  elec_h = 4;
qi_board = [20, 14, 3];                            // Qi receiver's small board (VERIFY)
front = 1;                                         // +1: the +Y wall faces the chest (anterior). Set -1 for the other arm.
foam_t = 1.5;
clr = 1.2;                                         // printed-part clearance on every pocket side

arm_r = 44; plate_t = 2.2; wall = 2; floor_t = 2; lid_t = 1.6; loop_w = 20;
batt_y = -14.5; strip_y = 14.5; batt_x = 2.5; chg_x = -33; chg_y = -10;
in_l = 76; in_w = 64; box_l = in_l + 2*wall; box_w = in_w + 2*wall;
corner_r = 7; screw_d = 2.3; z0 = -25;
scr_x = box_l/2 - 6; scr_y = box_w/2 - 7;
function arm_z(y) = -arm_r + sqrt(arm_r*arm_r - y*y);
boss_top = arm_z(scr_y) + plate_t + 5;                 // vertical boss top at the screw corners

// radial stack above the arm surface (everything measured along the arm normal)
r_floor  = plate_t + floor_t;                       // cavity floor
r_batt   = r_floor + foam_t + 0.3 + batt_h;         // battery top
r_pico   = r_floor + 2 + strip_t + hdr_base + 1 + 3; // Pico USB top (2 mm standoffs)
service  = 3.5;                                      // room under the lid for the Qi board and LED legs
r_in     = max(r_batt, r_pico) + service;            // cavity ceiling
r_out    = r_in + lid_t;                             // outer shell

function ang(y) = asin(y/arm_r);   // tilt to be tangent at y
module arm_cyl(dr=0){ translate([0,0,-arm_r]) rotate([0,90,0]) cylinder(r=arm_r+dr, h=400, center=true); }
module rrect(l,w,h,r){ linear_extrude(h) offset(r) offset(-r) square([l,w],center=true); }
// a rounded-rect footprint extruded radially: between arm radii r1 and r2
module cuff(l,w,r1,r2,rr){ intersection(){ difference(){ arm_cyl(r2); arm_cyl(r1); } translate([0,0,z0]) rrect(l,w,100,rr); } }
// place a part tangent to the arm at (x,y), sitting at radial height dr (part drawn with its base at z=0)
module on_out(x,y_out,dr){ translate([x,0,-arm_r]) rotate([-asin(y_out/(arm_r+dr)),0,0]) translate([0,0,arm_r+dr]) children(); }
module on_arm(x,y,dr){ translate([x,0,-arm_r]) rotate([-asin(y/arm_r),0,0]) translate([0,0,arm_r+dr]) children(); }

module box(){
  difference(){
    cuff(box_l, box_w, plate_t, r_in, corner_r);                 // shell (lid is separate, above r_in)
    cuff(in_l, in_w, r_floor, r_in+5, corner_r-wall);            // cavity
    // USB slot at the Pico end, tangent at strip_y
    on_arm(-box_l/2, strip_y, r_floor + 2 + strip_t + hdr_base + 2.5) cube([wall*3, 12, 8], center=true);
    on_arm( box_l/2, strip_y, r_floor + 2 + strip_t + 4) cube([wall*3, 16, 8], center=true);   // cable exit
    on_out(18, front*box_w/2, r_floor + 6) cube([sw_slot[0], wall*3, sw_slot[1]], center=true);   // kill switch, chest-facing wall, elbow end
    on_arm(chg_x, chg_y, r_floor - 1.6) cube([3, chg_l-4, 4], center=true);                             // charger pin slot in the floor
    for (sx=[-1,1], sy=[-1,1]) translate([sx*scr_x, sy*scr_y, z0]) { cylinder(d=screw_d, h=60); cylinder(d=6.6, h=boss_top - z0 + 1.5); }
  }
  intersection(){
    cuff(in_l+0.1, in_w+0.1, 0, r_in, corner_r-wall);
    difference(){
      union(){
        // battery bay, tangent at batt_y
        on_arm(batt_x, batt_y, r_floor-3) {
          for (sy=[-1,1]) translate([-(batt_l-14)/2, sy*(batt_w/2-4)-1.5, 0]) cube([batt_l-14, 3, 3+foam_t+0.3], center=false);
          difference(){ rrect(batt_l+2*clr+4, batt_w+2*clr+4, 3+foam_t+0.3+3, 2); rrect(batt_l+2*clr, batt_w+2*clr, 60, 1.5); }
        }
        // charger pocket
        on_arm(chg_x, chg_y, r_floor-3) difference(){
          rrect(chg_w+2*clr+3, chg_l+2*clr+3, 3+foam_t+0.3+5, 1);
          translate([0,0,2]) rrect(chg_w+2*clr, chg_l+2*clr, 40, 0.5);
          translate([0,0,2]) cube([chg_w+2*clr+10, chg_l-6, 40], center=true);   // open the long sides in the middle: two corner brackets
        }
        // Pico strip standoffs, tangent at strip_y
        for (sx=[-1,1], sy=[-1,1]) on_arm(sx*pico_hole_dx/2, strip_y, r_floor-3) translate([0, sy*pico_hole_dy/2, 0]) cylinder(d=5.5, h=5);
      }
      for (sx=[-1,1], sy=[-1,1]) on_arm(sx*pico_hole_dx/2, strip_y, r_floor-3) translate([0, sy*pico_hole_dy/2, -1]) cylinder(d=1.7, h=8);
      arm_cyl(r_floor);
    }
  }
}

edge_r = 3;   // fillet on the lid's outer rim
module lid(){
  difference(){
    union(){
      // rounded cap: minkowski of an inset cuff with a sphere, then keep only above r_in
      intersection(){
        minkowski(){ cuff(box_l-2*edge_r, box_w-2*edge_r, r_in-edge_r-1, r_out-edge_r, max(corner_r-edge_r,1)); sphere(r=edge_r, $fn=20); }
        cuff(box_l+1, box_w+1, r_in, r_out+1, corner_r);
      }
      cuff(in_l-0.4, in_w-0.4, r_in-2.4, r_in+0.01, corner_r-wall);      // lip
    }
    // hollow, following the rounded cap with wall lid_t
    intersection(){
      minkowski(){ cuff(in_l-2*edge_r, in_w-2*edge_r, r_in-edge_r-3, r_out-lid_t-edge_r, max(corner_r-wall-edge_r,1)); sphere(r=edge_r, $fn=20); }
      cuff(in_l-0.4, in_w-0.4, r_in-3, r_out, corner_r-wall);
    }
    on_out(-18, front*(in_w/2-10), r_in-5) cylinder(d=button_hole, h=15);     // button, chest side
    on_out(-18, -front*(in_w/2-10), r_in-5) cylinder(d=led_d, h=15);          // RGB LED, triceps side (visible from behind)
    translate([scr_x, -scr_y, z0]) cylinder(d=screw_d, h=80);                  // lid backup screw, vertical, shares a corner
  }
  // coin motor cradle on the lid underside, over the Pico side (3.5 mm clearance there)
  on_out(12, front*16, r_in-2.4) difference(){ cylinder(d=motor_d+3, h=2.4); translate([0,0,-1]) cylinder(d=motor_d+0.4, h=5); }
  // Qi receiver board pocket on the lid underside, over the charger corner; the coil tapes flat beside it (ferrite toward the Pico)
  on_arm(chg_x+10, chg_y+2, r_in-qi_board[2]-0.5) difference(){ rrect(qi_board[0]+3, qi_board[1]+3, qi_board[2]+0.5, 1); translate([0,0,-1]) rrect(qi_board[0]+2*clr, qi_board[1]+2*clr, 10, 0.5); translate([0,0,-1]) cube([qi_board[0]+10, 4, 10], center=true); }
}

module plate(){
  pl = box_l + 6; pw = box_w + 6;
  difference(){
    union(){
      cuff(pl, pw, 0, plate_t, corner_r+2);
      for (sx=[-1,1], sy=[-1,1]) translate([sx*scr_x, sy*scr_y, z0]) cylinder(d=6.2, h=boss_top - z0);
    }
    arm_cyl(0);
    for (sx=[-1,1], sy=[-1,1]) translate([sx*scr_x, sy*scr_y, boss_top-4.5]) cylinder(d=3.0, h=10);
    for (i=[-3:3]) for (sy=[-1,1]) on_arm(i*(pl/8), sy*(pw/2-2.5), -10) cylinder(d=2, h=30);
    for (i=[-2:2]) for (sx=[-1,1]) on_arm(sx*(pl/2-2.5), i*(pw/6), -10) cylinder(d=2, h=30);
  }
}

// forearm pucks (unchanged)
module loop_slots(l){ for (sx=[-1,1]) translate([sx*(l/2 - 2.5), 0, -1]) cube([2.2, loop_w+1, 20], center=true); }
module electrode_puck(){ pl = elec_l + 12; pw = max(elec_w + 6, loop_w + 8); t = 4;
  difference(){ rrect(pl, pw, t, 3); translate([0,0,-1]) rrect(elec_l+2*clr, elec_w+2*clr, elec_h+1, 1.5); translate([0,0,-1]) rrect(elec_l-6, elec_w-6, 20, 1); loop_slots(pl); translate([0, pw/2, t/2]) cube([6, 6, t+2], center=true); } }
module shim(){ pl = elec_l + 12; pw = max(elec_w + 6, loop_w + 8); difference(){ rrect(pl, pw, 1, 3); loop_slots(pl); } }
module imu_puck(){ pl = imu_l + 10; pw = max(imu_w + 8, loop_w + 8); t = imu_h + 5;
  difference(){ rrect(pl, pw, t, 3); translate([0,0,2]) rrect(imu_l+2*clr, imu_w+2*clr, 20, 1); loop_slots(pl); translate([-pl/2, 0, t-3]) cube([8, 8, 6], center=true); }
  for (sx=[-1,1]) translate([sx*9.5, 0, 2.8]) difference(){ cube([8,5,1.6],center=true); cube([5,1.9,5],center=true); } }
module imu_lid(){ pl = imu_l + 10; pw = max(imu_w + 8, loop_w + 8); rrect(pl, pw, 1.6, 3); translate([0,0,-1.8]) difference(){ rrect(imu_l+0.6, imu_w+0.6, 1.8, 1); rrect(imu_l-2, imu_w-2, 10, 1); } }

if (part=="box") box();
if (part=="lid") lid();
if (part=="plate") plate();
if (part=="electrode_puck") electrode_puck();
if (part=="shim") shim();
if (part=="imu_puck") imu_puck();
if (part=="imu_lid") imu_lid();
if (part=="assembled"){ box(); lid(); plate(); }
if (part=="boxcut2") difference(){ union(){box(); lid();} translate([-70,0,0]) cube([140,200,200],center=true); }
if (part=="all"){ box(); translate([0, box_w+15, 0]) lid(); translate([0, -(box_w+15), 0]) plate();
  translate([box_l+30, 20, 0]) electrode_puck(); translate([box_l+30, -20, 0]) imu_puck(); translate([box_l+30, -50, 0]) imu_lid(); translate([box_l+30, 50, 0]) shim(); }
echo(r_floor=r_floor, r_batt=r_batt, r_pico=r_pico, r_in=r_in, r_out=r_out);
if (part=="dbg") difference(){ cuff(box_l, box_w, plate_t, r_in, corner_r); cuff(in_l, in_w, r_floor, r_in+5, corner_r-wall); }
if (part=="dbg2") cuff(in_l, in_w, r_floor, r_in+5, corner_r-wall);
