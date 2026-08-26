# AHFMES Autonomous Research Engine V0 — Human Flowcharts

Status: **HUMAN-READABLE ARCHITECTURE MAP / NOT IMPLEMENTATION AUTHORITY**  
Effective date: **2026-08-20**

This file exists so a human reviewer, future assistant, or engineering agent can reconstruct the intended direction without relying on chat history.

## 1. System-level flow: THINK → PROVE → ACT

```mermaid
flowchart TD
    MW[Market World] --> OBS[Observation Bus]
    OBS --> CAP[Capability Library]
    CAP --> WM[Current World Model]

    WM --> OP[Operational Brain]
    OP --> DV[Decision Value]
    DV --> CSK[Capital Safety Kernel]
    CSK --> EXE[Executor]
    EXE --> EXP[Experience Store]

    WM --> EXP
    EXP --> REG[Regret / Decision Memory]
    REG --> PM[Problem Memory]
    PM --> RB[Research Brain]

    RB --> CR[Critic]
    CR --> CAND[Candidate / Hypothesis]
    CAND --> VAL[Scientific Validation]
    VAL --> SH[ Frozen Shadow ]
    SH --> GOV[Deterministic Governor]

    GOV -->|Reject / Invalid| GY[Graveyard / Scientific Memory]
    GOV -->|Promote| CH[Champion]
    CH --> OP

    SC[Scientific Constitution] -. governs .-> RB
    SC -. governs .-> CR
    SC -. governs .-> VAL
    SC -. governs .-> SH
    SC -. governs .-> GOV

    CSK -. protects capital .-> EXE
```

Interpretation:

- Research can think broadly.
- Research cannot jump directly to execution.
- Evidence must pass through proof machinery.
- Capital always remains behind a separate safety boundary.

## 2. Three-world authority separation

```mermaid
flowchart LR
    T[WORLD 1: THINK\nDiscovery / Hypothesis / Capability Search]
    P[WORLD 2: PROVE\nCritic / Validation / Shadow / Governor]
    A[WORLD 3: ACT\nOperational Brain / Safety / Executor]

    T --> P --> A
    T -. PROHIBITED .-> A
```

## 3. Problem lifecycle

```mermaid
stateDiagram-v2
    [*] --> OBSERVED
    OBSERVED --> OPEN
    OPEN --> RESEARCHING

    RESEARCHING --> RESOLVED_BOUNDED
    RESEARCHING --> UNRESOLVED
    RESEARCHING --> CURRENTLY_NON_PREDICTABLE
    RESEARCHING --> INSUFFICIENT_OBSERVABILITY
    RESEARCHING --> INSUFFICIENT_SAMPLE
    RESEARCHING --> NO_STABLE_EDGE

    RESOLVED_BOUNDED --> ARCHIVED
    CURRENTLY_NON_PREDICTABLE --> ARCHIVED
    NO_STABLE_EDGE --> ARCHIVED
```

Important: not every problem must end with a strategy.

## 4. Claim / epistemic lifecycle

```mermaid
stateDiagram-v2
    [*] --> OBSERVED
    OBSERVED --> SUSPECTED
    SUSPECTED --> DISCOVERY_CLUE
    DISCOVERY_CLUE --> VALIDATED
    VALIDATED --> PRODUCTION_ELIGIBLE

    SUSPECTED --> REJECTED
    DISCOVERY_CLUE --> REJECTED
    VALIDATED --> REJECTED

    OBSERVED --> INVALID
    SUSPECTED --> INVALID
    DISCOVERY_CLUE --> INVALID
```

`REJECTED` = valid experiment, hypothesis failed.  
`INVALID` = evidence/contract integrity failed; scientific result cannot be used.

## 5. Research Contract lifecycle

