from typing import Sequence
import numpy as np
from numpy import sin, cos
from .common import Const

def double_cart_pendulum(t, x, x_dot, *,
                         M: float, m1: float, m2: float, L1: float, L2: float, u: float = 0.0) -> np.ndarray:
    '''
    Double cart-pendulum expressions obtained from Euler-Lagrange equations. No drag is considered.
    The equations are the same presented in https://www.do-mpc.com/en/latest/example_gallery/DIP.html,
    substituting theta1 and theta2 by pi - theta1 and pi - theta2, respectively.

    Parameters
    ----------
    t : float
        Time.
    x : Sequence[float]
        State variables [x, theta1, theta2, dx, omega1, omega2]. ThetaN = pi corresponds to the pendulum pointing up.
    x_dot : Sequence[float]
        Derivatives of the state variables [dx, omega1, omega2, ddx, alpha1, alpha2].
    M : float
        Mass of the cart.
    m1 : float
        Mass of the first pendulum.
    m2 : float
        Mass of the second pendulum.
    L1 : float
        Length of the first pendulum.
    L2 : float
        Length of the second pendulum.
    u : float, optional
        Force applied to the cart. Default is 0.0.
    '''
    x, theta1, theta2, dx, omega1, omega2 = x
    x_dot, theta1_dot, theta2_dot, ddx, alpha1, alpha2 = x_dot

    g = Const.GRAVITY
    l1 = L1/2 # Half of the length of the first pendulum
    l2 = L2/2 # Half of the length of the second pendulum
    J1 = (m1 * l1**2) / 3 # Inertia of the first pendulum
    J2 = (m2 * l2**2) / 3 # Inertia of the second pendulum

    # Some parameters to keep the equations clean
    p1 = M + m1 + m2
    p2 = m1*l1 + m2*L1
    p3 = m2*l2
    p4 = m1*l1**2 + m2*L1**2 + J1
    p5 = m2*l2*L1
    p6 = m2*l2**2 + J2
    p7 = (m1*l1 + m2*L1) * g
    p8 = m2*l2*g

    
    g = np.zeros(6)
    # ODEs ... Relation between the state variables and their derivatives
    g[0] = dx - x_dot
    g[1] = omega1 - theta1_dot
    g[2] = omega2 - theta2_dot
    # Euler-Lagrange equations ... All terms in one side of the equations (0 = g(x, z))
    g[3] =  p1*ddx + p2*alpha1*cos(theta1) + p3*alpha2*cos(theta2) - (
        p2*omega1**2*sin(theta1) + p3*omega2**2*sin(theta2) + u)
    g[4] = -p2*cos(theta1)*ddx - p4*alpha1 - p5*alpha2*cos(theta1 - theta2) - (
        p7*sin(theta1) + p5*omega2**2*sin(theta1 - theta2))
    g[5] = -p3*cos(theta2)*ddx - p5*alpha1*cos(theta1 - theta2) - p6*alpha2 - (
        -p5*omega1**2*sin(theta1 - theta2) + p8*sin(theta2))
    
    return g


