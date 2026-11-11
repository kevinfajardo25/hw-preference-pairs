# hw-preference-pairs

A pairwise preference dataset for training and evaluating AI models on hardware and mechanical engineering questions (the format used for RLHF reward models and DPO), plus quality-control tools for the annotation process: a schema and bias validator and an inter-annotator agreement report.

Each record has a real engineering question, two candidate responses, which one an expert prefers, how strongly, a tag naming the error in the rejected response, and a written critique.

## What is inside

```
data/
  pairs.jsonl        12 expert-labeled pairs (electronics, PCB, mechanical)
  annotations.csv    labels from two annotators on the same items
tools/
  validate.py        schema, taxonomy, consistency and bias checks (CI-friendly exit code)
  agreement.py       accuracy against gold, Cohen's kappa, list of items to adjudicate
tests/
  test_tools.py      13 tests, including a check that the dataset itself passes validation
GUIDELINES.md        annotation guidelines and error taxonomy
```

## What the pairs test

| ID | Topic | Error in the rejected response |
|---|---|---|
| HW-001 | LED current-limiting resistor | Forgot to subtract the LED forward voltage |
| HW-002 | LDO dissipation, 12 V to 3.3 V at 500 mA | Used Vout x I instead of (Vin - Vout) x I; approved a design that overheats |
| HW-003 | Voltage divider into an ADC | Ignored the ADC input impedance loading the divider |
| HW-004 | I2C pull-ups at 400 kHz, 200 pF | Used 10k, which violates the 300 ns rise-time limit |
| HW-005 | MOSFET driven from 3.3 V logic | Treated Vgs(th) as the full turn-on voltage |
| HW-006 | IPC-2221 trace width | Used the internal-layer constant for an external trace |
| HW-007 | MCU decoupling | One large capacitor instead of per-pin 100 nF; ignored loop inductance |
| HW-008 | Bearing fits | Interference fit put on the wrong ring |
| HW-009 | FDM print orientation for a loaded bracket | Optimized surface finish and ignored the load across layers |
| HW-010 | Thread engagement in aluminum | Applied the steel one-diameter rule to aluminum |
| HW-011 | Relay flyback diode | Near tie: both correct, one adds a release-time trade-off |
| HW-012 | Natural frequency | rad/s reported as Hz |

## Record format

```json
{
  "id": "HW-005",
  "domain": "electronics",
  "prompt": "Can I switch a 12 V, 3 A load with an IRF540N driven directly from a 3.3 V microcontroller pin?",
  "response_a": "Not reliably. The IRF540N's Vgs(th) is 2 to 4 V ...",
  "response_b": "Yes. The gate threshold voltage is 2 to 4 V, and 3.3 V is above the 2 V minimum ...",
  "preferred": "A",
  "strength": 3,
  "error_tags": ["misread_datasheet"],
  "critique": "Response B treats gate threshold voltage as the full-enhancement voltage ..."
}
```

`strength` is 1 (near tie), 2 (clear preference) or 3 (one response is wrong or unsafe). The preferred response appears in position A and B at a balanced rate so position bias can be measured.

## Quality control

```bash
python tools/validate.py data/pairs.jsonl
python tools/agreement.py data/pairs.jsonl data/annotations.csv
pytest -q
```

```
12 pairs in data/pairs.jsonl
position: A preferred 7, B preferred 5
preferred response is the longer one in 8/12 pairs (67%)
OK

Accuracy against gold
  annotator_1    100.0%  (12 items)
  annotator_2     83.3%  (12 items)

Pairwise agreement
  annotator_1 vs annotator_2: raw 83.3%, Cohen's kappa 0.68
  disagreements to adjudicate: HW-009 (...), HW-011 (...)
```

The validator flags:

* **Schema errors:** missing fields, duplicate ids, invalid labels, unknown tags, identical responses.
* **Consistency warnings:** a strength 3 preference with no error tag, or a near tie that carries error tags.
* **Length bias:** if the preferred answer is nearly always the longer one, a reward model trained on the data may learn "longer is better." Several pairs here are deliberately won by the shorter response.

The agreement tool shows why overlap labeling matters: both disagreements in the sample are on the lower-strength items (a near tie and a constraint-reading question), which is where guidelines usually need clarifying.

## Related

* [mecheng-llm-eval](https://github.com/kevinfajardo25/mecheng-llm-eval): numeric evaluation set and auto-grader
* [mechcalc](https://github.com/kevinfajardo25/mechcalc): tested engineering formulas used to check answers
* [tolstack](https://github.com/kevinfajardo25/tolstack): tolerance stack-up analysis

## License

MIT