```mermaid
flowchart TD
    P[Problem selected] --> D[Draft Research Contract]
    D --> PRE[Precommit question / population / metric / budget / stopping rule]
    PRE --> LOCK[LOCKED]
    LOCK --> SEARCH[Bounded Discovery Search]

    SEARCH -->|Budget exhausted, no stable clue| NO[NO EDGE FOUND]
    SEARCH -->|Candidate found| FREEZE[Freeze Candidate]

    FREEZE --> CR[Critic Process Audit]
    CR -->|Violation| INV[INVALID]
    CR -->|Bounded claim survives| V[Validation]

    V -->|Primary gate fails| REJ[REJECT]
    V -->|Integrity violation| INV
    V -->|Pass bounded validation| SE[Shadow Eligible]
```

No threshold/metric/population rescue is allowed inside the same locked contract.

## 6. Full search-tree accounting

```mermaid
flowchart TD
    P[P001] --> RC[Research Contract]
    RC --> H1[Hypothesis Family A]
    RC --> H2[Hypothesis Family B]
    RC --> H3[Hypothesis Family C]

    H1 --> F11[Feature invention A1]
    H1 --> F12[Feature invention A2]
    F11 --> T111[Threshold 1]
    F11 --> T112[Threshold 2]

    H2 --> M21[Model family B1]
    H2 --> M22[Model family B2]

    H3 --> S31[Subpopulation cut C1]

    T111 --> C[Final candidate]
    T112 --> C
    M21 --> C
    M22 --> C
    S31 --> C
```

The candidate's multiplicity burden comes from the entire path/search family, not just the final test.

## 7. Evidence Ledger and holdout consumption

```mermaid
flowchart LR
    E[Evidence Object] --> U0[UNEXPOSED]
    U0 -->|Discovery use| D[DISCOVERY CONSUMED]
    U0 -->|Validation use| V1[VALIDATION EXPOSURE #1]
    V1 -->|Related future validation| V2[VALIDATION EXPOSURE #2]
    V2 --> PART[PARTIALLY CONSUMED]
    PART -->|Exposure budget exhausted| C[CONSUMED / NOT INDEPENDENT HOLDOUT]
    C --> F[Require prospective / new evidence for stronger independent claim]
```

The exact statistical rule for consumption is future design work; the architectural fact that exposure is finite is mandatory.

## 8. Critic boundary

```mermaid
flowchart TD
    CAND[Candidate] --> CR[Critic]
    CR --> A1[Attack assumptions]
    CR --> A2[Check provenance]
    CR --> A3[Check leakage]
    CR --> A4[Check search budget / multiplicity]
    CR --> A5[Check claim breadth / sample support]

    CR -->|Clean bounded claim| ACCEPT[Accept bounded claim for next gate]
    CR -->|Scientific/process defect| INV[Invalidate]

    CR -. forbidden .-> RETUNE[Retune threshold]
    CR -. forbidden .-> RESCUE[Rescue subgroup]
    CR -. forbidden .-> METRIC[Change primary metric]
```

## 9. Frozen Shadow lifecycle

```mermaid
flowchart TD
    C1[Candidate C1 frozen] --> START[Shadow Start]
    START --> LIVE[Receive real clock / real data arrival / real spreads]
    LIVE --> NOADAPT[No adaptation of C1 from C1 outcomes]
    NOADAPT --> CLOSE[Shadow Close]
    CLOSE --> ADJ[Adjudicate C1]

    ADJ -->|Pass| GOV[Governor]
    ADJ -->|Fail| REJ[Reject C1]
    ADJ -->|Outcome suggests change| C2[Create descendant C2]
    C2 --> NEW[New genealogy / new evidence accounting]
```

## 10. Capability-gap decision flow

```mermaid
flowchart TD
    NS[No stable answer from bounded research] --> CLS[Classify why]
    CLS --> SAMP[Insufficient sample]
    CLS --> NP[Currently non-predictable]
    CLS --> ECON[Execution economics erase signal]
    CLS --> FORM[Problem formulation weak]
    CLS --> OBS[Evidence suggests insufficient observability]

    OBS --> CG[Capability Gap Clue]
    CG --> CRC[New bounded capability Research Contract]
    CRC --> OPTIONS[Possible new timeframe / event context / external feed / representation / feature primitive]
```

Failure does not automatically mean "add more features".

## 11. Evolution hierarchy

