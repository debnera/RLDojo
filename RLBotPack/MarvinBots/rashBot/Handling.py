from Util import *


def controls(s):

    s.throttle = curve1((s.y - .63 * s.brakes * s.pyv / ((1 - s.pyv / 2300) * 3 + 1)) / 999)

    s.steer = curve1(Range180(s.a - s.av / 55, 1))
    s.pitch = regress(-s.i - s.iv / 17)
    s.yaw = regress(Range180(s.a - s.av / 12, 1))
    s.roll = regress(Range180(- s.r + s.rv / 22, 1)) * (abs(s.a) < .15)

    s.boost = s.throttle > .5 and abs(s.a) < .12 and (
        s.poG or abs(s.i) < .2) and abs(s.y) > 99 and s.pyv < 2260

    s.powerslide = s.jump = 0

    # general powerslide
    if s.throttle * s.pyv >= 0 and s.av * s.steer >= 0 and s.pxv * s.steer >= 0 and (
        # sliding
        (ang_dif(s.a, s.pva, 1) < .15 and .05 < abs(s.a) < .95) or (
        # turning
        s.pL[2] < 99 and .24 < ang_dif(s.a, s.av / 9, 1) < .76) or (
        # landing
        s.gtime < .05 and ang_dif(s.a, s.pva, 1) < .25 and not s.kickoff)):
            s.powerslide = 1

    # turn 180°
    if s.d2 > 400 and abs(s.a + s.av / 2.25) > 0.45:
        if abs(s.a) > 0.98:
            s.steer = 1
        if s.d2 > 600 and s.pyv < -90:
            if (abs(s.a) < 0.98 and abs(s.av) > 0.5 and
                    ang_dif(s.a, s.pva, 1) < .25):
                s.powerslide = 1
            s.steer = -sign(s.steer)
        elif s.d2 > 800 and abs(s.a) < 0.95 and s.pyv < 1000:
            s.throttle = 1

    # three point turn
    if (s.poG and 20<abs(s.x)<400 and abs(s.y)<200 and .35<abs(s.a)<.65 
        and abs(s.pyv)<550 and abs(s.yv)<550 ):
        s.throttle = -sign(s.throttle)
        s.steer = -sign(s.steer) 

    if s.shoot and to_jump(s):
        s.jumper = 1

    # # takeoff
    # if (s.z>250 and ang_dif(s.a,s.pva,1)<.1 and s.yv > -350 and 
    #     s.z*1.05<s.d2<s.z*(1.08+s.pB/55) and s.z<s.jcount*250+s.pB*12):
    #     s.jumper = 1

    # jumping off walls
    if ((s.z>1350 or ((s.d<s.z*1.5 or s.vd<400) and s.pL[2]<500 
        and abs(s.a)<.15 and s.bL[2] < 500)) and s.poG and 
        s.pL[2]>60 and (abs(0.5-abs(s.a))>0.25 or s.d>2500)) or (
        s.poG and s.pL[2]>1900 and s.d2pv<120 )  : 
            s.jump = 1

    # flip
    if (s.flip and s.d>400 and ang_dif(s.a,s.pva,1)<.06 and s.pB<80 and
        s.pvd<2200 and s.jcount>0 and (s.gtime>0.05 or not s.poG) and
        not s.jumper and abs(s.i)<.2 and ((s.pyv>1640 and s.ty-s.yv/4>3500)
        or (abs(s.a)>0.75 and abs(s.ty-s.yv/6)>850 and s.pyv<-140)
        or (s.pyv>1120 and s.ty-s.yv/4>3000 and s.pB<16)
        or (2000>s.pyv>970 and s.ty-s.pyv/4>1650 and s.pB<6) )) :
            s.dodge = 1
            s.djL = 's.tL'

    # jump for wavedash
    if (s.d>550 and 950<(s.ty-s.yv/2) and ang_dif(s.a,s.pva,1)<.02
        and abs(s.i)<0.1 and s.pL[2]<50 and s.poG and s.pB<40 and 
        1050<s.pvd<2200 and s.gtime>.1 and s.wavedash ):
        s.jump = 1

    # forward wavedash
    if (s.jcount>0 and s.pL[2]+s.pV[2]/20<32 and abs(s.r)<0.1 and 
        abs(s.a)<0.04 and s.y>400 and 0<abs(s.pR[0]/U)<0.12 and 
        not s.poG and s.pV[2]<-210 and s.wavedash ) :
        s.jump = 1
        s.pitch = -1    
        s.yaw = s.roll = 0

    if s.shoot:
        dodge_hit(s)

    # handling long jumps
    if s.jumper and s.jcount > 0:

        if s.poG or s.ljump and not s.poG:
            s.jump = 1

        if s.jump and s.ljump != s.lljump or not s.ljump:
            s.pitch = s.yaw = s.roll = 0

        if min(0.18, s.dT + 0.05) < s.airtime and s.fz > 100:
            s.jump = not s.ljump

    # handling pre-dodge
    if s.dodge and s.jcount > 0:

        s.jump = s.poG or s.z > 0

        if 0.08 < s.airtime and s.pL[2] > 45:
            exec("s.dja = dodge_ang(s, " + s.djL + ")")
            s.jump = not s.ljump
            s.pitch = abs(s.dja) * 2 - 1
            s.yaw = (abs(Range180(s.dja + .5, 1) * 2) - 1) * .9
            s.roll = 0
            s.djT = s.time

    # handling post-dodge
    if 0.05 < s.djtime < 0.25 or 0.25 < s.djtime < 0.65 and abs(s.a) > 0.5:
        s.pitch = s.yaw = s.roll = 0

    if s.poG and s.lljump != s.ljump:
        s.jump = s.ljump


