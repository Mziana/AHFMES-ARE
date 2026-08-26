# AHFMES ARE-0 — R9 Correction Package V6

Status: **NORMATIVE R9 CORRECTION COMPANION / HISTORICAL WAVE-8 BASE / SUPERSEDED ONLY BY A LATER MANIFEST-LISTED COMPANION / NO IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-21**

## 1. Scope

This file records the R9 correction semantics that were qualified for the historical candidate `6bf6b2ab...`. It remains normative only while included by the current manifest and only to the extent not narrowed/replaced by a later manifest-listed correction companion.

It cannot add machine rights absent from the sole current Matrix.

## 2. External audit status of the historical candidate

The historical candidate `6bf6b2ab8e83983da7e4291f20624c0e026438e8` received substantive external audit results with one reproducible blocker:

```text
EXT2-C01 = BOOTSTRAP_EPOCH_IDENTITY_IS_PAYLOAD_DERIVED
normalization = R9-01
```

Therefore this V6 package is not evidence that ARE-0 is closed.

## 3. Preserved R9 root taxonomy

```text
R9 CLOSURE ROOTS = 7
FORMAL / ARCHITECTURAL = R9-01,R9-02,R9-04,R9-05,R9-06,R9-07
CLOSURE-PROTOCOL = R9-03
NEW R9 ROOT FAMILY = NONE ESTABLISHED
```

## 4. Preserved correction semantics

All R9-02/R9-04/R9-05/R9-06/R9-07 semantics previously defined by the current Matrix composition remain required unless explicitly narrowed by a later Matrix generation.

R9-01 bootstrap semantics require a later narrowing because the historical `BOOTSTRAP_EPOCH_KEY` included payload/policy roots and therefore was not a stable identity for one semantic bootstrap instance.

## 5. Successor correction requirement

A later correction companion must bind at minimum:

```text
BOOTSTRAP_INSTANCE_KEY
= payload-independent semantic system/bootstrap identity

BOOTSTRAP_PAYLOAD_COMMITMENT_ROOT
= payload/policy content committed under that instance

same instance + same payload
= idempotent continuation

same instance + conflicting payload
= INVALID / no alternate authority slot

late discovery before genesis
= governed same-instance monotone reconciliation only

SystemGenesis #0
= atomically commits current same-instance import lineage
  + permanently consumes the bootstrap instance
```

The current regression suite must add a permanent alternate-payload bootstrap attack equivalent to R9-X82.

## 6. Closure-evidence companion requirement

The Quarantine Policy V1 remains normative. Its successor non-normative evidence must enumerate every detected authority-like historical self-claim with exact path/blob/location-or-bounded-quote/classification; mass set-difference classification alone is insufficient evidence of per-claim inspection.

## 7. Static firewall

```text
ARE-0 CLOSED = NO
IMPLEMENTATION = NOT AUTHORIZED
P001 = NOT AUTHORIZED
PRODUCTION = CLOSED
PR #20 MERGE = NOT AUTHORIZED
```
