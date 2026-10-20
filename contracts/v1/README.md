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
The first native component is an opt-in C++ constant-acceleration executable
at `native/cpp/constant_acceleration.cpp`. Its tests compile it and compare
its exact result object with every constant-acceleration vector here. The
component implements only that result sub-artifact; it does not yet emit the
complete `StudentResponse`, verification report, or runtime trace. An explicit
Python adapter can invoke it; the adapter cross-checks every result against the
canonical Python solver, then retains Python verification and trace behavior.
It remains opt-in rather than the default backend.

The current implementation requires a C++17 compiler that provides the
`__int128` integer extension (such as GCC or Clang), and bounds each input
numerator to +/-100000 and each positive denominator to 1000. Inputs outside
that native capability profile are rejected; this profile is not yet a
general-purpose replacement for Python's rational-number handling.

Any future component must pass all applicable shared vectors and add equivalent
tests for transport, resource limits, and failure behavior before being enabled.