def quadrotor(t, states, states_dot, *,
              Ixx: float, Iyy: float, Izz: float,
              k: float, L: float, m: float, drag: float,
              u: Sequence[float] = [0.0, 0.0, 0.0, 0.0]) -> np.ndarray:
    '''
    Quadrotor expressions obtained from Euler-Lagrange formalism.
    The code is based in the following references:
    - https://doi.org/10.1016/j.automatica.2009.10.018
    - https://es.mathworks.com/help/symbolic/derive-quadrotor-dynamics-for-nonlinearMPC.html

    Parameters
    ----------
    t : float
        Time.
    states : Sequence[float]
        State variables [x, y, z, phi, theta, psi, dx, dy, dz, dphi, dtheta, dpsi].
    states_dot : Sequence[float]
        Derivatives of the state variables [x_dot, y_dot, z_dot, phi_dot, theta_dot, psi_dot, dx_dot, dy_dot, dz_dot, dphi_dot, dtheta_dot, dpsi_dot].
    Ixx : float
        Moment of inertia around the x-axis (in the body frame).
    Iyy : float
        Moment of inertia around the y-axis (in the body frame).
    Izz : float
        Moment of inertia around the z-axis (in the body frame).
    k : float
        Thrust factor of the propellers.
    L : float
        Distance from the center of mass to the propellers.
    m : float
        Mass of the quadrotor.
    drag : float
        Drag factor of the quadrotor.
    u : Sequence[float], optional
        Squared angular velocities of the propellers [w1^2, w2^2, w3^2, w4^2]. Default is [0.0, 0.0, 0.0, 0.0].
    '''
    
    # Position of the center of mass relative to the inertial frame
    x, y, z = states[:3]
    # Euler angles (roll, pitch, yaw) relative to the inertial frame
    phi, theta, psi = states[3:6]
    # Linear velocities of the center of mass relative to the inertial frame
    dx, dy, dz = states[6:9]
    # Angular velocities relative to the inertial frame
    dphi, dtheta, dpsi = states[9:12]
    # Derivatives
    x_dot, y_dot, z_dot, phi_dot, theta_dot, psi_dot, dx_dot, dy_dot, dz_dot, dphi_dot, dtheta_dot, dpsi_dot = states_dot

    # Torques and thrust
    tau_phi, tau_theta, tau_psi, F = (
        L*k*(-u[1] + u[3]),
        L*k*(-u[0] + u[2]),
        drag*(-u[0] + u[1] - u[2] + u[3]),
        k*np.sum(u)
    )

    # Rotation matrix (relates linear velocities in the body frame to the inertial frame)
    R = np.array([[cos(psi)*cos(theta), cos(psi)*sin(theta)*sin(phi) - sin(psi)*cos(phi), cos(psi)*sin(theta)*cos(phi) + sin(psi)*sin(phi)],
                  [sin(psi)*cos(theta), sin(psi)*sin(theta)*sin(phi) + cos(psi)*cos(phi), sin(psi)*sin(theta)*cos(phi) - cos(psi)*sin(phi)],
                  [        -sin(theta),                              cos(theta)*sin(phi),                              cos(theta)*cos(phi)]])
    # Rotation matrix (relates angular velocities in the body frame to the inertial frame)
    W = np.array([[1,         0,         -sin(theta)], # type: ignore
                  [0,  cos(phi), cos(theta)*sin(phi)],
                  [0, -sin(phi), cos(theta)*cos(phi)]])
    # Moment of inertia matrix realted to the body frame
    J = np.array([[Ixx, 0, 0], # type: ignore
                  [0, Iyy, 0],
                  [0, 0, Izz]])
    # Moment of inertia matrix realted to the inertial frame
    M = W.T @ J @ W
    # Coriolis matrix
    c11 = 0
    c12 = (Iyy - Izz)*(theta_dot*cos(phi)*sin(phi) + psi_dot*sin(phi)**2*cos(theta)) + (Izz - Iyy)*psi_dot*cos(phi)**2*cos(theta) - Ixx*psi_dot*cos(theta)
    c13 = (Izz - Iyy)*psi_dot*cos(phi)*sin(phi)*cos(theta)**2
    c21 = -c12
    c22 = (Izz - Iyy)*phi_dot*cos(phi)*sin(phi)
    c23 = -Ixx*psi_dot*sin(theta)*cos(theta) + Iyy*psi_dot*sin(phi)**2*cos(theta)*sin(theta) + Izz*psi_dot*cos(phi)**2*cos(theta)*sin(theta)
    c31 = -c13 - Ixx*theta_dot*cos(theta)
    c32 = (Izz - Iyy)*(theta_dot*cos(phi)*sin(phi)*sin(theta) + phi_dot*sin(phi)**2*cos(theta)) + (Iyy - Izz)*psi_dot*cos(phi)**2*cos(theta) - c23
    c33 = (Iyy - Izz)*phi_dot*cos(phi)*sin(phi)*cos(theta)**2 - (
        Iyy*theta_dot*sin(phi)**2*cos(theta)*sin(theta) + Izz*theta_dot*cos(phi)**2*cos(theta)*sin(theta) - Ixx*theta_dot*sin(theta)*cos(theta)
    )
    C = np.array([[c11, c12, c13], # type: ignore
                  [c21, c22, c23],
                  [c31, c32, c33]])
    
    g = np.zeros(12)
    # ODEs ... Relation between the state variables and their derivatives
    g[0] = dx - x_dot
    g[1] = dy - y_dot
    g[2] = dz - z_dot
    g[3] = dphi - phi_dot
    g[4] = dtheta - theta_dot
    g[5] = dpsi - psi_dot
    # Euler-Lagrange equations ... All terms in one side of the equations (0 = g(x, z))
    # ddx, ddy, ddz
    g[6:9] = np.array([0, 0, -Const.GRAVITY]) + R @ np.array([0, 0, F/m]) - np.array([dx_dot, dy_dot, dz_dot])
    # ddphi, ddtheta, ddpsi
    g[9:12] = np.linalg.inv(M) @ (np.array([tau_phi, tau_theta, tau_psi]) - C @ np.array([dphi, dtheta, dpsi])) - np.array([dphi_dot, dtheta_dot, dpsi_dot])
    
    return g