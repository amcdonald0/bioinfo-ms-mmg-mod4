nextflow.enable.dsl=2

params.input_dir = "./mycocosm_annotations"
params.metadata = "./data/mycocosm_its_merge.csv"
params.outdir = "./results"
params.annotation_type = "GO"

workflow {
    Channel
        .from([file(params.input_dir), file(params.metadata), params.annotation_type, params.outdir])
        .set { input_data }

    normalize_annotations(input_data)
}
