// Robo Kyle claw gripper v1 - fin-ray two-jaw, Feetech STS3215, Pico 2 W
// openscad -D part=\"body\" -o body.stl claw.scad   parts: body lid gear_drive gear_idler finger pad cuff_stub all
part = "all";
$fn = 64;

// ---------- parts (mm) ----------
servo_l = 45.2; servo_w = 24.7; servo_h = 35;          // STS3215 body (VERIFY)
servo_ear_l = 52; servo_ear_w = 21; servo_ear_t = 3;   // ear span (holes) and thickness (VERIFY)
servo_shaft_x = 11;                                     // shaft offset from one end of the body (VERIFY)
servo_horn_d = 22;
batt_l = 55; batt_w = 31; batt_h = 16;                  // 2S 1000 mAh (VERIFY)
pico_l = 51; pico_w = 21; pico_h = 6;
drv_l = 40; drv_w = 33; drv_h = 12;                     // servo driver board (VERIFY)
bms_l = 48; bms_w = 8;   chg_l = 40; chg_w = 18; buck_l = 20; buck_w = 12;
bearing_od = 8; bearing_t = 3; pin_d = 3;

// ---------- gripper geometry ----------
gear_m = 2; gear_n = 20; gear_pd = gear_m*gear_n;       // module 2, 20 teeth, 40 mm pitch dia
gear_t = 8;                                             // gear thickness
pivot_dx = gear_pd;                                     // center distance
finger_l = 80; finger_base = 26; finger_tip = 10; finger_w = 18; finger_wall = 1.4; rib_t = 1.0; rib_n = 6;

// ---------- body ----------
wall = 3;
body_w = 72;                                            // servo at y=-20, idler at y=+20 (40 mm gear centers)
body_l = 24 + servo_l + batt_l + 3*wall + 12;           // gear block + servo + battery/electronics bay
body_h = servo_h + 8;                                   // servo standing, gear plane on top
corner_r = 6;
gear_plane_z = body_h;                                  // gears ride on top face
pivot_y = 0;                                            // pivots centered across width
pivot_x = body_l/2 - 12;                                // pivots near the front

module rrect(l,w,h,r){ linear_extrude(h) offset(r) offset(-r) square([l,w],center=true); }

// simple trapezoid-tooth spur gear (fine for printing, meshes with itself)
module gear(n=gear_n, m=gear_m, t=gear_t, bore=bearing_od){
  pr = m*n/2; ar = pr + m; rr = pr - 1.25*m;
  difference(){
    linear_extrude(t) union(){
      circle(r=rr);
      for (i=[0:n-1]) rotate(i*360/n) polygon([[rr-0.5,-m*0.95],[pr,-m*0.75],[ar,-m*0.35],[ar,m*0.35],[pr,m*0.75],[rr-0.5,m*0.95]]);
    }
    translate([0,0,-1]) cylinder(d=bore+0.2, h=t+2);
  }
}
module gear_drive(){   // bolts to the servo horn: horn screw pattern (VERIFY), plus bore for the horn boss
  difference(){
    union(){ gear(bore=0.1); }
    translate([0,0,-1]) cylinder(d=servo_horn_d+0.4, h=2.5);      // horn recess
    for (a=[0:90:270]) rotate(a) translate([7,0,-1]) cylinder(d=2.6, h=20);   // horn screws (VERIFY spacing)
    // finger mount: two M3 holes at the rim
    for (sx=[-1,1]) translate([gear_pd/2-6, sx*6, -1]) cylinder(d=2.8, h=20);
  }
}
module gear_idler(){
  difference(){
    gear();
    translate([0,0,gear_t-bearing_t-0.01]) cylinder(d=bearing_od+0.2, h=bearing_t+1);  // bearing seat top
    translate([0,0,-1]) cylinder(d=bearing_od+0.2, h=bearing_t+1);                     // bearing seat bottom
    for (sx=[-1,1]) translate([gear_pd/2-6, sx*6, -1]) cylinder(d=2.8, h=20);
  }
}

// fin-ray finger, printed lying flat (Z = finger width)
module finger(){
  difference(){
    union(){
      // outer shell
      linear_extrude(finger_w) difference(){
        polygon([[0,-finger_base/2],[finger_l,-finger_tip/2],[finger_l,finger_tip/2],[0,finger_base/2]]);
        offset(-finger_wall) polygon([[0,-finger_base/2],[finger_l,-finger_tip/2],[finger_l,finger_tip/2],[0,finger_base/2]]);
      }
      // ribs
      for (i=[1:rib_n]) let(x = i*finger_l/(rib_n+1), hw = (finger_base/2) + (finger_tip/2 - finger_base/2)*x/finger_l)
        translate([x, 0, finger_w/2]) cube([rib_t, 2*hw-finger_wall, finger_w], center=true);
      // base tab with mount holes
      translate([-8, -finger_base/2, 0]) cube([10, finger_base, finger_w]);
      // tip pocket for pad
      translate([finger_l-2, -finger_tip/2, 0]) cube([4, finger_tip, finger_w]);
    }
    for (sx=[-1,1]) translate([-3, sx*6, -1]) cylinder(d=3.2, h=finger_w+2);
    // pad dovetail slot along the gripping face (inner face is +Y side by convention)
    translate([finger_l-30, finger_base/2*0.55 - 2.0, finger_w/2]) cube([28, 2.2, 8], center=true);
    // conductive wire channel: outer (-Y) wall groove from tip to base, then a hole through the base tab
    translate([-8, -finger_base/2 - 0.2, finger_w/2]) rotate([0,90,0]) cylinder(d=2.0, h=finger_l+8);
    translate([finger_l-4, -finger_tip/2, finger_w/2]) rotate([0,0,0]) cylinder(d=2.0, h=finger_w);      // riser to the pad pocket at the tip
    translate([-3, 0, finger_w/2]) rotate([0,90,0]) cylinder(d=2.0, h=6, center=true);                   // through the tab, across
  }
}
module pad(){ // slides into the finger's slot; roughen after printing
  difference(){ cube([27.5, 2.0, 7.8], center=true); }
  translate([0, 2.2, 0]) cube([27.5, 2.4, 12], center=true);   // exposed grip face
}

