# SaemPhysics Starter Notes: Constant Acceleration

**Original pilot study pack · Version 1 · prepared for teacher review**

These notes teach one-dimensional motion when acceleration is constant. They
are an original SaemPhysics learning resource, not copied from a textbook or
exam paper. Review the examples and wording before selling or assigning this
pack.

## 1. The model

Choose a positive direction before writing equations. Position is measured
along that direction. Velocity tells you how position changes; acceleration
tells you how velocity changes.

For constant acceleration \(a\), initial velocity \(u\), final velocity \(v\),
time interval \(t\), and displacement \(s\):

\[
v = u + at
\]

The average velocity over the interval is \((u+v)/2\), so:

\[
s = \frac{u+v}{2}t
  = \frac{u+(u+at)}{2}t
  = ut + \frac{1}{2}at^2
\]

Eliminating time gives a third useful relation:

\[
v^2 = u^2 + 2as
\]

Use only the equations that contain the known values and the quantity you
need. The equations assume motion on one straight line, constant acceleration,
and consistent units.

## 2. Sign convention and units

If right/up/forward is positive, a quantity pointing the other way has a
negative sign. “Slowing down” does not always mean acceleration is negative:
the sign depends on the chosen direction and the velocity.

- \(u\), \(v\): metres per second (m/s)
- \(a\): metres per second squared (m/s²)
- \(t\): seconds (s)
- \(s\): metres (m)

Dimensional check for displacement:

\[
[ut] = (\text{m/s})(\text{s}) = \text{m}, \qquad
[at^2] = (\text{m/s}^2)(\text{s}^2) = \text{m}
\]

Both terms in \(s=ut+\tfrac12at^2\) therefore have units of length.

## 3. Worked example: speed and displacement

A trolley starts at \(u=3\text{ m/s}\) and accelerates at
\(a=2\text{ m/s}^2\) for \(t=4\text{ s}\).

Final velocity:

\[
v = 3 + (2)(4) = 11\text{ m/s}
\]

Displacement:

\[
s = (3)(4) + \frac12(2)(4^2)
  = 12 + 16 = 28\text{ m}
\]

Check using average velocity: the velocity rises uniformly from 3 to 11 m/s,
so the average is 7 m/s. In 4 seconds, the displacement is
\((7)(4)=28\text{ m}\), matching the first calculation.

## 4. Worked example: braking

A bicycle moves at \(u=12\text{ m/s}\). Its acceleration is
\(-3\text{ m/s}^2\) while braking. How long does it take to stop, and how far
does it travel?

At rest, \(v=0\):

\[
0 = 12 + (-3)t \quad\Rightarrow\quad t=4\text{ s}
\]

Then:

\[
s = (12)(4) + \frac12(-3)(4^2)
  = 48 - 24 = 24\text{ m}
\]

The negative acceleration reduces the positive velocity. The positive
displacement means the bicycle still moved forward before stopping.

## 5. A reliable problem-solving routine

1. Sketch the motion and choose a positive direction.
2. List known values with units and signs.
3. Identify the requested quantity.
4. Select an equation containing the unknown and known values.
5. Substitute with parentheses around signed values.
6. Check units, sign, and whether the result is physically plausible.
7. If possible, verify using a different relation or the velocity-time graph.

For constant acceleration, the velocity-time graph is a straight line. The
change in velocity is \(at\); the signed area under the graph is displacement.

## 6. Common errors

- **Mixing distance and displacement.** Displacement includes direction and
  can be negative; distance is total path length and is non-negative.
- **Dropping the sign while braking.** Use the chosen direction consistently.
- **Using \(t\) instead of \(t^2\).** The second term is
  \(\tfrac12at^2\).
- **Adding velocities without averaging.** Under constant acceleration,
  average velocity is \((u+v)/2\).
- **Combining incompatible units.** Convert minutes to seconds and km/h to
  m/s before substituting.
- **Assuming every acceleration is constant.** If acceleration changes, this
  model is not sufficient over the whole interval.

## 7. Try these

1. A runner has initial velocity \(2\text{ m/s}\), acceleration
   \(1.5\text{ m/s}^2\), and runs for \(6\text{ s}\). Find final velocity
   and displacement.
2. A ball moving upward at \(20\text{ m/s}\) experiences
   \(a=-10\text{ m/s}^2\). Find the time to its highest point and its
   displacement by then.
3. A cart's velocity changes from \(5\text{ m/s}\) to \(17\text{ m/s}\)
   in \(3\text{ s}\). Find its constant acceleration and displacement.

### Answers with checks

1. \(v=11\text{ m/s}\), \(s=39\text{ m}\). The average velocity is
   \((2+11)/2=6.5\text{ m/s}\); \(6.5\times6=39\text{ m}\).
2. \(t=2\text{ s}\), \(s=20\text{ m}\). The upward velocity reaches zero;
   the displacement is positive in the upward direction.
3. \(a=4\text{ m/s}^2\), \(s=33\text{ m}\). Average velocity is
   \(11\text{ m/s}\), and \(11\times3=33\text{ m}\).

## 8. Limits of this pack

This is a short introductory resource for one-dimensional constant
acceleration. It does not cover variable acceleration, air resistance,
projectile motion in two dimensions, or exam-board-specific requirements.
The SaemPhysics exact solver checks supported calculations, but a human teacher
must review this teaching material and confirm its suitability for a class.
