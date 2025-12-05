#!/bin/bash
#
# Generate comparison figures for baseline vs barrier-function trajectories
#

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================

# Token IDs to visualize
# TOKENS=(
#     "0a4cf95e90d45770"
#     "0a7ed373b7de5037"
#     "f51a75fadd695f06"
#     "64a417561b53530f"
#     "69966a921d43544d"
# )
TOKENS=(
    "6507522e38405857"
    "b133316a0e795993"
    "de49d859c60758e9"
    "114f66c4cf785eab"
    "bf72d4d6b25f5b27"
    "ea9f070b56115301"
)

# Paths
DATA_PATH="dataset/navsim_logs/test"
SENSOR_BLOBS="dataset/sensor_blobs/test"
OUTPUT_DIR="./my_assets"

# Trajectory directories
BASELINE_TRAJS="/home/mvielmet/Documents/GoalFlow/exp/a_test_release/2025.12.04.12.04.20/lightning_logs/version_0/trajs"
# BARRIER_TRAJS="/home/mvielmet/Documents/GoalFlow/exp/a_test_release/2025.12.04.16.01.12/lightning_logs/version_0/trajs"
# BARRIER_TRAJS="/home/mvielmet/Documents/GoalFlow/exp/a_test_release/2025.12.04.18.15.58/lightning_logs/version_0/trajs"
BARRIER_TRAJS="/home/mvielmet/Documents/GoalFlow/exp/a_test_release/2025.12.04.18.40.29/lightning_logs/version_0/trajs"

# ============================================================================
# Helper functions
# ============================================================================

print_header() {
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

print_status() {
    echo "  [✓] $1"
}

print_progress() {
    echo "  → $1"
}

# ============================================================================
# Main
# ============================================================================

print_header "Generating Comparison Figures"
echo "  Tokens to process: ${#TOKENS[@]}"
echo "  Output directory:  ${OUTPUT_DIR}"

# Create output directory if needed
mkdir -p "${OUTPUT_DIR}"

# --- Baseline figures ---
print_header "Generating BASELINE figures"

# for i in "${!TOKENS[@]}"; do
#     token="${TOKENS[$i]}"
#     fig_num=$((i + 1))
#     out_file="${OUTPUT_DIR}/fig_${fig_num}.png"
    
#     print_progress "Token ${token} → ${out_file}"
    
#     python scripts/visualize/plot_token.py \
#         --token "${token}" \
#         --data-path "${DATA_PATH}" \
#         --sensor-blobs "${SENSOR_BLOBS}" \
#         --trajs-dir "${BASELINE_TRAJS}" \
#         --out "${out_file}"
    
#     print_status "Created ${out_file}"
# done

# --- Barrier function figures ---
print_header "Generating BARRIER FUNCTION (BF) figures"

# for i in "${!TOKENS[@]}"; do
#     token="${TOKENS[$i]}"
#     fig_num=$((i + 1))
#     out_file="${OUTPUT_DIR}/fig_${fig_num}_bf.png"
    
#     print_progress "Token ${token} → ${out_file}"
    
#     python scripts/visualize/plot_token.py \
#         --token "${token}" \
#         --data-path "${DATA_PATH}" \
#         --sensor-blobs "${SENSOR_BLOBS}" \
#         --trajs-dir "${BARRIER_TRAJS}" \
#         --out "${out_file}"
    
#     print_status "Created ${out_file}"
# done

# --- Summary ---
print_header "Done!"

# --- Double figures (both trajectories on same plot) ---
print_header "Generating COMBINED figures (both trajectories)"

for i in "${!TOKENS[@]}"; do
    token="${TOKENS[$i]}"
    fig_num=$((i + 1))
    out_file="${OUTPUT_DIR}/fig_${fig_num}_combined.png"
    
    print_progress "Token ${token} → ${out_file}"
    
    python scripts/visualize/plot_token.py \
        --token "${token}" \
        --data-path "${DATA_PATH}" \
        --sensor-blobs "${SENSOR_BLOBS}" \
        --trajs-dir "${BASELINE_TRAJS}" \
        --trajs-dir2 "${BARRIER_TRAJS}" \
        --out "${out_file}"
    
    print_status "Created ${out_file}"
done

# --- Final Summary ---
print_header "All Done!"

echo "  Generated $((${#TOKENS[@]} * 3)) figures in ${OUTPUT_DIR}"
echo "    - ${#TOKENS[@]} baseline figures"
echo "    - ${#TOKENS[@]} barrier function figures"
echo "    - ${#TOKENS[@]} combined figures"
echo ""
ls -la "${OUTPUT_DIR}"/*.png 2>/dev/null | tail -20
echo ""
