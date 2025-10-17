import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------
# Global plot style and figure setup
# ---------------------------------------------------------------------
plt.style.use('seaborn-v0_8-whitegrid')          # Elegant, light grid style
fig, axes = plt.subplots(1, 2, figsize=(13, 5))  # Two subplots side by side

# =====================================================================
# Plot 1 — Integration vs DPE Concentration (with linear fit)
# =====================================================================
# Experimental data: DPE concentration vs integration
dpe_conc = np.array([422.75, 212.44, 105.6, 52.8, 26.4])
dpe_intg = np.array([44.7, 22.59, 11.44, 5.78, 2.98])

# Perform linear regression (1st-degree polynomial)
coeffs1 = np.polyfit(dpe_conc, dpe_intg, 1)    # Fit y = a*x + b
fit_line1 = np.polyval(coeffs1, dpe_conc)      # Calculate fitted y values

# Compute R² for goodness of fit
r2_1 = 1 - np.sum((dpe_intg - fit_line1)**2) / np.sum((dpe_intg - np.mean(dpe_intg))**2)

# Select left subplot (axes[0])
ax1 = axes[0]

# Plot scatter points (blue)
ax1.scatter(
    dpe_conc, dpe_intg,
    color='#1f77b4', s=80, edgecolor='white', zorder=3,
    label='Data points'
)

# Plot the linear fit (orange line)
ax1.plot(
    dpe_conc, fit_line1,
    color='#ff7f0e', linewidth=2.5,
    label=f'Fit: y = {coeffs1[0]:.3f}x + {coeffs1[1]:.2f}'
)

# Annotate R² value
ax1.text(
    0.05, 0.92, f'$R^2$ = {r2_1:.4f}',
    transform=ax1.transAxes,
    fontsize=11, color='gray',
    bbox=dict(facecolor='white', alpha=0.6, edgecolor='none')
)

# Label and title setup
ax1.set_xlabel('DPE Concentration', fontsize=12)
ax1.set_ylabel('Integration', fontsize=12)
ax1.set_title('Integration vs DPE Concentration w/o additive', fontsize=13, weight='bold')
ax1.tick_params(axis='both', labelsize=10)
ax1.legend(frameon=False, fontsize=10)

# =====================================================================
# Plot 2 — Integration vs TBABr Concentration (NO fitting)
# =====================================================================
# Experimental data: Integration measured at fixed DPE (212 mM)
tbabr_conc = np.array([300, 225, 150, 75, 0])
tbabr_intg = np.array([15.85, 15.65, 16.02, 17.68, 22.48])

# Select right subplot (axes[1])
ax2 = axes[1]

# Plot only scatter points (green markers)
ax2.scatter(
    tbabr_conc, tbabr_intg,
    color='#2ca02c', s=80, edgecolor='white', zorder=3,
    label='Data points'
)

# Optional: connect points with smooth guiding line (no regression)
ax2.plot(
    tbabr_conc, tbabr_intg,
    color='#d62728', linewidth=2.0, linestyle='--', alpha=0.7,
    label='Trend (guide only)'
)

# Label and title setup
ax2.set_xlabel('TBABr Concentration', fontsize=12)
ax2.set_ylabel('Integration', fontsize=12)
ax2.set_title('Integration vs TBABr Concentration (DPE = 212 mM)', fontsize=13, weight='bold')
ax2.tick_params(axis='both', labelsize=10)
ax2.legend(frameon=False, fontsize=10)

# =====================================================================
# Final layout and export
# =====================================================================
plt.tight_layout()  # Adjust spacing between plots
plt.savefig('intg_combined_nofit.png', dpi=300, bbox_inches='tight')  # Save high-res PNG
plt.show()

print("✅ Combined plot saved as 'intg_combined_nofit.png' in the current directory.")
