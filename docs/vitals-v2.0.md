# Vitals Telemetry Contract — v2.0

## Overview

The v2.0 vitals payload is the single authoritative format published by the
**vitals-publisher** service on the MQTT topic:

```
medtech/vitals/latest
```

All consumers (**edge-analytics**, **clinician-ui**, and any future services)
**must** validate the `version` field and reject (log + drop) payloads where
`version != "2.0"`.

The canonical JSON Schema is located at:
```
schemas/vitals/v2.0.json
```

---

## Fields

| Field              | Type             | Unit / Notes                                                            |
|--------------------|------------------|-------------------------------------------------------------------------|
| `version`          | `string`         | Always `"2.0"`. Consumers must reject any other value.                 |
| `patient_id`       | `string`         | Unique patient or simulated-patient identifier.                         |
| `scenario`         | `string` (enum)  | `healthy` \| `sepsis` \| `critical`                                    |
| `scenario_stage`   | `string` (enum)  | `healthy` \| `pre_sepsis` \| `sepsis_onset` \| `sepsis` \| `septic_shock` |
| `timestamp`        | `integer`        | Unix epoch in **milliseconds** (ms). Always positive.                  |
| `hr`               | `number`         | Heart rate — **bpm** (beats per minute).                               |
| `bp_sys`           | `number`         | Systolic blood pressure — **mmHg**.                                     |
| `bp_dia`           | `number`         | Diastolic blood pressure — **mmHg**.                                    |
| `o2_sat`           | `number`         | Peripheral oxygen saturation — **%** (SpO₂). Range 0–100.              |
| `temperature`      | `number`         | Body temperature — **°C** (Celsius).                                    |
| `respiratory_rate` | `number`         | Respiratory rate — **breaths/min**.                                     |
| `wbc`              | `number`         | White blood cell count — **10³/µL**.                                    |
| `lactate`          | `number`         | Blood lactate — **mmol/L**.                                             |
| `sirs_score`       | `integer`        | SIRS score — range **0–4**.                                             |
| `qsofa_score`      | `integer`        | qSOFA score — range **0–3**.                                            |
| `sepsis_stage`     | `string` (enum)  | `none` \| `sirs` \| `sepsis` \| `septic_shock`                         |
| `sepsis_onset_ts`  | `integer` \| `null` | Unix epoch in **ms** when sepsis onset detected; `null` if not yet.  |
| `quality`          | `string`         | Signal quality indicator, e.g. `"good"`, `"degraded"`, `"poor"`.      |
| `source`           | `string`         | Data source/device identifier, e.g. `"synthea-simulator"`.             |

---

## Enumerations

### `scenario`
| Value      | Description                              |
|------------|------------------------------------------|
| `healthy`  | Normal, non-deteriorating patient.       |
| `sepsis`   | Patient on a sepsis trajectory.          |
| `critical` | Critically ill patient (non-sepsis).     |

### `scenario_stage`
| Value           | Description                                                        |
|-----------------|--------------------------------------------------------------------|
| `healthy`       | Stable, no deterioration signs.                                    |
| `pre_sepsis`    | Early sub-clinical indicators; SIRS criteria not yet fully met.   |
| `sepsis_onset`  | First moment when sepsis criteria are met.                         |
| `sepsis`        | Established sepsis.                                                |
| `septic_shock`  | Organ dysfunction with hypotension; highest severity.             |

### `sepsis_stage`
| Value          | Description                                             |
|----------------|---------------------------------------------------------|
| `none`         | No sepsis indicators.                                   |
| `sirs`         | SIRS criteria met but infection not confirmed.          |
| `sepsis`       | Infection-driven organ dysfunction (Sepsis-3 criteria). |
| `septic_shock` | Sepsis with circulatory/metabolic failure.              |

---

## Invariants

1. **`version` must be `"2.0"`** — consumers must hard-reject any other value.
2. **`timestamp` and `sepsis_onset_ts` are Unix epoch milliseconds** — divide by
   1000 to convert to seconds.
3. **`sepsis_onset_ts` is `null`** until the first moment sepsis is detected
   within a scenario run; once set it remains constant for that run.
4. **All fields are required** — the schema uses `additionalProperties: false`.
   Consumers must not accept partial payloads.
5. **Numeric vitals are `number`** (float) unless explicitly marked `integer`
   (scores, timestamps). Do not assume integer arithmetic on vitals.

---

## Example Payload

```json
{
  "version": "2.0",
  "patient_id": "patient-001",
  "scenario": "sepsis",
  "scenario_stage": "sepsis_onset",
  "timestamp": 1746376800000,
  "hr": 102.5,
  "bp_sys": 95.0,
  "bp_dia": 62.0,
  "o2_sat": 94.2,
  "temperature": 38.7,
  "respiratory_rate": 22.0,
  "wbc": 13.4,
  "lactate": 2.3,
  "sirs_score": 3,
  "qsofa_score": 2,
  "sepsis_stage": "sepsis",
  "sepsis_onset_ts": 1746376500000,
  "quality": "good",
  "source": "synthea-simulator"
}
```

The example file is also available at `examples/vitals/v2.0.example.json`.

---

## Consumer Integration Guidance

### Python (edge-analytics, vitals-publisher)
```python
import json
import jsonschema

# Load schema once at startup
with open("path/to/schemas/vitals/v2.0.json") as f:
    VITALS_SCHEMA = json.load(f)

def validate_payload(payload: dict) -> None:
    """Raises jsonschema.ValidationError if payload is invalid."""
    jsonschema.validate(instance=payload, schema=VITALS_SCHEMA)
```

### JavaScript / TypeScript (clinician-ui)
```js
import Ajv from "ajv";
import schema from "./schemas/vitals/v2.0.json";

const ajv = new Ajv();
const validate = ajv.compile(schema);

function validatePayload(payload) {
  if (!validate(payload)) {
    throw new Error(JSON.stringify(validate.errors));
  }
}
```

---

## Changelog

| Version | Date       | Notes                        |
|---------|------------|------------------------------|
| 2.0     | 2025-05-04 | Initial v2.0 contract.       |
