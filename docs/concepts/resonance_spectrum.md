# Resonance Spectrum

## 1. From pair relation to spectrum

Approximate resonance answers a pair question:

`Does part resonate in whole within defect budget d?`

A spectrum asks a richer question:

> Which candidate parts best explain this whole mode as a recurrence?

## 2. Definition

**DEF-035 — Resonance spectrum.**

Given a whole mode `W`, a candidate set `C`, and defect budget `d`, the resonance spectrum is the ordered list:

`Spec_d(W,C) = sort({ profile(p,W,d) : p ∈ C })`

where `profile` is the bounded-defect phase resonance profile.

## 3. Ranking principle

The first Core-0.9 ranking is intentionally simple:

1. resonating candidates before non-resonating candidates;
2. fewer defects before more defects;
3. exact resonance before bounded-defect resonance;
4. shorter candidate part before longer candidate part;
5. lexical word order only as an external tie-breaker.

This is not final metaphysics. It is a reproducible exploration order.

## 4. Example

Let:

`whole = abac`

Candidate `part = ab` gives:

- expected `abab`,
- actual `abac`,
- one defect at index 3.

So `ab` appears in the spectrum as bounded-defect resonance with defect count 1.

Candidate `part = cc` gives:

- expected `cccc`,
- too many defects,
- over-budget unless the budget is large.

## 5. Interpretation

A resonance spectrum is like a primitive Fourier-like decomposition, but for finite mode rhythms instead of sinusoidal waves.

It reports:

- what rhythms are exact;
- what rhythms are near;
- where defects occur;
- which phase offset makes the rhythm most visible.

## 6. Next research direction

The spectrum can become a bridge to scientific structure:

- signal periodicity detection,
- biological motif discovery,
- crystal defect classification,
- quasi-periodic structures,
- compression and complexity measures.

The next layer should export spectra to tables and compare ranking strategies.
