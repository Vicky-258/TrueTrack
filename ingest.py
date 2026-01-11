from core.job import Job
from core.states import PipelineState
from core.pipeline import (
    Pipeline,
    handle_init,
    handle_searching,
    handle_downloading,
    handle_extracting,
    handle_matching_metadata,
    handle_tagging,
    handle_storage
)

if __name__ == "__main__":
    
    query = input("Enter the song: ")
    
    job = Job(
        raw_query=query,
        normalized_query=query.strip().lower()
    )

    pipeline = Pipeline()
    pipeline.register(PipelineState.INIT, handle_init)
    pipeline.register(PipelineState.SEARCHING, handle_searching)
    pipeline.register(PipelineState.DOWNLOADING, handle_downloading)
    pipeline.register(PipelineState.EXTRACTING, handle_extracting)
    pipeline.register(PipelineState.MATCHING_METADATA, handle_matching_metadata)
    pipeline.register(PipelineState.TAGGING, handle_tagging)
    pipeline.register(PipelineState.STORING, handle_storage)

    pipeline.run(job)

    print(job)
    for record in job.state_history:
        print(record)
