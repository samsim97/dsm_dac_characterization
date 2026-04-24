# import numpy as np


# def read_data(filename):
#     data = np.loadtxt(filename, delimiter=',', skiprows=1)
#     timestamps = data[:, 0]
#     word_values = data[:, 1]
#     voltages = data[:, 2]
#     valid_mask = voltages <= 2.5
#     return timestamps[valid_mask], word_values[valid_mask], voltages[valid_mask]


# def calculate_dac_metrics(word_values, voltages):
#     if len(word_values) < 2:
#         return {
#             'samples': len(word_values),
#             'message': 'Not enough points for DAC metrics',
#         }

#     # Sort by code
#     sort_idx = np.argsort(word_values)
#     code = word_values[sort_idx]
#     v = voltages[sort_idx]

#     # Global linear fit (robust LSB estimate)
#     slope, intercept = np.polyfit(code, v, 1)

#     # Fit quality
#     v_fit = slope * code + intercept
#     residuals = v - v_fit
#     ss_res = np.sum(residuals ** 2)
#     ss_tot = np.sum((v - np.mean(v)) ** 2)
#     r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

#     # Define LSB from slope (CRITICAL FIX)
#     lsb = slope

#     # --- DNL ---
#     delta_code = np.diff(code)
#     delta_v = np.diff(v)

#     # Only keep true adjacent codes
#     mask = delta_code == 1

#     if np.any(mask):
#         step = delta_v[mask]
#         dnl = step / lsb - 1.0
#         max_dnl = np.max(np.abs(dnl))
#     else:
#         max_dnl = np.nan

#     # --- INL (best-fit) ---
#     inl = (v - v_fit) / lsb
#     max_inl = np.max(np.abs(inl))

#     # --- Monotonicity ---
#     monotonic_steps = np.sum(delta_v >= 0) if slope >= 0 else np.sum(delta_v <= 0)
#     monotonic_ratio = monotonic_steps / len(delta_v) if len(delta_v) else np.nan

#     return {
#         'samples': len(word_values),
#         'code_min': np.min(word_values),
#         'code_max': np.max(word_values),
#         'voltage_min': np.min(voltages),
#         'voltage_max': np.max(voltages),
#         'slope_v_per_code': slope,
#         'offset_v': intercept,
#         'r2': r2,
#         'lsb_v': lsb,
#         'max_abs_dnl_lsb': max_dnl,
#         'max_abs_inl_lsb': max_inl,
#         'monotonic_ratio': monotonic_ratio,
#     }


# def format_metrics(metrics):
#     if 'message' in metrics:
#         return [metrics['message']]

#     return [
#         f"Samples: {metrics['samples']}",
#         f"Code range: {metrics['code_min']:.0f} to {metrics['code_max']:.0f}",
#         f"Voltage range: {metrics['voltage_min']:.6g} V to {metrics['voltage_max']:.6g} V",
#         f"Slope (LSB estimate): {metrics['slope_v_per_code']:.6e} V/code",
#         f"Offset: {metrics['offset_v']:.6e} V",
#         f"Linear fit R^2: {metrics['r2']:.6f}",
#         f"LSB (from fit): {metrics['lsb_v']:.6e} V",
#         f"Max |DNL|: {metrics['max_abs_dnl_lsb']:.3f} LSB",
#         f"Max |INL|: {metrics['max_abs_inl_lsb']:.3f} LSB",
#         f"Monotonic steps: {metrics['monotonic_ratio'] * 100:.2f}%",
#     ]


# def plot_data(timestamps, word_values, voltages):
#     import matplotlib.pyplot as plt
#     metrics = calculate_dac_metrics(word_values, voltages)
#     metric_lines = format_metrics(metrics)

#     # Compute voltage deltas: delta[i] = voltage[i] - voltage[i-1]
#     # First point has no previous value, so we pad with NaN
#     voltage_deltas = np.empty(len(voltages))
#     voltage_deltas[0] = np.nan
#     voltage_deltas[1:] = np.diff(voltages)

#     # Delta timestamps: same as original (each delta is associated with its sample)
#     delta_timestamps = timestamps