module body(){
  bay_x0 = -body_l/2 + wall;                     // rear bay start
  bay_l  = body_l - 24 - servo_l - 3*wall - 6;    // rear bay length
  difference(){
    rrect(body_l, body_w, body_h, corner_r);
    // servo pocket, standing, shaft at (pivot_x, drive_y)
    translate([pivot_x - servo_shaft_x, drive_y, body_h - servo_h + 2 + 50]) cube([servo_l+0.6, servo_w+0.6, 100], center=true);
    for (sx=[-1,1], sy=[-1,1]) translate([pivot_x - servo_shaft_x + sx*servo_ear_l/2, drive_y + sy*servo_ear_w/2, body_h - 10]) cylinder(d=2.5, h=20);
    // idler pivot pin + top bearing seat
    translate([pivot_x, idler_y, 0]) { translate([0,0,-1]) cylinder(d=pin_d+0.2, h=body_h+2); translate([0,0,body_h-bearing_t]) cylinder(d=bearing_od+0.2, h=bearing_t+1); }
    // rear bay: battery on one side, Pico + boards on the other, open top (lid)
    translate([bay_x0 + bay_l/2, 0, body_h - 30 + 50]) cube([bay_l, body_w - 2*wall, 100], center=true);
    // divider rib is left standing: battery side (+Y) / electronics side (-Y)
    // USB-C charge port and kill switch in the rear wall
    translate([-body_l/2, -12, body_h-10]) cube([wall*3, 10, 4], center=true);
    translate([-body_l/2, -26, body_h-10]) cube([wall*3, 7, 3.2], center=true);
    // conductive wire pass-throughs: front wall beside each pivot, rear face beside the stub
    for (sy=[-1,1]) translate([body_l/2 - 6, sy*(pivot_dx/2 + 14), body_h - 6]) rotate([0,90,0]) cylinder(d=2.5, h=20, center=true);
    for (sy=[-1,1]) translate([-body_l/2, sy*30, body_h/2]) rotate([0,90,0]) cylinder(d=2.5, h=20, center=true);
    // cuff stub inserts on the rear face (M3 heat-set)
    for (sy=[-1,1], sz=[-1,1]) translate([-body_l/2 - 1, sy*16, body_h/2 + sz*10]) rotate([0,90,0]) cylinder(d=4.0, h=8);
  }
  // divider rib between battery and electronics inside the rear bay
  translate([bay_x0 + bay_l/2, 3, (body_h-30)/2 + 15]) cube([bay_l, 2, 30], center=true);
  // Pico standoffs on the electronics side
  for (sx=[-1,1], sy=[-1,1]) translate([bay_x0 + bay_l/2 + sx*pico_hole_dx/2, -18 + sy*pico_hole_dy/2, body_h-30]) difference(){ cylinder(d=5, h=4); cylinder(d=1.7, h=5); }
}
pico_hole_dx = 47; pico_hole_dy = 11.4;

module lid(){ // covers the electronics/battery bays; snaps at the rear
  difference(){
    rrect(body_l - 24 - servo_l - 6, body_w, 2, corner_r);
  }
}

module cuff_stub(){ // bolts to the rear face; the cuff attaches to its 4 M4 holes
  difference(){
    union(){ rrect(50, 46, 6, 4); translate([0,0,6]) rrect(30, 30, 6, 3); }
    for (sy=[-1,1], sz=[-1,1]) translate([sy*16, sz*10, -1]) cylinder(d=3.2, h=20);
    for (a=[45:90:315]) rotate(a) translate([18,0,5]) cylinder(d=4.2, h=10);
    for (sy=[-1,1]) translate([0, sy*20, -1]) cylinder(d=2.5, h=20);
  }
}

if (part=="body") body();
if (part=="lid") lid();
if (part=="gear_drive") gear_drive();
if (part=="gear_idler") gear_idler();
if (part=="finger") finger();
if (part=="pad") pad();
if (part=="cuff_stub") cuff_stub();
if (part=="all"){
  body();
  translate([pivot_x, drive_y, body_h]) rotate(9) gear_drive();
  translate([pivot_x, idler_y, body_h]) gear_idler();
  translate([pivot_x, drive_y, body_h+gear_t]) rotate([0,0,-20]) translate([14,0,0]) finger();
  translate([pivot_x, idler_y, body_h+gear_t]) rotate([0,0,20]) translate([14,0,0]) mirror([0,1,0]) finger();
  translate([-body_l/2 + (body_l-24-servo_l-6)/2 + wall, body_w+30, 0]) lid();
  translate([-body_l/2 - 40, 0, 0]) rotate([0,0,90]) cuff_stub();
  translate([body_l/2 + 60, 40, 0]) pad();
}
echo(body_l=body_l, body_w=body_w, body_h=body_h, pivot_x=pivot_x);
