# Fashion Store SAT Encoder – Constraint & Colour Harmony Reference

## 1 Constraint Families

| ID    | Constraint Family                    | Example Formal Rule                                                        | CNF‑Encoding Sketch                                                                |
| ----- | ------------------------------------ | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **A** | **Outfit Size**                      | `MIN_G ≤ Σ Gᵢ ≤ MAX_G` (e.g. 3 ≤ garments ≤ 6)                             | Cardinality network or pair‑wise clauses when _N_ is small                         |
| **B** | **Type Coverage**                    | “Exactly one _top_, at least one _bottom_, ≤ 1 *hat*”                      | Partition the garment variables by _type_ and impose `AtMost`/`AtLeast` per bucket |
| **C** | **Palette Size**                     | `MIN_C ≤ Σ Cₖ ≤ MAX_C` where `Cₖ ⇔ ∨_{g∈col(k)} G_g`                       | Indicator vars `Cₖ` + a cardinality constraint on them                             |
| **D** | **Colour Clashes**                   | Forbid (`red`,`pink`) appearing together                                   | For each conflicting pair `(g,h)`: clause `¬G_g ∨ ¬G_h`                            |
| **E** | **Complement Harmony**               | “If a _warm_ hue appears, at least one _cool_ complement must also appear” | Warm‑present → Cool‑present (implication = 2‑CNF)                                  |
| **F** | **Layering Order**                   | “If a _coat_ is chosen, a _top_ must also be chosen”                       | For each coat `g`: `¬G_g ∨ (∨_{tops t} G_t)`                                       |
| **G** | **One‑Per‑Body‑Part**                | “You can’t wear two hats at once”                                          | `AtMost1(HAT)` = pair‑wise `¬G_i ∨ ¬G_j` or a cardinality gadget                   |
| **H** | **Season / Context**                 | `WINTER → (∨ outerwear)`                                                   | Introduce a global literal `WINTER`; add the implication                           |
| **I** | **Cost / Style Optimisation (soft)** | Minimise `Σ priceᵢ·Gᵢ`                                                     | Use **MaxSAT**: hard clauses + weighted soft clauses                               |
| **J** | **RGB Distance (advanced)**          | “Average ΔE between any two colours ≥ 20”                                  | Pre‑compute violating pairs → treat as clashes **or** move to SMT                  |

> _Pick only the constraints you need; keep the rest for bonus experiments or “future work” in the report._

---

## 2 Colour Harmony Modes (generated from a fixed list of named colours)

Every named colour is mapped to a hue angle `h ∈ [0°,360°)`.  
Let `Cₖ` be the Boolean indicator “colour *k* appears”.

| `--harmony` value                 | Informal Rule                                                           | CNF Clauses Emitted                                                                                               |
| --------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `any` _(default)_                 | No extra restriction beyond global palette limits                       | _None_                                                                                                            |
| `complementary`                   | Palette must be **exactly two** complementary colours (`h`, `h + 180°`) | 1. `Σ Cₖ = 2` (AtMost + AtLeast)<br>2. For each colour *k*: `¬Cₖ ∨ C_compl(k)`                                    |
| `analogous` _(±30° window)_       | All chosen colours must lie inside a 60° arc                            | Pre‑compute pairs with Δhue > 30°; add `¬C_i ∨ ¬C_j` for each                                                     |
| `triadic` _(120° apart)_          | Exactly three colours forming a triad                                   | Enumerate **allowed triples** `{a,b,c}`.<br>Add Tseitin var for each triple and a big disjunction plus `Σ Cₖ = 3` |
| `tetradic` _(double complements)_ | Four colours forming two complementary pairs                            | Enumerate allowed quadruples; require `Σ Cₖ = 4`                                                                  |

### Example Named‑Hue Table

| Colour     | Hue (°) |
| ---------- | ------- |
| red        | 0       |
| orange     | 30      |
| yellow     | 60      |
| chartreuse | 90      |
| green      | 120     |
| turquoise  | 150     |
| cyan       | 180     |
| azure      | 210     |
| blue       | 240     |
| violet     | 270     |
| magenta    | 300     |
| rose       | 330     |

---

The encoder inserts the harmony‑specific clauses right after it builds the `Cₖ` indicator variables—no other part of your model needs to change.
