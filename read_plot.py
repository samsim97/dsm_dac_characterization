import numpy as np


def read_data(filename):
    data = np.loadtxt(filename, delimiter=',', skiprows=1)
    timestamps = data[:, 0]
    word_values = data[:, 1]
    voltages = data[:, 2]
    valid_mask = voltages <= 2.5
    return timestamps[valid_mask], word_values[valid_mask], voltages[valid_mask]


def calculate_dac_metrics(word_values, voltages):
    if len(word_values) < 2:
        return {
            'samples': len(word_values),
            'message': 'Not enough points for DAC metrics',
        }

    # Sort by code
    sort_idx = np.argsort(word_values)
    code = word_values[sort_idx]
    v = voltages[sort_idx]

    # Global linear fit (robust LSB estimate)
    slope, intercept = np.polyfit(code, v, 1)

    # Fit quality
    v_fit = slope * code + intercept
    residuals = v - v_fit
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((v - np.mean(v)) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

    # Define LSB from slope (CRITICAL FIX)
    lsb = slope

    # --- DNL ---
    delta_code = np.diff(code)
    delta_v = np.diff(v)

    # Only keep true adjacent codes
    mask = delta_code == 1

    if np.any(mask):
        step = delta_v[mask]
        dnl = step / lsb - 1.0
        max_dnl = np.max(np.abs(dnl))
    else:
        max_dnl = np.nan

    # --- INL (best-fit) ---
    inl = (v - v_fit) / lsb
    max_inl = np.max(np.abs(inl))

    # --- Monotonicity ---
    monotonic_steps = np.sum(delta_v >= 0) if slope >= 0 else np.sum(delta_v <= 0)
    monotonic_ratio = monotonic_steps / len(delta_v) if len(delta_v) else np.nan

    return {
        'samples': len(word_values),
        'code_min': np.min(word_values),
        'code_max': np.max(word_values),
        'voltage_min': np.min(voltages),
        'voltage_max': np.max(voltages),
        'slope_v_per_code': slope,
        'offset_v': intercept,
        'r2': r2,
        'lsb_v': lsb,
        'max_abs_dnl_lsb': max_dnl,
        'max_abs_inl_lsb': max_inl,
        'monotonic_ratio': monotonic_ratio,
    }


def format_metrics(metrics):
    if 'message' in metrics:
        return [metrics['message']]

    return [
        f"Samples: {metrics['samples']}",
        f"Code range: {metrics['code_min']:.0f} to {metrics['code_max']:.0f}",
        f"Voltage range: {metrics['voltage_min']:.6g} V to {metrics['voltage_max']:.6g} V",
        f"Slope (LSB estimate): {metrics['slope_v_per_code']:.6e} V/code",
        f"Offset: {metrics['offset_v']:.6e} V",
        f"Linear fit R^2: {metrics['r2']:.6f}",
        f"LSB (from fit): {metrics['lsb_v']:.6e} V",
        f"Max |DNL|: {metrics['max_abs_dnl_lsb']:.3f} LSB",
        f"Max |INL|: {metrics['max_abs_inl_lsb']:.3f} LSB",
        f"Monotonic steps: {metrics['monotonic_ratio'] * 100:.2f}%",
    ]


def plot_data(timestamps, word_values, voltages):
    import matplotlib.pyplot as plt
    metrics = calculate_dac_metrics(word_values, voltages)
    metric_lines = format_metrics(metrics)

    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 8))

    word_line, = ax1.plot(
        timestamps,
        word_values,
        color='tab:blue',
        marker='x',
        linestyle='None',
        markersize=1,
        label='Word Value',
        picker=5,
    )
    ax1.set_ylabel('Word Value')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')

    voltage_line, = ax2.plot(
        timestamps,
        voltages,
        color='tab:red',
        marker='x',
        linestyle='None',
        markersize=1,
        label='Voltage',
        picker=5,
    )
    ax2.set_xlabel('Timestamp (s)')
    ax2.set_ylabel('Voltage (V)')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')

    word_highlight = ax1.scatter([], [], s=120, facecolors='none', edgecolors='black', linewidths=2, zorder=5)
    voltage_highlight = ax2.scatter([], [], s=120, facecolors='none', edgecolors='black', linewidths=2, zorder=5)
    selected_text = fig.text(
        0.985,
        0.08,
        'Selected point:\nNone',
        va='bottom',
        ha='right',
        fontsize=9,
        bbox={'facecolor': 'white', 'alpha': 0.8, 'edgecolor': '0.7'},
    )

    def highlight_point(index):
        word_highlight.set_offsets([[timestamps[index], word_values[index]]])
        voltage_highlight.set_offsets([[timestamps[index], voltages[index]]])
        selected_text.set_text(
            'Selected point:\n'
            f'Timestamp: {timestamps[index]:.6f} s\n'
            f'Word value: {word_values[index]:.0f}\n'
            f'Voltage: {voltages[index]:.6g} V'
        )
        fig.suptitle(f'DAC Word Value and Voltage at Timestamp {timestamps[index]:.6f} s')
        print(
            f"Selected point -> timestamp: {timestamps[index]:.6f} s, "
            f"word value: {word_values[index]:.0f}, voltage: {voltages[index]:.6g} V"
        )
        fig.canvas.draw_idle()

    def on_pick(event):
        if event.artist not in (word_line, voltage_line):
            return
        if not len(event.ind):
            return
        highlight_point(event.ind[0])

    fig.canvas.mpl_connect('pick_event', on_pick)
    fig.suptitle('DAC Word Value and Measured Voltage')
    fig.text(
        0.985,
        0.5,
        '\n'.join(metric_lines),
        va='center',
        ha='right',
        fontsize=9,
        bbox={'facecolor': 'white', 'alpha': 0.8, 'edgecolor': '0.7'},
    )
    fig.tight_layout(rect=[0, 0, 0.8, 1])

    print('\nDAC characterization metrics:')
    for line in metric_lines:
        print(f"- {line}")

    plt.show()

if __name__ == "__main__":
    filename = "data_1776870266.csv"
    print(f"Reading data from {filename}...")
    timestamps, word_values, voltages = read_data(filename)
    plot_data(timestamps, word_values, voltages)