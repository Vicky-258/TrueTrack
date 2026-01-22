from core.states import PipelineState
from cli.phases import CLIPhase

STATE_TO_PHASE = {
    PipelineState.RESOLVING_IDENTITY: CLIPhase.IDENTIFYING,
    PipelineState.SEARCHING: CLIPhase.IDENTIFYING,
    PipelineState.DOWNLOADING: CLIPhase.DOWNLOADING,
    PipelineState.EXTRACTING: CLIPhase.PROCESSING,
    PipelineState.MATCHING_METADATA: CLIPhase.MATCHING,
    PipelineState.USER_METADATA_SELECTION: CLIPhase.USER_INPUT,
    PipelineState.ARCHIVING: CLIPhase.ARCHIVED,
    PipelineState.STORING: CLIPhase.STORING,
    PipelineState.FINALIZED: CLIPhase.DONE,
}