#     # Compute bit resolution: log2(2.5V / |delta|), masking out zero/NaN deltas
#     FULL_SCALE_UV = 2.5e6  # 2.5 V in µV
#     with np.errstate(divide='ignore', invalid='ignore'):
#         abs_deltas_uv = np.abs(voltage_deltas * 1e6)
#         bit_resolution = np.where(
#             (abs_deltas_uv > 0) & ~np.isnan(abs_deltas_uv),
#             np.log2(FULL_SCALE_UV / abs_deltas_uv),
#             np.nan,
#         )

#     fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(10, 11))

#     word_line, = ax1.plot(
#         timestamps,
#         word_values,
#         color='tab:blue',
#         marker='x',
#         linestyle='None',
#         markersize=1,
#         label='Word Value',
#         picker=5,
#     )
#     ax1.set_ylabel('Word Value')
#     ax1.grid(True, alpha=0.3)
#     ax1.legend(loc='upper left')

#     voltage_line, = ax2.plot(
#         timestamps,
#         voltages,
#         color='tab:red',
#         marker='x',
#         linestyle='None',
#         markersize=1,
#         label='Voltage',
#         picker=5,
#     )
#     ax2.set_ylabel('Voltage (V)')
#     ax2.grid(True, alpha=0.3)
#     ax2.legend(loc='upper left')

#     delta_line, = ax3.plot(
#         delta_timestamps,# / 3600,
#         voltage_deltas * 1e6,
#         color='tab:green',
#         marker='x',
#         linestyle='None',
#         markersize=1,
#         label='Voltage Delta (V[i] - V[i-1])',
#         picker=5,
#     )
#     ax3.axhline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.6)
#     ax3.set_ylim(-5e-5 * 1e6, 5e-5 * 1e6)
#     # ax3.set_xlim(delta_timestamps[0] / 3600, delta_timestamps[-1] / 3600)
#     ax3.set_xlabel('Timestamp (h)')
#     ax3.set_ylabel('ΔVoltage (µV)')
#     ax3.grid(True, alpha=0.3)
#     ax3.legend(loc='upper left')

#     word_highlight = ax1.scatter([], [], s=120, facecolors='none', edgecolors='black', linewidths=2, zorder=5)
#     voltage_highlight = ax2.scatter([], [], s=120, facecolors='none', edgecolors='black', linewidths=2, zorder=5)
#     delta_highlight = ax3.scatter([], [], s=120, facecolors='none', edgecolors='black', linewidths=2, zorder=5)
#     selected_text = fig.text(
#         0.985,
#         0.06,
#         'Selected point:\nNone',
#         va='bottom',
#         ha='right',
#         fontsize=9,
#         bbox={'facecolor': 'white', 'alpha': 0.8, 'edgecolor': '0.7'},
#     )

#     def highlight_point(index):
#         word_highlight.set_offsets([[timestamps[index], word_values[index]]])
#         voltage_highlight.set_offsets([[timestamps[index], voltages[index]]])
#         delta_val = voltage_deltas[index]
#         if not np.isnan(delta_val):
#             delta_highlight.set_offsets([[delta_timestamps[index], delta_val * 1e6]])
#         else:
#             delta_highlight.set_offsets(np.empty((0, 2)))
#         selected_text.set_text(
#             'Selected point:\n'
#             f'Timestamp: {timestamps[index]:.6f} s\n'
#             f'Word value: {word_values[index]:.0f}\n'
#             f'Voltage: {voltages[index]:.6g} V\n'
#             f'ΔVoltage: {"N/A" if np.isnan(delta_val) else f"{delta_val * 1e6:.6g} µV"}'
#         )
#         fig.suptitle(f'DAC Word Value and Voltage at Timestamp {timestamps[index]:.6f} s')
#         print(
#             f"Selected point -> timestamp: {timestamps[index]:.6f} s, "
#             f"word value: {word_values[index]:.0f}, voltage: {voltages[index]:.6g} V, "
#             f"delta: {'N/A' if np.isnan(delta_val) else f'{delta_val * 1e6:.6g} µV'}"
#         )
#         fig.canvas.draw_idle()

#     def on_pick(event):
#         if event.artist not in (word_line, voltage_line, delta_line):
#             return
#         if not len(event.ind):
#             return
#         highlight_point(event.ind[0])

