import jax
import jax.numpy as jnp

from bayesian_sde_solver.ode_solvers.probnum import IOUP_transition_function
from bayesian_sde_solver.ode_solvers.probnum import ekf


def _solver(init, drift, diffusion, delta, h, N, sqrt=True, EKF0=False):
    """
    EKF{0, 1} implementation for the Parabola ODE method with
    the Brownian increment and the Levy's area as part of the observations.
    IOUBM prior.
    One derivative of the vector field is used.
    No observation noise.
    """
    ts = jnp.linspace(h, N * h, N)
    dim = int(init[0].shape[0] / 4)
    noise = jnp.zeros((dim, dim))

    def pol(t):
        H = jnp.array([[1, 0, 0, 0],
                       [0, 0, 0, 0],
                       [0, 0, 1 / delta, 0],
                       [0, 0, 0, jnp.sqrt(6) * (2 * t / delta - 1)]])
        H = jnp.kron(jnp.eye(dim), H)
        return H

    H23 = jnp.kron(jnp.eye(dim), jnp.array([[0, 0, 1, 1]]))

    def extended_vector_field(x, t):
        return drift(x[::4], t) + diffusion(x[::4], t) @ H23 @ pol(t) @ x

    if EKF0:
        def observation_function(x, t):
            # IVP observation function
            return x[1::4] - jax.lax.stop_gradient(extended_vector_field(x, t))
    else:
        def observation_function(x, t):
            # IVP observation function
            return x[1::4] - extended_vector_field(x, t)

    (
        _,
        one_block_transition_covariance,
        one_block_transition_matrix
    ) = IOUP_transition_function(theta=0.0, sigma=1.0, q=1, dt=h, dim=1)

    if sqrt:
        one_block_transition_covariance = jnp.linalg.cholesky(one_block_transition_covariance)

    one_block_transition_matrix = jnp.block(
        [[one_block_transition_matrix, jnp.zeros((2, 2))],
         [jnp.zeros((2, 2)), jnp.eye(2)]]
    )
    one_block_transition_covariance = jnp.block(
        [[one_block_transition_covariance, jnp.zeros((2, 2))],
         [jnp.zeros((2, 2)), jnp.zeros((2, 2))]]
    )

    transition_matrix = jnp.kron(jnp.eye(dim), one_block_transition_matrix)
    transition_covariance = jnp.kron(jnp.eye(dim), one_block_transition_covariance)



    filtered = ekf(init=init, observation_function=observation_function, A=transition_matrix,
                   Q_or_cholQ=transition_covariance, R_or_cholR=noise, params=(ts,), sqrt=sqrt)

    return filtered
