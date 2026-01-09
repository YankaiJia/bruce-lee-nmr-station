import pandas as pd
import matplotlib.pyplot as plt


def peak_color(peak_name):
    if "Ar" in peak_name:
        return "tab:purple"
    if "CH3" in peak_name:
        return "tab:red"
    if "Ha" in peak_name:
        return "tab:blue"
    if "Hb" in peak_name:
        return "tab:orange"
    if "Hc" in peak_name:
        return "tab:green"
    return "tab:gray"

def plot_reference_peaks(
    csv_peak,
    show_aromatic=True,
    show_dots=True,
    save_path=None
):
    df = pd.read_csv(csv_peak)

    # 🔀 switch: hide aromatic region
    if not show_aromatic:
        df = df[~df["peak"].str.contains("Ar", case=False)]

    fig, ax = plt.subplots(figsize=(10, 2))

    # y-axis as index space only
    ax.set_ylim(-0.5, len(df) - 0.5)

    for i, (ppm, peak) in enumerate(zip(df["ppm"], df["peak"])):
        color = peak_color(peak)

        # ✅ reference vertical line (axis-spanning)
        ax.axvline(
            x=ppm,
            color=color,
            linewidth=1,
            alpha=0.5,
            zorder=1
        )

        # dot (optional)
        if show_dots:
            ax.scatter(
                ppm,
                i,
                color=color,
                s=50,
                zorder=3
            )

        # label
        # label (tilted)
        ax.text(
            ppm,
            i,
            # f"{peak} ({ppm:.2f})",
            f"{peak.split('_')[0]}",

            fontsize=18,
            ha="right",
            va="center",
            rotation=35,              # <- tilt angle (try 25–60)
            rotation_mode="anchor",   # <- keep anchor point stable
            zorder=4
        )


    # NMR-style axis
    ax.invert_xaxis()
    ax.set_xlabel("ppm")
    ax.set_title("Reference NMR peaks")

    ax.set_yticks([])
    ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.6, zorder=0)

    plt.tight_layout()

    if save_path is not None:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()




csv_peak = r'D:\Dropbox\brucelee\code\vscode_projects\bruce-nmr-station\data-treatment\yield_from_nmr_spectrum\peaks_for_BDA.csv'

# plot_reference_peaks(csv_peak, show_aromatic=True)

plot_reference_peaks(csv_peak, show_aromatic=False)

