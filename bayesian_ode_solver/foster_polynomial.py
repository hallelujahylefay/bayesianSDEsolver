import math

import jax
import jax.numpy as jnp


def get_approx():
    def parabolas(key, dt):
        eps_0, eps_1 = jax.random.normal(key, shape=(2,))

        eps_0 *= jnp.sqrt(dt)
        eps_1 *= jnp.sqrt(0.5 * dt)

        return eps_0, eps_1

    def eval_parabola(t, dt, a, b):
        u = t / dt
        return a * u + b * math.sqrt(6) * u * (u - 1)

    return parabolas, eval_parabola