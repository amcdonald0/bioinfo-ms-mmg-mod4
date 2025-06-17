#!/bin/bash

# Activate Conda environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate annot_env

# Set variables 
 ### raw annotation '.tab' files needed --> 
 ### used "unzip bulk_data_306143-2.zip -d extracted_annotation" to extract annotations
ANNOTATION_DIR="extracted_annotations"
METADATA_PATH="data/mycocosm_its_merge.csv"
OUTPUT_DIR="data"
ANNOTATION_TYPE="KEGG"

# Run the script
echo "Running annotation normalization for ${ANNOTATION_TYPE}..."
python normalize_gene_counts.py \
    --annotation_dir "$ANNOTATION_DIR" \
    --metadata_path "$METADATA_PATH" \
    --output_dir "$OUTPUT_DIR" \
    --annotation_type "$ANNOTATION_TYPE"

#### normalize_gene_counts updated to 1. detect annotation (remove last line) or 2. explicitly set annotation type (keep lat line)

echo "Done."