#     fig.canvas.mpl_connect('pick_event', on_pick)
#     fig.suptitle('DAC Word Value, Measured Voltage, and Voltage Deltas')
#     fig.text(
#         0.985,
#         0.5,
#         '\n'.join(metric_lines),
#         va='center',
#         ha='right',
#         fontsize=9,
#         bbox={'facecolor': 'white', 'alpha': 0.8, 'edgecolor': '0.7'},
#     )
#     fig.tight_layout(rect=[0, 0, 0.8, 1])

#     # --- Bit resolution figure ---
#     fig2, ax4 = plt.subplots(1, 1, figsize=(10, 4))
#     res_line, = ax4.plot(
#         delta_timestamps / 3600,
#         bit_resolution,
#         color='tab:purple',
#         marker='x',
#         linestyle='None',
#         markersize=1,
#         label='Bit Resolution (log₂(2.5 V / |ΔV|))',
#         picker=5,
#     )
#     # Draw integer bit reference lines only within the x-range where data exists
#     valid_mask_res = ~np.isnan(bit_resolution)
#     valid_bits = bit_resolution[valid_mask_res]
#     if len(valid_bits):
#         x_data_min = delta_timestamps[valid_mask_res][0]
#         x_data_max = delta_timestamps[valid_mask_res][-1]
#         bit_min = int(np.floor(np.nanmin(valid_bits)))
#         bit_max = int(np.ceil(np.nanmax(valid_bits)))
#         for b in range(bit_min, bit_max + 1):
#             ax4.plot([x_data_min, x_data_max], [b, b], color='gray', linewidth=0.6, linestyle='--', alpha=0.5)
#             ax4.text(x_data_max, b, f' {b}-bit', va='center', fontsize=7, color='gray')
#         # Clip y-axis to actual data range with a small margin
#         ax4.set_ylim(bit_min - 0.5, bit_max + 0.5)
#     ax4.set_xlim(delta_timestamps[0] / 3600, delta_timestamps[-1] / 3600)
#     ax4.set_xlabel('Timestamp (h)')
#     ax4.set_ylabel('Resolution (bits)')
#     ax4.set_title('Effective Bit Resolution from Voltage Deltas  [log₂(2.5 V / |ΔV|)]')
#     ax4.grid(True, alpha=0.3)
#     ax4.legend(loc='upper left')

#     res_highlight = ax4.scatter([], [], s=120, facecolors='none', edgecolors='black', linewidths=2, zorder=5)
#     res_selected_text = fig2.text(
#         0.985,
#         0.06,
#         'Selected point:\nNone',
#         va='bottom',
#         ha='right',
#         fontsize=9,
#         bbox={'facecolor': 'white', 'alpha': 0.8, 'edgecolor': '0.7'},
#     )

#     def highlight_point_res(index):
#         bits = bit_resolution[index]
#         if not np.isnan(bits):
#             res_highlight.set_offsets([[delta_timestamps[index], bits]])
#         else:
#             res_highlight.set_offsets(np.empty((0, 2)))
#         delta_val = voltage_deltas[index]
#         res_selected_text.set_text(
#             'Selected point:\n'
#             f'Timestamp: {timestamps[index]:.6f} s\n'
#             f'ΔVoltage: {"N/A" if np.isnan(delta_val) else f"{delta_val * 1e6:.6g} µV"}\n'
#             f'Resolution: {"N/A" if np.isnan(bits) else f"{bits:.2f} bits"}'
#         )
#         fig2.canvas.draw_idle()

#     def on_pick_res(event):
#         if event.artist is not res_line:
#             return
#         if not len(event.ind):
#             return
#         highlight_point_res(event.ind[0])

#     fig2.canvas.mpl_connect('pick_event', on_pick_res)
#     fig2.tight_layout(rect=[0, 0, 0.85, 1])

#     print('\nDAC characterization metrics:')
#     for line in metric_lines:
#         print(f"- {line}")

#     plt.show()

