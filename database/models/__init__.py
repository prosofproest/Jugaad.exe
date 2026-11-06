"""
CropSentinel AI — Master Database SQLAlchemy Models
Aggregates all 11 database domains and 76 core tables.
"""

from database.models.base import (
    Base,
    PortableUUID,
    PostGISGeometry,
    SoftDeleteMixin,
    TimestampMixin,
    VectorType,
    generate_uuid_str,
    utc_now,
)

# 1. User Database
from database.models.user import (
    User,
    UserPermission,
    UserPreference,
    UserProfile,
    UserRole,
    UserSession,
)

# 2. Farm Database
from database.models.farm import (
    Farm,
    FarmBoundary,
    FarmLocation,
    FarmMember,
    FarmPlot,
    FarmSection,
)

# 3. Crop and Plant Database
from database.models.crop import (
    CropGrowthStage,
    CropGroup,
    CropInstance,
    CropType,
    Plant,
    PlantObservation,
    PlantingRecord,
)

# 4. Media Database
from database.models.media import (
    MediaAnalysisLink,
    MediaFile,
    MediaFrame,
    MediaLocation,
    MediaObservation,
)

# 5. Pest and Disease Database
from database.models.pest_disease import (
    CropSymptom,
    Disease,
    DiseaseSymptom,
    Pest,
    PestCategory,
    PestDamageRecord,
    PestHostCrop,
    PestLifeCycle,
)

# 6. AI Analysis Database
from database.models.ai_analysis import (
    AIAnalysis,
    AIConfidence,
    AIDetection,
    AIFeedback,
    AIModelVersion,
    AIPrediction,
    DiagnosisRecord,
)

# 7. Pest Management Database
from database.models.pest_management import (
    BehavioralControl,
    BiologicalControl,
    ChemicalControl,
    CulturalControl,
    IPMMethod,
    MechanicalControl,
    PestControlOption,
    PesticideRegistration,
    PhysicalControl,
    TreatmentEffectiveness,
    TreatmentRecord,
)

# 8. Hotspot and Outbreak Database
from database.models.hotspot import (
    HotspotRegion,
    MonitoringCoverage,
    OutbreakPrediction,
    PestReport,
    RegionalPestStatistic,
    RiskHistory,
    SpreadObservation,
    VerifiedCase,
)

# 9. Recovery and Inspection Database
from database.models.recovery import (
    InfestationHistory,
    Inspection,
    InspectionAssignment,
    RecoveryComparison,
    RecoveryRecord,
    ScoutingRecord,
    SeasonalHistory,
)

# 10. Chatbot and Knowledge Database
from database.models.chatbot import (
    ChatbotFeedback,
    ChatMessage,
    ChatSession,
    KnowledgeArticle,
    KnowledgeChunk,
    KnowledgeEmbedding,
)

# 11. Notification Database
from database.models.notification import (
    AlertRule,
    Notification,
    ScheduledTask,
    SyncLog,
    UserAlertPreference,
)

__all__ = [
    # Base
    "Base",
    "PortableUUID",
    "PostGISGeometry",
    "VectorType",
    "TimestampMixin",
    "SoftDeleteMixin",
    "utc_now",
    "generate_uuid_str",
    # 1. User
    "User",
    "UserRole",
    "UserProfile",
    "UserPermission",
    "UserSession",
    "UserPreference",
    # 2. Farm
    "Farm",
    "FarmBoundary",
    "FarmSection",
    "FarmPlot",
    "FarmLocation",
    "FarmMember",
    # 3. Crop and Plant
    "CropType",
    "CropGroup",
    "CropInstance",
    "Plant",
    "PlantObservation",
    "CropGrowthStage",
    "PlantingRecord",
    # 4. Media
    "MediaFile",
    "MediaFrame",
    "MediaObservation",
    "MediaLocation",
    "MediaAnalysisLink",
    # 5. Pest and Disease
    "Pest",
    "PestCategory",
    "PestLifeCycle",
    "PestHostCrop",
    "Disease",
    "DiseaseSymptom",
    "CropSymptom",
    "PestDamageRecord",
    # 6. AI Analysis
    "AIAnalysis",
    "AIPrediction",
    "AIDetection",
    "AIConfidence",
    "AIModelVersion",
    "AIFeedback",
    "DiagnosisRecord",
    # 7. Pest Management
    "IPMMethod",
    "PestControlOption",
    "BiologicalControl",
    "MechanicalControl",
    "CulturalControl",
    "PhysicalControl",
    "BehavioralControl",
    "ChemicalControl",
    "PesticideRegistration",
    "TreatmentRecord",
    "TreatmentEffectiveness",
    # 8. Hotspot and Outbreak
    "PestReport",
    "VerifiedCase",
    "HotspotRegion",
    "RegionalPestStatistic",
    "OutbreakPrediction",
    "SpreadObservation",
    "RiskHistory",
    "MonitoringCoverage",
    # 9. Recovery and Inspection
    "Inspection",
    "InspectionAssignment",
    "ScoutingRecord",
    "RecoveryRecord",
    "RecoveryComparison",
    "SeasonalHistory",
    "InfestationHistory",
    # 10. Chatbot and Knowledge
    "ChatSession",
    "ChatMessage",
    "KnowledgeArticle",
    "KnowledgeChunk",
    "KnowledgeEmbedding",
    "ChatbotFeedback",
    # 11. Notification
    "Notification",
    "AlertRule",
    "UserAlertPreference",
    "ScheduledTask",
    "SyncLog",
]

