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
test inputs, not a claim that native C, C++, or C#/.NET implementations exist.
Any future implementation must pass the same vectors and add equivalent tests
for transport, resource limits, and failure behavior before being enabled.
