from core.pipeline import Pipeline
from core.states import PipelineState
from core.pipeline import (
    handle_init,
    handle_resolving_identity,
    handle_user_intent_selection,
    handle_searching,
    handle_downloading,
    handle_extracting,
    handle_matching_metadata,
    handle_metadata_user_selection,
    handle_tagging,
    handle_storage,
    handle_archiving,
)

def create_pipeline():
    pipeline = Pipeline()

    pipeline.register(PipelineState.INIT, handle_init)
    pipeline.register(PipelineState.RESOLVING_IDENTITY, handle_resolving_identity)
    pipeline.register(PipelineState.USER_INTENT_SELECTION, handle_user_intent_selection)
    pipeline.register(PipelineState.SEARCHING, handle_searching)
    pipeline.register(PipelineState.DOWNLOADING, handle_downloading)
    pipeline.register(PipelineState.EXTRACTING, handle_extracting)
    pipeline.register(PipelineState.MATCHING_METADATA, handle_matching_metadata)
    pipeline.register(PipelineState.USER_METADATA_SELECTION, handle_metadata_user_selection)
    pipeline.register(PipelineState.TAGGING, handle_tagging)
    pipeline.register(PipelineState.STORING, handle_storage)
    pipeline.register(PipelineState.ARCHIVING, handle_archiving)

    return pipeline
