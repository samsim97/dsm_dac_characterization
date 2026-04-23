import re
import time
import numpy as np
import pyvisa
from redpitaya.redpitaya import redpitaya

# ---------------- PARAMETERS ----------------

WORD_WIDTH = 20
MAX_CODE = 2**WORD_WIDTH - 1

N_CODES = 1000
N_SAMPLES_PER_CODE = 1000

SETTLING_TIME = 1       # seconds (adjust for your DSM)
SAMPLE_DELAY = 0.002       # time between DMM reads

OUTPUT_FILE = f"dac_dc_characterization_{int(time.time())}.csv"

# ---------------- INSTRUMENT SETUP ----------------

rm = pyvisa.ResourceManager()
inst = rm.open_resource('GPIB0::16::INSTR')
inst.timeout = 5000

rp = redpitaya()
rp.pin_write_dir(1, 'N', 'OUT')

pattern = re.compile(r'^([+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)')

# ---------------- CODE SELECTION ----------------

def generate_test_codes():
    """Deterministic symmetric DAC test vector (correct signed 20-bit)."""

    codes = set()

    MIN_CODE = -(2**(WORD_WIDTH - 1))
    MAX_CODE = (2**(WORD_WIDTH - 1)) - 1

    RANGE = MAX_CODE - MIN_CODE

    # ----------------------------
    # 1. Absolute anchors
    # ----------------------------
    anchors = [
        MIN_CODE,
        -RANGE // 4,
        -RANGE // 8,
        0,
        RANGE // 8,
        RANGE // 4,
        MAX_CODE
    ]

    for c in anchors:
        codes.add(int(c))

    # ----------------------------
    # 2. Dense regions around key points
    # ----------------------------

    def dense_region(center, span, step):
        for c in range(center - span, center + span, step):
            if MIN_CODE <= c <= MAX_CODE:
                codes.add(c)

    # zero region (critical for DSM)
    dense_region(0, 5000, 10)

    # negative edge
    dense_region(MIN_CODE, 5000, 10)

    # positive edge
    dense_region(MAX_CODE, 5000, 10)

    # ----------------------------
    # 3. Uniform coarse grid (global coverage)
    # ----------------------------
    for c in range(MIN_CODE, MAX_CODE, RANGE // 200):
        codes.add(c)

    # ----------------------------
    # 4. Medium grid
    # ----------------------------
    for c in range(MIN_CODE, MAX_CODE, RANGE // 500):
        codes.add(c)

    # ----------------------------
    # Final cleanup (IMPORTANT FIX)
    # ----------------------------
    codes = np.array(sorted(codes))

    # enforce exact size WITHOUT bias
    if len(codes) > N_CODES:
        step = len(codes) / N_CODES
        codes = np.array([codes[int(i * step)] for i in range(N_CODES)])
    else:
        # deterministic padding using cyclic expansion
        i = 0
        while len(codes) < N_CODES:
            codes = np.append(codes, codes[i % len(codes)])
            i += 1

    return codes.astype(int)

# ---------------- MEASUREMENT ----------------

def read_voltage():
    read = inst.query('DATA:FRESh?')
    match = pattern.match(read)
    return float(match.group(1)) if match else np.nan


def measure_code(code):
    """Measure one DAC code with averaging."""

    rp.pin_write(1, 'N', int(code))

    time.sleep(SETTLING_TIME)

    values = []

    # Burn-in samples (avoid transient)
    for _ in range(50):
        _ = read_voltage()
        time.sleep(SAMPLE_DELAY)

    # Acquisition
    for _ in range(N_SAMPLES_PER_CODE):
        v = read_voltage()
        if np.isfinite(v):
            values.append(v)
        time.sleep(SAMPLE_DELAY)

    values = np.array(values)

    return {
        "code": code,
        "mean": np.mean(values),
        "std": np.std(values),
        "n": len(values)
    }

# ---------------- MAIN LOOP ----------------

def main():
    codes = generate_test_codes()
    print(codes)
    return

    results = []

    start = time.time()

    for i, code in enumerate(codes):

        print(f"[{i+1}/{len(codes)}] Measuring code {code}")

        try:
            res = measure_code(code)
            results.append(res)

        except Exception as e:
            print(f"Error at code {code}: {e}")

        # periodic save
        if i % 20 == 0 and len(results) > 0:
            np.savetxt(
                OUTPUT_FILE,
                [[r["code"], r["mean"], r["std"], r["n"]] for r in results],
                delimiter=",",
                header="Code,MeanVoltage,StdVoltage,N",
                comments=""
            )

    # final save
    np.savetxt(
        OUTPUT_FILE,
        [[r["code"], r["mean"], r["std"], r["n"]] for r in results],
        delimiter=",",
        header="Code,MeanVoltage,StdVoltage,N",
        comments=""
    )

    inst.close()

    print(f"Done. Duration: {time.time() - start:.2f} s")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()