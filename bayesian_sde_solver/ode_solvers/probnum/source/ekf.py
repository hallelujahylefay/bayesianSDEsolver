import jax
import jax.numpy as jnp
import jax.scipy.linalg as jlinalg


def tria(A):
    q, r = jlinalg.qr(A.T)
    return r.T


def predict(m, P, A, Q, sqrt=False):
    if sqrt:
        P = tria(jnp.concatenate([A @ P, Q], axis=1))
        return A @ m, P

    return A @ m, A @ P @ A.T + Q


def update(m, P, y, H, R, sqrt=False):
    if sqrt:
        dim = m.shape[0]
        y_diff = y - H @ m
        M = jnp.block([[H @ P, R],
                          [P, jnp.zeros_like(P, shape=(dim, dim))]])
        chol_S = tria(M)
        cholP = chol_S[dim:, dim:]
        G = chol_S[dim:, :dim]
        I = chol_S[:dim, :dim]
        m = m + G @ jlinalg.solve_triangular(I, y_diff, lower=True)
        return m, cholP

    S = H @ P @ H.T + R
    S_invH = jlinalg.solve(S, H, sym_pos=True)
    K = (S_invH @ P).T
    b = m + K @ (y - H @ m)
    C = P - K @ S @ K.T
    return b, C


def ekf(init, observation_function, A, Q, R, params=None):
    def body(x, param):
        m, P = x
        if param is None:
            H = jax.jacfwd(observation_function, 0)(m)
        else:
            H = jax.jacfwd(observation_function, 0)(m, *param)
        predm, predP = predict(m, P, A, Q)
        m, P = update(predm, predP, m, H, R)
        return (m, P), (m, P)

    _, traj = jax.lax.scan(body, init, params)
    return traj