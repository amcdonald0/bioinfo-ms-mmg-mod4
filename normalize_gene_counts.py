import os
import argparse
import pandas as pd
from pathlib import Path

# Map known annotation types to their key column
ANNOTATION_TYPES = {
    "GO": "goAcc",
    "KEGG": "ecNum",
    "InterPro": "iprId",
    "KOG": "kogid",
    "Signalp": "proteinid"
}

def detect_annotation_type(annotation_dir):
    for file in os.listdir(annotation_dir):
        for ann_type, key in ANNOTATION_TYPES.items():
            if ann_type.lower() in file.lower():
                return ann_type
    raise ValueError("Could not detect annotation type from file names.")

def is_empty_file(filepath):
    try:
        df = pd.read_csv(filepath, sep='\t')
        return df.empty
    except Exception:
        return True

def extract_portal_name(filename):
    parts = filename.split("_")
    for i, part in enumerate(parts):
        if part in {"GeneCatalog", "filtered", "KEGG.tab", "FilteredModels1"}:
            return "_".join(parts[:i]) if i > 2 else parts[0]
    return parts[0]

def remove_duplicate_files(file_list):
    portals = [extract_portal_name(f) for f in file_list]
    df = pd.DataFrame({'file': file_list, 'portal': portals})
    df['date'] = df['file'].apply(lambda x: x.split("_")[-2] if len(x.split("_")) > 2 else "0000")
    keep_files = []

    for portal in df['portal'].unique():
        subset = df[df['portal'] == portal]
        latest = subset.loc[subset['date'].astype(str).idxmax()]
        keep_files.append(latest['file'])

    return keep_files

def get_gene_id_table(filepath, annotation_type):
    col = ANNOTATION_TYPES[annotation_type]
    try:
        skip = 1 if annotation_type == "Signalp" else 0
        df = pd.read_csv(filepath, sep='\t', skiprows=skip)
        return pd.DataFrame({col: df[col].dropna().unique()})
    except:
        return pd.DataFrame(columns=[col])

def get_gene_counts(filepath, gene_names, annotation_type):
    col = ANNOTATION_TYPES[annotation_type]
    skip = 1 if annotation_type == "Signalp" else 0
    df = pd.read_csv(filepath, sep='\t', skiprows=skip)
    df["numHits"] = 1
    agg = df.groupby(col)["numHits"].sum().reset_index()
    portal = extract_portal_name(Path(filepath).name)
    agg.columns = ["gene_id", portal]
    merged = gene_names.merge(agg, how='left', left_on=col, right_on="gene_id").drop(columns=["gene_id"])
    return merged.rename(columns={col: "gene_id"})

def combine_counts(list_of_dfs):
    result = list_of_dfs[0].copy()
    for df in list_of_dfs[1:]:
        result = result.merge(df, on="gene_id", how="outer")
    return result

def normalize_counts(df):
    return df.div(df.sum(axis=0), axis=1) * 10000

def average_taxa(df, metadata, group_by):
    merged = df.T.merge(metadata[[group_by, "portal"]], left_index=True, right_on="portal", how="left")
    grouped = merged.groupby(group_by).mean().T
    return grouped

def main(annotation_dir, metadata_path, output_dir, annotation_type=None):
    os.makedirs(output_dir, exist_ok=True)
    if not annotation_type:
        annotation_type = detect_annotation_type(annotation_dir)

    all_files = list(Path(annotation_dir).glob("*.tab"))
    valid_files = [str(f) for f in all_files if not is_empty_file(f)]
    deduped_files = remove_duplicate_files(valid_files)

    # Gene list
    gene_name_col = ANNOTATION_TYPES[annotation_type]
    gene_lists = [get_gene_id_table(f, annotation_type) for f in deduped_files]
    all_gene_ids = pd.concat(gene_lists).drop_duplicates()
    all_gene_ids.columns = [gene_name_col]

    # Count matrix
    count_tables = [get_gene_counts(f, all_gene_ids, annotation_type) for f in deduped_files]
    count_matrix = combine_counts(count_tables).fillna(0)
    count_matrix.to_csv(f"{output_dir}/{annotation_type}_annotations_count_table.csv", index=False)

    # Normalize
    norm_matrix = count_matrix.set_index("gene_id")
    norm_matrix = normalize_counts(norm_matrix)
    norm_matrix.to_csv(f"{output_dir}/{annotation_type}_annotations_count_table_norm.csv")

    # Add genus/species info
    metadata = pd.read_csv(metadata_path)
    metadata['species'] = metadata['species'].str.replace(" ", "_")
    gene_count_t = norm_matrix.T
    gene_count_t['Genus'] = gene_count_t.index.map(lambda x: metadata.loc[metadata['portal'] == x, 'genus'].values[0] if x in metadata['portal'].values else None)
    gene_count_t['Species'] = gene_count_t.index.map(lambda x: metadata.loc[metadata['portal'] == x, 'species'].values[0] if x in metadata['portal'].values else None)

    # Averages
    avg_species = average_taxa(gene_count_t, metadata, "Species")
    avg_genus = average_taxa(gene_count_t, metadata, "Genus")
    avg_species.to_csv(f"{output_dir}/{annotation_type}_average_bySpecies.csv")
    avg_genus.to_csv(f"{output_dir}/{annotation_type}_average_byGenus.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotation_dir", required=True)
    parser.add_argument("--metadata_path", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--annotation_type", required=False, choices=ANNOTATION_TYPES.keys())
    args = parser.parse_args()
    main(args.annotation_dir, args.metadata_path, args.output_dir, args.annotation_type)
