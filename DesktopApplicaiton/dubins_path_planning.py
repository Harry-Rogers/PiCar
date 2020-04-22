"""

Dubins path planner sample code

author Atsushi Sakai(@Atsushi_twi)

modified by Harry Rogers (15623886@students.lincoln.ac.uk)

"""
import math
import numpy as np

import matplotlib.pyplot as plt

def mod2pi(theta):
    return theta - 2.0 * math.pi * math.floor(theta / 2.0 / math.pi)


def pi_2_pi(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi


def LSL(alpha, beta, d):
    sa = math.sin(alpha)
    sb = math.sin(beta)
    ca = math.cos(alpha)
    cb = math.cos(beta)
    c_ab = math.cos(alpha - beta)

    tmp0 = d + sa - sb

    mode = ["L", "S", "L"]
    p_squared = 2 + (d * d) - (2 * c_ab) + (2 * d * (sa - sb))
    if p_squared < 0:
        return None, None, None, mode
    tmp1 = math.atan2((cb - ca), tmp0)
    t = mod2pi(-alpha + tmp1)
    p = math.sqrt(p_squared)
    q = mod2pi(beta - tmp1)
    #  print(np.rad2deg(t), p, np.rad2deg(q))

    return t, p, q, mode


def RSR(alpha, beta, d):
    sa = math.sin(alpha)
    sb = math.sin(beta)
    ca = math.cos(alpha)
    cb = math.cos(beta)
    c_ab = math.cos(alpha - beta)

    tmp0 = d - sa + sb
    mode = ["R", "S", "R"]
    p_squared = 2 + (d * d) - (2 * c_ab) + (2 * d * (sb - sa))
    if p_squared < 0:
        return None, None, None, mode
    tmp1 = math.atan2((ca - cb), tmp0)
    t = mod2pi(alpha - tmp1)
    p = math.sqrt(p_squared)
    q = mod2pi(-beta + tmp1)

    return t, p, q, mode


def LSR(alpha, beta, d):
    sa = math.sin(alpha)
    sb = math.sin(beta)
    ca = math.cos(alpha)
    cb = math.cos(beta)
    c_ab = math.cos(alpha - beta)

    p_squared = -2 + (d * d) + (2 * c_ab) + (2 * d * (sa + sb))
    mode = ["L", "S", "R"]
    if p_squared < 0:
        return None, None, None, mode
    p = math.sqrt(p_squared)
    tmp2 = math.atan2((-ca - cb), (d + sa + sb)) - math.atan2(-2.0, p)
    t = mod2pi(-alpha + tmp2)
    q = mod2pi(-mod2pi(beta) + tmp2)

    return t, p, q, mode


def RSL(alpha, beta, d):
    sa = math.sin(alpha)
    sb = math.sin(beta)
    ca = math.cos(alpha)
    cb = math.cos(beta)
    c_ab = math.cos(alpha - beta)

    p_squared = (d * d) - 2 + (2 * c_ab) - (2 * d * (sa + sb))
    mode = ["R", "S", "L"]
    if p_squared < 0:
        return None, None, None, mode
    p = math.sqrt(p_squared)
    tmp2 = math.atan2((ca + cb), (d - sa - sb)) - math.atan2(2.0, p)
    t = mod2pi(alpha - tmp2)
    q = mod2pi(beta - tmp2)

    return t, p, q, mode


def RLR(alpha, beta, d):
    sa = math.sin(alpha)
    sb = math.sin(beta)
    ca = math.cos(alpha)
    cb = math.cos(beta)
    c_ab = math.cos(alpha - beta)

    mode = ["R", "L", "R"]
    tmp_rlr = (6.0 - d * d + 2.0 * c_ab + 2.0 * d * (sa - sb)) / 8.0
    if abs(tmp_rlr) > 1.0:
        return None, None, None, mode

    p = mod2pi(2 * math.pi - math.acos(tmp_rlr))
    t = mod2pi(alpha - math.atan2(ca - cb, d - sa + sb) + mod2pi(p / 2.0))
    q = mod2pi(alpha - beta - t + mod2pi(p))
    return t, p, q, mode


def LRL(alpha, beta, d):
    sa = math.sin(alpha)
    sb = math.sin(beta)
    ca = math.cos(alpha)
    cb = math.cos(beta)
    c_ab = math.cos(alpha - beta)

    mode = ["L", "R", "L"]
    tmp_lrl = (6.0 - d * d + 2.0 * c_ab + 2.0 * d * (- sa + sb)) / 8.0
    if abs(tmp_lrl) > 1:
        return None, None, None, mode
    p = mod2pi(2 * math.pi - math.acos(tmp_lrl))
    t = mod2pi(-alpha - math.atan2(ca - cb, d + sa - sb) + p / 2.0)
    q = mod2pi(mod2pi(beta) - alpha - t + mod2pi(p))

    return t, p, q, mode


def dubins_path_planning_from_origin(ex, ey, eyaw, c, D_ANGLE):
    # normalize
    dx = ex
    dy = ey
    #euclidean norm of x and y
    D = math.hypot(dx, dy)
    d = D * c
    #  print(dx, dy, D, d)

    #return the 
    theta = mod2pi(math.atan2(dy, dx))
    alpha = mod2pi(- theta)
    beta = mod2pi(eyaw - theta)
    #  print(theta, alpha, beta, d)

    planners = [LSL, RSR, LSR, RSL, RLR, LRL]

    bcost = float("inf")
    bt, bp, bq, bmode = None, None, None, None

    for planner in planners:
        t, p, q, mode = planner(alpha, beta, d)
        if t is None:
            continue

        cost = (abs(t) + abs(p) + abs(q))
        if bcost > cost:
            bt, bp, bq, bmode = t, p, q, mode
            bcost = cost

    #print(bmode)
    px, py, pyaw = generate_course([bt, bp, bq], bmode, c, D_ANGLE)

    return px, py, pyaw, bmode, bcost


def dubins_path_planning(sx, sy, syaw, ex, ey, eyaw, c, D_ANGLE=np.deg2rad(45.0)):
    """
    Dubins path plannner

    input:
        sx x position of start point [m]
        sy y position of start point [m]
        syaw yaw angle of start point [rad]
        ex x position of end point [m]
        ey y position of end point [m]
        eyaw yaw angle of end point [rad]
        c curvature [1/m]

    output:
        px
        py
        pyaw
        mode

    """
    ex = ex - sx #end point of x minus start point of x
    ey = ey - sy #end point of y minus start point of y

    #cosine(start angle) * distance between x's sine(start angle) * distance between y's
    lex = math.cos(syaw) * ex + math.sin(syaw) * ey #
    #sine(start angle) * distance between x's + cosine(start angle) *distance between y's
    ley = - math.sin(syaw) * ex + math.cos(syaw) * ey
    #End angle - start angle
    leyaw = eyaw - syaw

    lpx, lpy, lpyaw, mode, clen = dubins_path_planning_from_origin(
        lex, ley, leyaw, c, D_ANGLE)

    px = [math.cos(-syaw) * x + math.sin(-syaw)
          * y + sx for x, y in zip(lpx, lpy)]
    py = [- math.sin(-syaw) * x + math.cos(-syaw)
          * y + sy for x, y in zip(lpx, lpy)]
    pyaw = [pi_2_pi(iyaw + syaw) for iyaw in lpyaw]
    
  
    
   
        
   
    speed(px, py, mode)
    return px, py, pyaw, mode, clen


def generate_course(length, mode, c, D_ANGLE):

    px = [0.0]
    py = [0.0]
    pyaw = [0.0]

    for m, l in zip(mode, length):
        pd = 0.0
        if m == "S":
            d = 1.0 * c
        else:  # turning couse
            d = D_ANGLE

        while pd < abs(l - d):
            #  print(pd, l)
            px.append(px[-1] + d / c * math.cos(pyaw[-1]))
            py.append(py[-1] + d / c * math.sin(pyaw[-1]))

            if m == "L":  # left turn
                pyaw.append(pyaw[-1] + d)
            elif m == "S":  # Straight
                pyaw.append(pyaw[-1])
            elif m == "R":  # right turn
                pyaw.append(pyaw[-1] - d)
            pd += d

        d = l - pd
        px.append(px[-1] + d / c * math.cos(pyaw[-1]))
        py.append(py[-1] + d / c * math.sin(pyaw[-1]))

        if m == "L":  # left turn
            pyaw.append(pyaw[-1] + d)
            print("HER")
        elif m == "S":  # Straight
            pyaw.append(pyaw[-1])
            print("HHH")
        elif m == "R":  # right turn
            pyaw.append(pyaw[-1] - d)
            print("JJJ")
        pd += d

    return px, py, pyaw
        

def speed(px, py, mode):
    x_diff = np.diff(px)
   
    length = len(x_diff)
    inrange = []
    for i in range(length):
        if i < length-1:
            #print(x_diff[i])
            if ((x_diff[i] >= (x_diff[i+1] - 0.005)) and (x_diff[i] <= (x_diff[i+1] + 0.005))):
                #Make an array of 0's and 1 if 0 turning if 1 go faster at this point
                inrange.append(1)
                if inrange[i]==1:
                    inrange.append(i+i)
            else:
                inrange.append(0)
    return inrange
                

    
def main():
    print("Calculating route")

    
    start_x = 0.0 
    start_y = 0 
    start_yaw = np.deg2rad(45.0)  

    end_x =  -6.8
    end_y =  0
    end_yaw = np.deg2rad(45.0)  

    curvature = 1.0

    px, py, pyaw, mode, clen = dubins_path_planning(start_x, start_y, start_yaw, end_x, end_y, end_yaw, curvature)
    inrange = speed(px,py,mode)
    print(mode)
    
    plt.plot(px, py, 'k', linewidth = 5, color = 'black')
    
    return(mode,px,py,inrange)
    

 
  


if __name__ == '__main__':
    main()
