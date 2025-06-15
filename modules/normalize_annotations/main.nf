#!/usr/bin/env nextflow

process NORMALIZE_ANNOTATIONS {
    label 'process_single'
    conda 'envs/annot_env.yml'
    cache 'lenient'
    
    input:
    tuplel val(meta), path(annotation_dir), path(metadata_file), val(annotation_type), val(output_dir)

    output:
    tuple val(meta), path("${output_dir}"), emit: results

    shell:
    """

    python normalize_gene_counts.py \
    --annotation_dir ${annotation_dir} \
    --metadata_path ${metadata_file} \
    --output_dir ${output_dir} \
    --annotation_type ${annotation_type}
    
    """
}