```mermaid
flowchart TD
    K[Level 0: Knowledge Evolution\nLearn without changing policy]
    P[Level 1: Policy Evolution\nNew composition from existing capabilities]
    M[Level 2: Model Evolution\nNew model artifacts / calibration]
    C[Level 3: Capability Evolution\nNew sensor / representation / source / code]

    K --> P --> M --> C
```

This is not a mandatory linear progression for every idea. It expresses increasing mutation depth and proof burden.

## 12. Code evolution / descendant model

```mermaid
flowchart TD
    CH[Immutable Active Champion] --> R[Research identifies capability gap]
    R --> CP[Capability Proposal]
    CP --> CODE[Code Candidate]
    CODE --> SB[Isolated Sandbox]
    SB --> COMP[Compile / Static Checks]
    COMP --> UT[Unit Tests]
    UT --> REG[Regression]
    REG --> SCI[Scientific Validation]
    SCI --> CR[Critic]
    CR --> SH[ Frozen Shadow ]
    SH --> GOV[Governor]

    GOV -->|Promote| NEW[New Champion]
    GOV -->|Reject| GY[Graveyard]
    NEW --> RB[Old Champion retained for Rollback]
```

The active system never edits itself in-place and immediately trades the mutation.

## 13. Fast loop vs slow loop

```mermaid
flowchart LR
    subgraph FAST[Fast Loop — Market Intelligence]
      T[Tick / incoming data] --> ST[State estimate]
      ST --> MR[Memory retrieval]
      MR --> DV[Decision value]
      DV --> SAFE[Capital safety]
      SAFE --> EX[Execute / Abstain]
    end

    subgraph SLOW[Slow Loop — Scientific Evolution]
      EXP[Experience] --> PROB[Problem detection]
      PROB --> RES[Research Contract]
      RES --> DISC[Bounded discovery]
      DISC --> CRIT[Critic]
      CRIT --> VAL[Validation]
      VAL --> SHAD[Shadow]
      SHAD --> PROM[Promotion / Reject]
    end

    EX --> EXP
    PROM --> MR
```

Fast loop adapts to current state. Slow loop changes knowledge/policy/capability only after proof.

## 14. Seed problem P001 flow

```mermaid
flowchart TD
    OBS[Observed: trades can reach favorable profit then deteriorate] --> G1[Hypothesis: after +1, protect around break-even]
    G1 --> PPR[Frozen Position-Path Replay]
    PPR --> VER[PPR_W1_G1_REJECT]
    VER --> MEM[Rejected Hypothesis Memory]
    MEM --> P001[P001 PROFIT GIVEBACK]
    P001 --> Q[Open question: richer pre-decision information gives stable EXIT-vs-CONTINUE incremental value?]
    Q --> U[ANSWER = UNKNOWN]
    U --> FUT[Future ARE testcase]
```

This flow intentionally stops at `UNKNOWN`. No G1.1/G2/manual indicator rescue is part of the current direction.

## 15. Development sequence

```mermaid
flowchart LR
    A0[ARE-0\nConstitution] --> A1[ARE-1\nScientific Registries]
    A1 --> A2[ARE-2\nExperience Intelligence]
    A2 --> A3[ARE-3\nAutonomous Science]
    A3 --> A4[ARE-4\nEvolution]
```

Do not start autonomous code generation before the constitutional and registry layers exist and have been audited.

## 16. Human checklist before future ARE implementation

A reviewer should be able to answer YES to all of these before implementation authority is granted:

- Is THINK separated from ACT by a PROVE layer?
- Is Scientific Constitution independent from Capital Safety?
- Is evidence exposure/holdout consumption represented?
- Is the full search genealogy represented?
- Can `NO RESULT` and `CURRENTLY_NON_PREDICTABLE` be final outcomes?
- Can Critic invalidate without retuning?
- Is Governor mostly mechanical/deterministic?
- Does shadow freeze the candidate for the window?
- Does a shadow-derived change create a descendant?
- Is information-time represented for every observable class?
- Can a capability gap be rejected instead of automatically adding features?
- Can code evolve only through isolated descendants?
- Is rollback retained?
- Is P001 preserved without manual answer injection?

If any answer is NO, the architecture is not ready for autonomous implementation.