def dodge_hit(s):
    d2pv = d2(s.tL - s.pL - s.pV * (s.dT + .1))
    # dodge hit
    if (d2pv < 99 and abs(s.tL[2] - s.pL[2]) < 110 and s.bd < 1299):
        # dodge to shoot
        if (s.offense and (abs(s.glinex) < 650 or Range180(s.gta - s.gpa, 1) < .01)
        # dodge to clear
         or ((not s.offense or abs(s.a) > .8) and abs(s.oglinex) > 1400)
        # dodge for 
         or s.kickoff):
            s.dodge = 1
            s.djL = 's.bL + s.bV/60'


def dodge_ang(s, tL):
    L = tL - s.pL
    yaw = Range180(s.pR[1] - U / 2, U) * pi / U
    x, y = rotate2D(L[0], L[1], -yaw)
    a = math.atan2(y, x)
    return Range180(a / pi - .5, 1)


def to_jump(s):
    """Conditions to jump"""

    s.fx, s.fy, s.fz = local(s.tL, s.pfL, s.pR)
    s.fd2 = d2([s.fx, s.fy])

    s.jumpd = min(s.dT * 300, s.jcount * 220)
    s.boostd = 0.5 * 1058 * min(s.dT, s.pB / 33) ** 2
    s.zspeed = s.z / (s.dT + 1e-4)

    if (s.offense and (abs(s.glinex) < 650 or Range180(s.gta - s.gpa, 1) < .01) or
        ((not s.offense or abs(s.a) > .8) and (abs(s.oglinex) > 999 or s.glinez > 1200)) or
            s.kickoff):

        if s.fd2 < 150 and 70 < s.fz < s.jumpd + max(s.boostd - s.jumpd, 0) and s.jcount > 0:
            if 140 < s.zspeed < 400 + max(s.boostd - 300, 0) / (s.dT + 1e-2):
                return 1

    if (s.z > 140 and s.tojump and ((s.z < s.jcount * 250 + s.pB * 10 and s.d2pv < 100 and s.vd2 < 150))):
            s.jumper = 1

    return 0
