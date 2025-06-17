nextflow.enable.dsl=2
include { NORMALIZE_ANNOTATIONS } from './modules/normalize_annotations/main'

params.input_dir = "./mycocosm_annotations"
params.metadata = "./data/mycocosm_its_merge.csv"
params.outdir = "./results"
params.annotation_type = "KEGG"

workflow {
    Channel
        .from([":sample1", params.input_dir, params.metadata, params.annotation_type, params.outdir])
        .set { input_data }

    NORMALIZE_ANNOTATIONS(input_data)
}
