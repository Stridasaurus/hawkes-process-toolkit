# E2 — Theory grounding: exp-kernel Hawkes derivations

Parameterization fixed by ROADMAP.md's glossary: `φ(t) = α e^(-βt)`, branching ratio
`n = α/β`, stationarity requires `n < 1` i.e. `α < β`.

## 1. Conditional intensity and the Markov recursion

The univariate Hawkes conditional intensity given history `H_t = {t_i : t_i < t}` is

```
λ(t) = μ + Σ_{t_i < t} α e^(-β(t - t_i))
```

Because the kernel is exponential, the sum is Markov: define, for the sequence of
event times `t_1 < t_2 < ... < t_n`,

```
R_i = Σ_{j < i} e^(-β(t_i - t_j))          (i.e. the "excitation state" just before event i)
```

Then `λ(t_i) = μ + α R_i`, and `R_i` obeys the recursion

```
R_1 = 0
R_i = e^(-β Δt_i) (1 + R_{i-1}),   Δt_i = t_i - t_{i-1}
```

This turns an O(n²) sum into O(n) — every likelihood/simulation/rescaling routine
below uses this recursion instead of re-summing history.

Between events, for `t in (t_i, t_{i+1}]`:

```
λ(t) = μ + α (1 + R_i) e^(-β(t - t_i))
```

which is a decreasing function of `t` on that interval (since `α, β > 0`) — this
monotonicity is exactly what makes `λ(t_i^+)` a valid upper bound for Ogata thinning
on each inter-event gap.

## 2. Log-likelihood

For a point process on `[0, T]` with (predictable) intensity `λ(t)`, the log-likelihood is

```
log L = Σ_i log λ(t_i) - Λ(T),      Λ(T) = ∫_0^T λ(t) dt
```

`Λ(T)` (the "compensator") splits into the background term and one integral per
past event:

```
Λ(T) = μT + Σ_i ∫_{t_i}^{T} α e^(-β(t - t_i)) dt
     = μT + Σ_i (α/β) (1 - e^(-β(T - t_i)))
```

The boundary term `(1 - e^(-β(T - t_i)))` is the piece most often dropped (it's
easy to write `Λ(T) = μT + (α/β) n_events` by forgetting events near `T` haven't
finished decaying) — it must stay in.

So the full objective (using `R_i` from §1):

```
log L(μ, α, β) = Σ_i log(μ + α R_i) - μT - (α/β) Σ_i (1 - e^(-β(T - t_i)))
```

Constraints for the optimizer: `μ > 0`, `α > 0`, `β > 0` (stationarity `α < β` is
checked post-fit, not imposed as a hard constraint, since an unconstrained fit
landing outside it is itself diagnostic).

## 3. Ogata's modified thinning algorithm (exact simulation)

Exploits §1's monotonicity: intensity only jumps *up* (at a new event, by `α`) and
decays monotonically in between, so the intensity value at the start of a gap is a
valid rejection-sampling majorant for that whole gap.

```
t <- 0, R <- 0 (excitation state), history <- []
while t < T_max:
    λ_bar <- μ + α R                      # current intensity = upper bound for the gap
    u ~ Exp(λ_bar);  t' <- t + u
    if t' > T_max: break
    λ(t') <- μ + α R e^(-β(t' - t))        # decayed intensity at the candidate time
    D ~ Uniform(0, 1)
    if D <= λ(t') / λ_bar:
        accept t' as an event; append to history
        R <- R e^(-β(t' - t)) + 1          # jump: fold in decay since last event, add 1 for the new event
    else:
        R <- R e^(-β(t' - t))              # rejected: still advance the decay, no jump
    t <- t'
```

This is exact (not approximate thinning), and its per-step cost is O(1) thanks to
the recursion, so simulating ~10⁴ events is cheap.

## 4. Time-rescaling theorem (residual analysis / GOF)

If `λ(t)` is the *true* intensity, then `τ_i = Λ(t_i) = ∫_0^{t_i} λ(s) ds` is a
unit-rate Poisson process, i.e. `τ_i - τ_{i-1} ~ iid Exp(1)`. Using §2's compensator
formula per-event:

```
τ_i = μ t_i + (α/β) Σ_{j <= i} (1 - e^(-β(t_i - t_j)))
```

(computed via the same `R`-recursion, O(n)). Fit residuals `u_i = τ_i - τ_{i-1}`
are tested against `Exp(1)` via a one-sample KS test — equivalently `1 - e^(-u_i)`
against `Uniform(0,1)`. This is the GOF check used identically in E2 (self-test),
E3 (real substrate), and E4 (transfer) — one routine, reused, never substrate-specific.
