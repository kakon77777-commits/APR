from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _distribution_version

from .adapters import BaseAdapter, ObservationSpec, SimulatorAdapter
from .evidence import EvidenceStore
from .models import (
    Budget,
    Evidence,
    FactState,
    FactStatus,
    Goal,
    Modality,
    PerceptualAction,
    ReadingMode,
)
from .policy import ChannelProfile, PolicyController
from .runtime import APRRuntime
from .world_state import WorldState

try:
    __version__ = _distribution_version("apr-runtime-mvp")
except _PackageNotFoundError:
    __version__ = "0.10.0"


# v0.2 real-stream components
# v0.8 action readiness gates + evidence preconditions
from .action_gate import (
    ActionDecision,
    ActionDecisionKind,
    ActionGatePolicy,
    ActionReadinessGate,
    ActionSpec,
    EvidenceSummary,
    FactRequirement,
    PreconditionAssessment,
    PreconditionState,
)
from .action_runtime import (
    ActionExecutionResult,
    ActionReadinessRuntime,
)
from .archive import EvidenceArchive
from .browser import (
    BrowserSnapshot,
    BrowserSource,
    PlaywrightCDPBrowserSource,
)
from .browser_adapter import BrowserStructuredAdapter
from .browser_events import BrowserCDPEventSource, BrowserEventConfig
from .browser_stream import BrowserStreamConfig, BrowserStreamMonitor
from .browser_targeted import BrowserSubtreeResult, TargetedBrowserReader
from .desktop_adapters import DesktopStructuredAdapter
from .event_fact_router import (
    EventFactDependencyMap,
    EventFactRule,
    TaskAwareEventRouter,
    TaskAwareRoute,
    TaskAwareRoutingConfig,
)

# v0.5 event-native + targeted subtree
from .event_ledger import EventLedger, NativeEvent
from .event_runtime import EventNativeRuntime, VerifiedEvent
from .execution_ledger import ExecutionLedger, ExecutionReceipt
from .executor import (
    AsyncEventExecutor,
    AsyncSchedulerRuntime,
    EventHandlerRegistry,
    ExecutionResult,
)
from .frame_delta import FrameDelta, FrameDeltaDetector
from .hosted_semantic import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_OPENAI_MODEL,
    AnthropicMessagesSemanticInspector,
    HostedSemanticError,
    HostedSemanticInspectorsPlugin,
    OpenAIResponsesSemanticInspector,
)
from .image_generation import ImageGenerationResult, ImageGenerator

# v0.3 semantic evidence layer
from .image_ops import (
    clamp_bbox,
    crop_frame,
    frame_to_png_bytes,
    pad_bbox,
    save_frame_png,
)

# v0.7 perceptual need graph + task-aware routing
from .need_graph import (
    NeedAssessment,
    NeedState,
    PerceptualNeed,
    PerceptualNeedGraph,
)
from .need_refresh import NeedRefreshConfig, NeedRefreshPlanner
from .orchestrator import IngestReport, UnifiedEventRuntime

# v0.9 action outcome verification + recovery
from .outcome import (
    ActionOutcomeSpec,
    ActionOutcomeVerifier,
    OutcomeDecision,
    OutcomeDecisionKind,
    PostconditionAssessment,
    PostconditionRequirement,
    PostconditionState,
)
from .outcome_runtime import ActionOutcomeRuntime, OutcomeExecutionResult
from .plugins import (
    PLUGIN_ENTRY_POINT_GROUP,
    APRPlugin,
    DuplicateComponentError,
    LoadedPlugin,
    PluginError,
    PluginFailure,
    PluginLoadError,
    PluginLoadReport,
    PluginRegistry,
)
from .query_router import (
    PerceptualQuery,
    QueryDecision,
    QueryDecisionKind,
    QueryRouter,
    QueryScope,
)

# v0.10 closed-loop recovery orchestrator
from .recovery_orchestrator import (
    ClosedLoopRecoveryOrchestrator,
    ExecutionCancelled,
    ExecutionDeadlineExceeded,
    PartialSuccessPolicy,
    RecoveryContext,
    RecoveryPolicy,
    RecoveryRunResult,
    RecoveryRunStatus,
    RecoveryTrace,
    RecoveryTraceStep,
    RetryMode,
    ReversibilityClass,
)
from .retention import RetentionManager, RetentionPolicy, RetentionReport

# v0.4 historical revisit + browser native state
from .revisit import HistoricalRevisitRecord, HistoricalRevisitService

# v0.6 unified scheduling / backpressure / retention
from .scheduler import (
    RefreshSpec,
    ScheduledEvent,
    SchedulerConfig,
    SchedulerMetrics,
    UnifiedEventScheduler,
)
from .semantic import (
    CallableSemanticInspector,
    CommandSemanticInspector,
    RuleSemanticInspector,
    SemanticFact,
    SemanticInspector,
    SemanticResult,
)
from .semantic_pipeline import (
    SemanticEvidencePipeline,
    SemanticInspectionRecord,
    SemanticPipelineConfig,
)
from .semantic_stream import (
    SemanticStreamConfig,
    SemanticStreamRuntime,
)
from .sources import (
    ForegroundWindowSnapshot,
    MSSScreenSource,
    PywinautoUIAutomationSource,
    ScreenFrame,
    SourceUnavailable,
    UIAutomationSnapshot,
    UIElementRecord,
    Win32ForegroundWindowSource,
)
from .stream import RealStreamConfig, RealStreamMonitor, StreamEvent
from .task_runtime import TaskAwareIngestReport, TaskAwarePerceptionRuntime
from .uia_targeted import PywinautoTargetedUIAReader, UIASubtreeResult
from .vertex_image import (
    DEFAULT_VERTEX_IMAGE_MODEL,
    DEFAULT_VERTEX_LOCATION,
    GoogleVertexImageGenerationPlugin,
    GoogleVertexImageGenerator,
    VertexImageGenerationError,
)
from .win_events import Win32NativeEventSource, WinEventConfig

