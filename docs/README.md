# SaemPhysics source library

The uploaded references are kept in subject folders so that the implementation
can be traced to its source material without mixing the library into the
application package. Filenames and original documents are preserved.

See the [phased build roadmap](./ROADMAP.md) for monthly milestones and the
current first step.

The machine-readable catalog is [`data/sources.json`](../data/sources.json).
Validate every catalog entry and its local file with:

```bash
saemphysics validate-sources data/sources.json
```

The 29 uploaded reference documents remain `review_required` for rights and
`catalogued` for ingestion. A separate SaemPhysics-authored synthetic sample
is marked `original`; that does not assert that any external upload is
licensed for redistribution. The catalog does not claim that exam questions
have been extracted.

The five original synthetic mechanics prompts are catalogued separately in
[`data/sources/synthetic_mechanics_pilot.md`](../data/sources/synthetic_mechanics_pilot.md)
and stored as canonical records in [`data/questions/`](../data/questions).
They are test/learning examples, not questions extracted from the uploaded
textbooks or from a real examination. Validate their provenance links with:

```bash
saemphysics validate-corpus data/questions
```

## Core processor knowledge matrix

[`CORE_PROCESSOR_BOOK_MATRIX.csv`](./CORE_PROCESSOR_BOOK_MATRIX.csv) maps all
29 uploaded reference documents to their visible chapters or sections, topics,
concepts, mathematical/computational capabilities, and possible processor
applications. Its chapter coverage is deliberately evidence-labeled:
`outline_verified` means chapter structure was extractable; partial, summary,
and unreadable uploads are identified rather than filled with invented
headings. The processor mappings are engineering hypotheses to test, not claims
that a source itself prescribes C, C++, or C# architecture. Rights remain
`review_required`; the matrix is a concise study index, not a replacement for
the books or permission to redistribute their contents.

## Vision and project design

- [`New Architecture - cos ai.PDF`](./vision/New%20Architecture%20-%20cos%20ai.PDF) — architecture proposal.
- [`SaemPhysics Future Roadmap`](./vision/SaemPhysics_Future_Roadmap_Knowledge_to_Lecture_Engine-1.pdf) — knowledge-to-lecture roadmap.
- [`SaemPhysics AI Animation Studio textbook`](./vision/SaemPhysics_AI_Animation_Studio_Textbook-1.pdf) — animation and teaching workflow.
- [`Constitution-Medina.pdf`](./vision/Constitution-Medina.pdf) — reference document.
- [`Bismillah-ir-Rahman-ir-Raheem.PDF`](./vision/Bismillah-ir-Rahman-ir-Raheem.PDF) — reference document.

## Computing and programming

- [`Feynmann computation.PDF`](./computing/Feynmann%20computation.PDF) and [Feynman's *Lectures on Computation*](./computing/computation-Richard_P._Feynman-Feynman_Lectures_on_Computation__-Addison-Wesley%281996%29.docx).
- [Strang, *Computational Science and Engineering*](./computing/Gilbert%20Strang%20MIT%20Computational%20Science%20and%20Engineering%20%281%29.docx).
- [MIT Python programming](./computing/Python%20programming%20mit.pdf) and [MIT 6.01 systems course](./computing/mit6_01scs11_textbook%20%281%29.pdf).
- [SICP, Book 2](./computing/Book%202%20SICP.PDF) and [`SCIP MIT.docx`](./computing/SCIP%20MIT.docx).
- [Automatic digital composium, Book 1](./computing/Book%201%20Automatic%20digital%20composium.PDF).
- [C star Programming guides](./computing/C%20star%20Programming%20guides.PDF) and [CStarProgrammingGuide](./computing/CStarProgrammingGuide%20%281%29.pdf).
- [C++ Templates: The Complete Guide](./computing/C%2B%2B%20Templates%20-%20The%20Complete%20Guide%20%28Addison%20Wesley-2002%29.pdf).
- [John von Neumann, *The Computer and the Brain*](./computing/John%20von%20Neumann,%20The%20Computer%20%26%20the%20Brain,%20Third%20Edition%20%282012%29;%20the%20file%20contains%20the%20complete%20two-part%20structure-%20Part%201%20.PDF).

## Mathematics

- [Gilbert Strang, MIT 18.001 calculus](./mathematics/mitres_18_001_gilbert%20strang.pdf).
- [Napier, construction of logarithms](./mathematics/Napier%20-%20construction%20of%20logarithm.pdf).

## Physics

- [Feynman Lectures, Volume 1: Mainly Mechanics](./physics/V1-%20The%20Feynman%20Lectures%20on%20Physics,%20Volume%201_%20Mainly%20Mechanics.docx).
- [Feynman Lectures, Volume 2: Electromagnetism and Matter](./physics/V2%20-%20feynman-lectures-on-physics-vol%202%20-electromagnetism-and-matter%20-%20volume%202%20%281%29.docx).
- [Feynman Lectures, Volume 3: Quantum Mechanics](./physics/V3-%20Feynman%20Lectures%20vol%203%20on%20Quantum%20Mechanics%203.docx).
- [Feynman's QED](./physics/QED_%20The%20Strange%20Theory%20of%20Light%20and%20Matter%20by%20Feynman.docx).
- [`Feynman Stastucal mechanics.PDF`](./physics/Feynman%20Stastucal%20mechanics.PDF) and [`Statistical Mechanics_ feynmann.docx`](./physics/Statistical%20Mechanics_%20feynmann.docx).

## Quantum computing

- [`2110.00827v2.pdf`](./quantum/2110.00827v2.pdf) (filename retained as provided).
- [`algorithm for quantum computing.pdf`](./quantum/algorithm%20for%20quantum%20computing.pdf) (image-only upload; no extractable text was available during the initial review).
- [`caltech - quantum state phase computation.pdf`](./quantum/caltech%20-%20quantum%20state%20phase%20computation.pdf).
- [`notes on quantum algorithm.pdf`](./quantum/notes%20on%20quantum%20algorithm.pdf).

## Prototypes

The standalone web prototypes are separate from the reference library:

- [Exam Forecaster](../prototypes/Exam%20Forecaster%201.html)
- [Mock Tester](../prototypes/Mock%20Tester%201.html)

## Using the sources

Use sources to inform original implementation and explanations; do not assume
that an uploaded file is licensed for redistribution or reuse. Keep source,
page, and rights metadata with any question derived from external material.
When a document's contents have not been read or verified, treat its filename
as a catalog entry, not as evidence for technical claims.