# if __name__ == "__main__":
#     filename = "data_1776870266.csv"
#     print(f"Reading data from {filename}...")
#     timestamps, word_values, voltages = read_data(filename)
#     plot_data(timestamps, word_values, voltages)

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

    lsb = slope

    # --- DNL ---
    delta_code = np.diff(code)
    delta_v = np.diff(v)
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
    import matplotlib
    import matplotlib.pyplot as plt

    metrics = calculate_dac_metrics(word_values, voltages)
    metric_lines = format_metrics(metrics)

    # Convert timestamps to hours for all plots
    ts_h = timestamps / 3600.0

    # Compute voltage deltas
    voltage_deltas = np.empty(len(voltages))
    voltage_deltas[0] = np.nan
    voltage_deltas[1:] = np.diff(voltages)
    delta_ts_h = ts_h  # same x-axis in hours

    # Bit resolution: log2(2.5 V / |delta|)
    FULL_SCALE_UV = 2.5e6  # µV
    with np.errstate(divide='ignore', invalid='ignore'):
        abs_deltas_uv = np.abs(voltage_deltas * 1e6)
        bit_resolution = np.where(
            (abs_deltas_uv > 0) & ~np.isnan(abs_deltas_uv),
            np.log2(FULL_SCALE_UV / abs_deltas_uv),
            np.nan,
        )

    # ------------------------------------------------------------------ #
    #  Figure 1 — Word value / Voltage / Delta  (high-DPI PNG)
    # ------------------------------------------------------------------ #
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(16, 12))
    fig.set_dpi(150)

    ax1.plot(ts_h, word_values, color='tab:blue', marker='x',
             linestyle='None', markersize=1, label='Word Value')
    ax1.set_ylabel('Word Value')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')

    ax2.plot(ts_h, voltages, color='tab:red', marker='x',
             linestyle='None', markersize=1, label='Voltage')
    ax2.set_ylabel('Voltage (V)')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')

    ax3.plot(delta_ts_h, voltage_deltas * 1e6, color='tab:green', marker='x',
             linestyle='None', markersize=1, label='ΔVoltage (V[i] − V[i−1])')
    ax3.axhline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.6)
    ax3.set_ylim(-5e-5 * 1e6, 5e-5 * 1e6)
    ax3.set_xlabel('Timestamp (h)')
    ax3.set_ylabel('ΔVoltage (µV)')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='upper left')

    fig.suptitle('DAC Word Value, Measured Voltage, and Voltage Deltas')
    fig.text(
        0.985, 0.5, '\n'.join(metric_lines),
        va='center', ha='right', fontsize=9,
        bbox={'facecolor': 'white', 'alpha': 0.8, 'edgecolor': '0.7'},
    )
    fig.tight_layout(rect=[0, 0, 0.8, 1])
    fig.savefig('dac_main.png', dpi=300, bbox_inches='tight')
    print('Saved dac_main.png')

    # ------------------------------------------------------------------ #
    #  Figure 2 — Bit resolution  (high-DPI PNG)
    # ------------------------------------------------------------------ #
    fig2, ax4 = plt.subplots(1, 1, figsize=(16, 5))
    fig2.set_dpi(150)

    ax4.plot(delta_ts_h, bit_resolution, color='tab:purple', marker='x',
             linestyle='None', markersize=1,
             label='Bit Resolution (log₂(2.5 V / |ΔV|))')

    valid_mask_res = ~np.isnan(bit_resolution)
    valid_bits = bit_resolution[valid_mask_res]
    if len(valid_bits):
        x_min_h = delta_ts_h[valid_mask_res][0]
        x_max_h = delta_ts_h[valid_mask_res][-1]
        bit_min = int(np.floor(np.nanmin(valid_bits)))
        bit_max = int(np.ceil(np.nanmax(valid_bits)))
        for b in range(bit_min, bit_max + 1):
            ax4.plot([x_min_h, x_max_h], [b, b],
                     color='gray', linewidth=0.6, linestyle='--', alpha=0.5)
            ax4.text(x_max_h, b, f' {b}-bit', va='center', fontsize=7, color='gray')
        ax4.set_ylim(bit_min - 0.5, bit_max + 0.5)

    ax4.set_xlim(ts_h[0], ts_h[-1])
    ax4.set_xlabel('Timestamp (h)')
    ax4.set_ylabel('Resolution (bits)')
    ax4.set_title('Effective Bit Resolution from Voltage Deltas  [log₂(2.5 V / |ΔV|)]')
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='upper left')

    fig2.tight_layout(rect=[0, 0, 0.9, 1])
    fig2.savefig('dac_resolution.png', dpi=300, bbox_inches='tight')
    print('Saved dac_resolution.png')

    # ------------------------------------------------------------------ #
    #  Interactive HTML via plotly
    # ------------------------------------------------------------------ #
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        # --- Figure 1: main plots ---
        pfig = make_subplots(
            rows=3, cols=1, shared_xaxes=True,
            subplot_titles=('Word Value', 'Voltage (V)', 'ΔVoltage (µV)'),
            vertical_spacing=0.06,
        )

        pfig.add_trace(go.Scattergl(
            x=ts_h, y=word_values, mode='markers',
            marker=dict(size=2, color='steelblue', symbol='x'),
            name='Word Value',
            hovertemplate='Time: %{x:.4f} h<br>Word: %{y:.0f}<extra></extra>',
        ), row=1, col=1)

        pfig.add_trace(go.Scattergl(
            x=ts_h, y=voltages, mode='markers',
            marker=dict(size=2, color='crimson', symbol='x'),
            name='Voltage',
            hovertemplate='Time: %{x:.4f} h<br>Voltage: %{y:.6g} V<extra></extra>',
        ), row=2, col=1)

        pfig.add_trace(go.Scattergl(
            x=delta_ts_h, y=voltage_deltas * 1e6, mode='markers',
            marker=dict(size=2, color='seagreen', symbol='x'),
            name='ΔVoltage',
            hovertemplate='Time: %{x:.4f} h<br>ΔV: %{y:.4g} µV<extra></extra>',
        ), row=3, col=1)

        # zero reference line on delta plot
        pfig.add_hline(y=0, line=dict(color='gray', dash='dash', width=0.8), row=3, col=1)

        pfig.update_yaxes(range=[-50, 50], row=3, col=1)
        pfig.update_xaxes(title_text='Timestamp (h)', row=3, col=1)
        pfig.update_layout(
            title='DAC Word Value, Measured Voltage, and Voltage Deltas',
            height=900, width=1400,
            plot_bgcolor='white',
            annotations=[
                dict(
                    x=1.01, y=0.5, xref='paper', yref='paper',
                    text='<br>'.join(metric_lines),
                    showarrow=False, align='left',
                    font=dict(size=10),
                    bgcolor='white', bordercolor='lightgray', borderwidth=1,
                )
            ],
        )
        pfig.write_html('dac_main_interactive.html')
        print('Saved dac_main_interactive.html')

        # --- Figure 2: bit resolution ---
        pfig2 = go.Figure()

        pfig2.add_trace(go.Scattergl(
            x=delta_ts_h, y=bit_resolution, mode='markers',
            marker=dict(size=2, color='mediumpurple', symbol='x'),
            name='Bit Resolution',
            hovertemplate='Time: %{x:.4f} h<br>Resolution: %{y:.2f} bits<extra></extra>',
        ))

        if len(valid_bits):
            for b in range(bit_min, bit_max + 1):
                pfig2.add_shape(
                    type='line',
                    x0=x_min_h, x1=x_max_h, y0=b, y1=b,
                    line=dict(color='gray', dash='dash', width=0.8),
                )
                pfig2.add_annotation(
                    x=x_max_h, y=b, text=f' {b}-bit',
                    showarrow=False, xanchor='left',
                    font=dict(size=9, color='gray'),
                )
            pfig2.update_yaxes(range=[bit_min - 0.5, bit_max + 0.5])

        pfig2.update_xaxes(range=[ts_h[0], ts_h[-1]], title_text='Timestamp (h)')
        pfig2.update_yaxes(title_text='Resolution (bits)')
        pfig2.update_layout(
            title='Effective Bit Resolution from Voltage Deltas  [log₂(2.5 V / |ΔV|)]',
            height=500, width=1400,
            plot_bgcolor='white',
        )
        pfig2.write_html('dac_resolution_interactive.html')
        print('Saved dac_resolution_interactive.html')

        # Open interactive HTML files in the default browser
        import webbrowser, os
        webbrowser.open('file://' + os.path.abspath('dac_main_interactive.html'))
        webbrowser.open('file://' + os.path.abspath('dac_resolution_interactive.html'))

    except ImportError:
        print('plotly not installed — skipping interactive HTML export.')
        print('Install with: pip install plotly')

    print('\nDAC characterization metrics:')
    for line in metric_lines:
        print(f"- {line}")

    plt.show()


if __name__ == "__main__":
    filename = "data_1776870266.csv"
    print(f"Reading data from {filename}...")
    timestamps, word_values, voltages = read_data(filename)
    plot_data(timestamps, word_values, voltages)