__all__ = [
    "PLUGIN_ENTRY_POINT_GROUP",
    "APRPlugin",
    "APRRuntime",
    "ActionDecision",
    "ActionDecisionKind",
    "ActionExecutionResult",
    "ActionGatePolicy",
    "ActionOutcomeRuntime",
    "ActionOutcomeSpec",
    "ActionOutcomeVerifier",
    "ActionReadinessGate",
    "ActionReadinessRuntime",
    "ActionSpec",
    "AsyncEventExecutor",
    "AsyncSchedulerRuntime",
    "BaseAdapter",
    "BrowserCDPEventSource",
    "BrowserEventConfig",
    "BrowserSnapshot",
    "BrowserSource",
    "BrowserStreamConfig",
    "BrowserStreamMonitor",
    "BrowserStructuredAdapter",
    "BrowserSubtreeResult",
    "Budget",
    "CallableSemanticInspector",
    "ChannelProfile",
    "ClosedLoopRecoveryOrchestrator",
    "CommandSemanticInspector",
    "DesktopStructuredAdapter",
    "DuplicateComponentError",
    "EventFactDependencyMap",
    "EventFactRule",
    "EventHandlerRegistry",
    "EventLedger",
    "EventNativeRuntime",
    "Evidence",
    "EvidenceArchive",
    "EvidenceStore",
    "EvidenceSummary",
    "ExecutionCancelled",
    "ExecutionDeadlineExceeded",
    "ExecutionLedger",
    "ExecutionReceipt",
    "ExecutionResult",
    "FactRequirement",
    "FactState",
    "FactStatus",
    "ForegroundWindowSnapshot",
    "FrameDelta",
    "FrameDeltaDetector",
    "Goal",
    "GoogleVertexImageGenerationPlugin",
    "GoogleVertexImageGenerator",
    "HistoricalRevisitRecord",
    "HistoricalRevisitService",
    "HostedSemanticError",
    "HostedSemanticInspectorsPlugin",
    "IngestReport",
    "ImageGenerationResult",
    "ImageGenerator",
    "LoadedPlugin",
    "MSSScreenSource",
    "Modality",
    "NativeEvent",
    "NeedAssessment",
    "NeedRefreshConfig",
    "NeedRefreshPlanner",
    "NeedState",
    "ObservationSpec",
    "OpenAIResponsesSemanticInspector",
    "OutcomeDecision",
    "OutcomeDecisionKind",
    "OutcomeExecutionResult",
    "PartialSuccessPolicy",
    "PerceptualAction",
    "PerceptualNeed",
    "PerceptualNeedGraph",
    "PerceptualQuery",
    "PlaywrightCDPBrowserSource",
    "PluginError",
    "PluginFailure",
    "PluginLoadError",
    "PluginLoadReport",
    "PluginRegistry",
    "PolicyController",
    "PostconditionAssessment",
    "PostconditionRequirement",
    "PostconditionState",
    "PreconditionAssessment",
    "PreconditionState",
    "PywinautoTargetedUIAReader",
    "PywinautoUIAutomationSource",
    "QueryDecision",
    "QueryDecisionKind",
    "QueryRouter",
    "QueryScope",
    "ReadingMode",
    "RealStreamConfig",
    "RealStreamMonitor",
    "RecoveryContext",
    "RecoveryPolicy",
    "RecoveryRunResult",
    "RecoveryRunStatus",
    "RecoveryTrace",
    "RecoveryTraceStep",
    "RefreshSpec",
    "RetentionManager",
    "RetentionPolicy",
    "RetentionReport",
    "RetryMode",
    "ReversibilityClass",
    "RuleSemanticInspector",
    "ScheduledEvent",
    "SchedulerConfig",
    "SchedulerMetrics",
    "ScreenFrame",
    "SemanticEvidencePipeline",
    "SemanticFact",
    "SemanticInspectionRecord",
    "SemanticInspector",
    "SemanticPipelineConfig",
    "SemanticResult",
    "SemanticStreamConfig",
    "SemanticStreamRuntime",
    "SimulatorAdapter",
    "SourceUnavailable",
    "StreamEvent",
    "TargetedBrowserReader",
    "TaskAwareEventRouter",
    "TaskAwareIngestReport",
    "TaskAwarePerceptionRuntime",
    "TaskAwareRoute",
    "TaskAwareRoutingConfig",
    "UIASubtreeResult",
    "UIAutomationSnapshot",
    "UIElementRecord",
    "UnifiedEventRuntime",
    "UnifiedEventScheduler",
    "VerifiedEvent",
    "VertexImageGenerationError",
    "Win32ForegroundWindowSource",
    "Win32NativeEventSource",
    "WinEventConfig",
    "WorldState",
    "AnthropicMessagesSemanticInspector",
    "DEFAULT_ANTHROPIC_MODEL",
    "DEFAULT_OPENAI_MODEL",
    "DEFAULT_VERTEX_IMAGE_MODEL",
    "DEFAULT_VERTEX_LOCATION",
    "__version__",
    "clamp_bbox",
    "crop_frame",
    "frame_to_png_bytes",
    "pad_bbox",
    "save_frame_png",
]
