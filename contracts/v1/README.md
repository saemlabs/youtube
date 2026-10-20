# Student request/response contract v1

`conformance.json` is the language-neutral contract fixture set for
`saemphysics.student-request-response` version `1.0.0`. Requests and responses
are JSON objects using the field names, exact numeric strings, and enum values
shown in the vectors.

The current version is an external compatibility label; it does not add a
version field to `StudentRequest` or change the public API. Consumers should
identify the contract version out of band, reject unsupported versions, and
must not silently ignore unknown request fields.

Each valid vector specifies the response status, complete computation
artifact, verification status, and ordered execution trace layers. A consumer
passes a vector only when those values match exactly. Invalid vectors pass
only when request validation rejects them before capability execution; error
wording is intentionally not standardized.

The vectors cover the current exact derivative, constant-acceleration,
definite-integral, and square linear-system capabilities. They are executable
test inputs, not a claim that the full processor has native implementations.
The shared native capabilities are exact constant-acceleration kinematics and
bounded exact square linear-system solves, implemented in C, C++, and C# under
`native/`. Linear-system commands accept dimensions 1 through 3 and exact
rational values with reduced numerator magnitude and denominator at most 1000;
singular systems are rejected. An explicit Python adapter can invoke any
executable and cross-checks every result against its canonical Python solver,
then retains Python verification and trace behavior. Native capabilities
remain opt-in rather than the default backend and do not implement the complete
`StudentResponse`, verification report, or runtime trace.
This slice does not implement the broader calculus, eigenvalue, iterative
method, numerical-PDE, logarithm, or complex-exponential topics in the
referenced books.

The versioned native capability output envelope is specified in
[`native-capability-response.schema.json`](./native-capability-response.schema.json).
It is intentionally narrower than the frontend contract: Python validates the
whole `StudentRequest`, routes intent and corpus workflows, validates this
capability envelope, cross-checks the exact result, performs canonical
verification, and assembles the final response and ordered trace. The current
native command protocol accepts
`--core-v1 solve_constant_acceleration INITIAL_VELOCITY ACCELERATION TIME` or
`--core-v1 solve_linear_system N A-values... b-values...`; other operations
fail explicitly instead of being treated as successful work.

The C and C++ implementations require GCC or Clang-compatible 128-bit integer
extensions; the C++ source requires C++17 and the C source requires C11. The C#
implementation targets .NET 10 and uses `BigInteger`. All three bound each
input numerator to +/-100000 and each positive denominator to 1000. Inputs
outside that capability profile are rejected; this profile is not a
general-purpose replacement for Python's rational-number handling.

Compile the C and C++ capabilities with the commands in
[`docs/INTERFACE.md`](../../docs/INTERFACE.md). Build the C# capability with
`dotnet build native/csharp/SaemPhysics.Kinematics.csproj --configuration Release`.
Any additional component must pass all applicable shared vectors and add
equivalent tests for transport, resource limits, and failure behavior before
being enabled.
