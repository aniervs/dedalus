"""
Dedalus script solving the 2D Poisson equation with mixed boundary conditions.
This script demonstrates solving a 2D cartesian linear boundary value problem.
and produces a plot of the solution. It should be ran serially and take just a
few seconds to complete.

We use a Fourier(x) * Chebyshev(y) discretization to solve the LBVP:
    dx(dx(u)) + dy(dy(u)) = f
    u(y=0) = g
    dy(u)(y=Ly) = h

For a scalar Laplacian on a finite interval, we need two tau terms. Here we
choose to lift them to the natural output (second derivative) basis.
"""

import numpy as np
import matplotlib.pyplot as plt
import dedalus.public as d3
import logging
logger = logging.getLogger(__name__)

# TODO: make proper plotting using plotbot/xarray
# TODO: indexing on coord systems by name or axis


# Parameters
Nx = 256
Ny = 128
Lx = 2 * np.pi
Ly = 1
dtype = np.float64

# Bases
coords = d3.CartesianCoordinates('x', 'y')
dist = d3.Distributor(coords, dtype=dtype)
xbasis = d3.RealFourier(coords.coords[0], size=Nx, bounds=(0, Lx))
ybasis = d3.Chebyshev(coords.coords[1], size=Ny, bounds=(0, Ly))

# Fields
u = dist.Field(name='u', bases=(xbasis, ybasis))
tau1 = dist.Field(name='tau1', bases=xbasis)
tau2 = dist.Field(name='tau2', bases=xbasis)

# Forcing
x = xbasis.local_grid()
y = ybasis.local_grid()
f = dist.Field(bases=(xbasis, ybasis))
g = dist.Field(bases=xbasis)
h = dist.Field(bases=xbasis)
f['g'] = -10 * np.sin(x/2)**2 * (y - y**2)
g['g'] = np.sin(8*x)
h['g'] = 0

# Substitutions
dy = lambda A: d3.Differentiate(A, coords.coords[1])
lap = lambda A: d3.Laplacian(A, coords)
lift_basis = ybasis.clone_with(a=3/2, b=3/2) # Natural output basis
lift = lambda A, n: d3.LiftTau(A, lift_basis, n)

# Problem
problem = d3.LBVP(variables=[u, tau1, tau2])
problem.add_equation((lap(u) + lift(tau1,-1) + lift(tau2,-2), f))
problem.add_equation((u(y=0), g))
problem.add_equation((dy(u)(y=Ly), h))

# Solver
solver = problem.build_solver()
solver.solve()

# Plot
ug = u.allgather_data('g')
if dist.comm.rank == 0:
    plt.figure(figsize=(6, 4))
    plt.imshow(ug.T)
    plt.colorbar(label='u')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.tight_layout()
    plt.savefig('poisson.png')
