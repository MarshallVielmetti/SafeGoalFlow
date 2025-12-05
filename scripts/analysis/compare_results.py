#!/usr/bin/env python3
"""
Compare two result CSVs token-by-token and report tokens where one outperforms the other.
Usage:
    python scripts/analysis/compare_results.py <base.csv> <new.csv> [--metric METRIC] [--higher-is-better]

The script expects both CSVs to contain a `token` column and numeric metric columns.
It will align rows by `token` and compute the difference (new - base) for the chosen metric.
By default, the script treats larger metric values as better; pass --lower-is-better to invert.

Outputs a short report and writes `compare_{metric}.csv` with per-token diffs.
"""
import argparse
import sys
import pandas as pd


def load_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"Failed to read {path}: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", help="Path to base CSV (e.g., without barrier)")
    parser.add_argument("new", help="Path to new CSV (e.g., with barrier)")
    parser.add_argument("--metric", default=None, help="Metric column to compare. If omitted, try to auto-detect.")
    parser.add_argument("--lower-is-better", action="store_true", help="Set if lower metric values are better (e.g., error). By default higher is better.")
    parser.add_argument("--topk", type=int, default=20, help="How many top tokens to list where new>base and base>new")
    args = parser.parse_args()

    df_base = load_csv(args.base)
    df_new = load_csv(args.new)

    if 'token' not in df_base.columns or 'token' not in df_new.columns:
        print("CSV files must contain a 'token' column to align rows.")
        sys.exit(1)

    # Drop any rows that are not 'valid'
    df_base = df_base[df_base['valid'] == True]
    df_new = df_new[df_new['valid'] == True]

    # Align on tokes; one n
    df = pd.merge(df_base, df_new, on='token', how='inner', suffixes=("_base", "_new"))
    print(f"Aligned {len(df)} tokens present in both files.")

    # Determine metric
    metric = args.metric
    if metric is None:
        # pick a numeric column common to both besides token
        candidates = [c[:-5] for c in df.columns if c.endswith('_base')]
        # remove token_base if present
        candidates = [c for c in candidates if c != 'token']
        if not candidates:
            print("No candidate metric columns found. Please pass --metric.")
            print('Columns in merged file:', df.columns.tolist())
            sys.exit(1)
        metric = candidates[0]
        print(f"Auto-selected metric: {metric}")

    base_col = metric + '_base'
    new_col = metric + '_new'
    if base_col not in df.columns or new_col not in df.columns:
        print(f"Metric columns {base_col} or {new_col} not found in merged CSV. Columns: {df.columns.tolist()}")
        sys.exit(1)

    # Ensure numeric
    df[base_col] = pd.to_numeric(df[base_col], errors='coerce')
    df[new_col] = pd.to_numeric(df[new_col], errors='coerce')

    df = df.dropna(subset=[base_col, new_col]).copy()
    df['diff'] = df[new_col] - df[base_col]
    if args.lower_is_better:
        # For lower-is-better metrics, invert sign so positive diff means new is better
        df['diff'] = -df['diff']

    better_new = df[df['diff'] > 0].sort_values('diff', ascending=False)
    better_base = df[df['diff'] < 0].sort_values('diff')
    no_change = df[df['diff'] == 0]

    # Summary statistics
    print('\n' + '='*60)
    print('SUMMARY STATISTICS')
    print('='*60)
    
    print(f"\nTotal tokens compared: {len(df)}")
    print(f"  - NEW better than BASE: {len(better_new)} ({100*len(better_new)/len(df):.1f}%)")
    print(f"  - BASE better than NEW: {len(better_base)} ({100*len(better_base)/len(df):.1f}%)")
    print(f"  - No change:            {len(no_change)} ({100*len(no_change)/len(df):.1f}%)")
    
    print(f"\nMetric: {metric}")
    print(f"  BASE mean: {df[base_col].mean():.4f} (std: {df[base_col].std():.4f})")
    print(f"  NEW mean:  {df[new_col].mean():.4f} (std: {df[new_col].std():.4f})")
    print(f"  Diff mean: {df['diff'].mean():.4f} (std: {df['diff'].std():.4f})")
    
    if len(better_new) > 0:
        print(f"\nWhen NEW > BASE ({len(better_new)} tokens):")
        print(f"  Avg improvement: {better_new['diff'].mean():.4f}")
        print(f"  Max improvement: {better_new['diff'].max():.4f}")
        print(f"  Min improvement: {better_new['diff'].min():.4f}")
    
    if len(better_base) > 0:
        print(f"\nWhen BASE > NEW ({len(better_base)} tokens):")
        print(f"  Avg regression:  {better_base['diff'].mean():.4f}")
        print(f"  Max regression:  {better_base['diff'].min():.4f}")
        print(f"  Min regression:  {better_base['diff'].max():.4f}")
    
    print('\n' + '='*60)

    print('\nTop tokens where NEW > BASE:')
    print(better_new[['token', base_col, new_col, 'diff']].head(args.topk).to_string(index=False))

    print('\nTop tokens where BASE > NEW:')
    print(better_base[['token', base_col, new_col, 'diff']].head(args.topk).to_string(index=False))

    out_csv = f"compare_{metric}.csv"
    df[['token', base_col, new_col, 'diff']].to_csv(out_csv, index=False)
    print(f"Wrote per-token diffs to {out_csv}")


if __name__ == '__main__':
    main()
