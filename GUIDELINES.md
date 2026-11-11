# Annotation guidelines

These guidelines are for annotators comparing two AI responses to the same hardware or mechanical engineering question. Each judgment produces one record in `data/pairs.jsonl`.

## 1. Read the prompt first

Write down what the user actually needs before reading either response: the quantity asked for, its units, and every constraint stated (load direction, supply voltage, bus speed, material). Many bad responses are fluent and confident but answer a slightly different question.

## 2. Check each response independently

For each response, work through this order and stop at the first serious failure:

1. **Is the physics right?** Correct formula, correct boundary conditions, correct reading of datasheet parameters.
2. **Is the arithmetic right?** Recompute key numbers. Do not trust a value because it is precise.
3. **Are the units right?** Watch for rad/s labeled as Hz, mm and m mixed, mil and mm mixed.
4. **Does it respect every constraint in the prompt?**
5. **Is it safe?** Would following it damage hardware or hurt someone?
6. **Is it useful?** Practical next steps, standard part values, trade-offs.

## 3. Choose and rate strength

| Strength | Meaning |
|---|---|
| 3 | One response is wrong or unsafe and the other is right |
| 2 | Both are usable, but one has a clear error or misses the main constraint |
| 1 | Both are correct; one is somewhat clearer or more complete |

Rules:

* **Correctness beats style.** A short correct answer always beats a long, polished, wrong one.
* **Do not prefer the longer response by default.** Length is only a plus when the extra text adds checks, trade-offs or next steps.
* **Position does not matter.** The validator reports A/B balance; a strong skew across your labels is a sign of position bias.
* **Unsafe advice is always strength 3**, tagged `unsafe` alongside the underlying error.

## 4. Tag the error in the rejected response

Use one or more tags. Strength 3 pairs need at least one tag; strength 1 pairs normally have none.

| Tag | Use when | Example |
|---|---|---|
| `omitted_term` | A term or factor is left out of an otherwise correct formula | LED resistor sized without subtracting Vf |
| `wrong_formula` | A different formula or quantity was used | Regulator loss computed as Vout x I |
| `wrong_constant` | Correct formula, wrong coefficient or table value | IPC-2221 internal-layer k used for an external trace |
| `unit_error` | Wrong unit, missing conversion or mislabeled unit | omega_n in rad/s reported as Hz |
| `ignored_loading` | Source or load impedance ignored | Divider output computed without the ADC input impedance |
| `misread_datasheet` | A parameter used for something it does not mean | Vgs(th) treated as full turn-on voltage |
| `rule_of_thumb_misapplied` | A heuristic used outside its range | 10k I2C pull-ups at 400 kHz and 200 pF |
| `misconception` | Wrong mental model of the physics | "Bigger decoupling capacitor is always better" |
| `reversed_logic` | Rule applied backwards | Interference fit on the stationary bearing ring |
| `overgeneralization` | A conditional rule stated as always true | "One diameter of thread engagement is always enough" |
| `ignored_requirement` | A stated constraint is ignored | Print orientation chosen for finish when a load was stated |
| `unsafe` | Advice that could damage hardware or injure someone | Approving a regulator that would overheat |

## 5. Write the critique

The critique is what a model or another annotator learns from. It should:

* name the error and where it happens,
* give the corrected value or rule,
* say briefly why the preferred response is better.

Good: "Response A ignores the LED forward voltage and uses the full supply voltage. With 250 ohm the current is only 12 mA. Response B subtracts Vf and gets 150 ohm."

Weak: "B is better and more accurate."

## 6. Quality control

* `python tools/validate.py` must pass before a batch is submitted.
* Overlapping items are labeled by two annotators. `python tools/agreement.py` reports Cohen's kappa; a target of 0.7 or higher is typical for this task. Every disagreement is adjudicated against these guidelines, and the guideline is clarified if the disagreement came from ambiguity rather than an error.
