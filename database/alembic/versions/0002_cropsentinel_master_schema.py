"""Complete Master Schema across 11 domains (76 tables)

Revision ID: 0002_cropsentinel_master_schema
Revises: 0001_initial_schema
Create Date: 2026-11-06 18:00:00.000000

Implements the complete CropSentinel AI database:
  1. User Database (users, user_roles, user_profiles, user_permissions, user_sessions, user_preferences)
  2. Farm Database (farms, farm_boundaries, farm_sections, farm_plots, farm_locations, farm_members)
  3. Crop and Plant Database (crop_types, crop_groups, crop_instances, plants, plant_observations, crop_growth_stages, planting_records)
  4. Media Database (media_files, media_frames, media_observations, media_locations, media_analysis_links)
  5. Pest and Disease Database (pests, pest_categories, pest_life_cycles, pest_host_crops, diseases, disease_symptoms, crop_symptoms, pest_damage_records)
  6. AI Analysis Database (ai_analysis, ai_predictions, ai_detections, ai_confidence, ai_model_versions, ai_feedback, diagnosis_records)
  7. Pest Management Database (ipm_methods, pest_control_options, biological_controls, mechanical_controls, cultural_controls, physical_controls, behavioral_controls, chemical_controls, pesticide_registrations, treatment_records, treatment_effectiveness)
  8. Hotspot and Outbreak Database (pest_reports, verified_cases, hotspot_regions, regional_pest_statistics, outbreak_predictions, spread_observations, risk_history, monitoring_coverage)
  9. Recovery and Inspection Database (inspections, inspection_assignments, scouting_records, recovery_records, recovery_comparisons, seasonal_history, infestation_history)
  10. Chatbot and Knowledge Database (chat_sessions, chat_messages, knowledge_articles, knowledge_chunks, knowledge_embeddings, chatbot_feedback)
  11. Notification Database (notifications, alert_rules, user_alert_preferences, scheduled_tasks, sync_logs)
"""
from typing import Sequence, Union
import os
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_cropsentinel_master_schema"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    schema_sql_path = os.path.join(base_dir, "schema", "03-cropsentinel-master-schema.sql")

    if not os.path.exists(schema_sql_path):
        schema_sql_path = os.path.join("database", "schema", "03-cropsentinel-master-schema.sql")

    with open(schema_sql_path, "r", encoding="utf-8") as f:
        ddl = f.read()

    op.execute(sa.text(ddl))


def downgrade() -> None:
    tables = [
        # Notification
        "sync_logs",
        "scheduled_tasks",
        "user_alert_preferences",
        "alert_rules",
        "notifications",
        # Chatbot
        "chatbot_feedback",
        "knowledge_embeddings",
        "knowledge_chunks",
        "knowledge_articles",
        "chat_messages",
        "chat_sessions",
        # Recovery
        "infestation_history",
        "seasonal_history",
        "recovery_comparisons",
        "recovery_records",
        "scouting_records",
        "inspection_assignments",
        "inspections",
        # Hotspot
        "monitoring_coverage",
        "risk_history",
        "spread_observations",
        "outbreak_predictions",
        "regional_pest_statistics",
        "hotspot_regions",
        "verified_cases",
        "pest_reports",
        # Pest Management
        "treatment_effectiveness",
        "treatment_records",
        "pesticide_registrations",
        "chemical_controls",
        "behavioral_controls",
        "physical_controls",
        "cultural_controls",
        "mechanical_controls",
        "biological_controls",
        "pest_control_options",
        "ipm_methods",
        # AI Analysis
        "ai_feedback",
        "diagnosis_records",
        "ai_confidence",
        "ai_detections",
        "ai_predictions",
        "media_analysis_links",
        "ai_analysis",
        "ai_model_versions",
        # Pest and Disease
        "pest_damage_records",
        "crop_symptoms",
        "disease_symptoms",
        "diseases",
        "pest_host_crops",
        "pest_life_cycles",
        "pests",
        "pest_categories",
        # Media
        "media_locations",
        "media_observations",
        "media_frames",
        "media_files",
        # Crop
        "planting_records",
        "plant_observations",
        "plants",
        "crop_instances",
        "crop_growth_stages",
        "crop_types",
        "crop_groups",
        # Farm
        "farm_members",
        "farm_locations",
        "farm_plots",
        "farm_sections",
        "farm_boundaries",
        "farms",
        # User
        "user_preferences",
        "user_sessions",
        "user_permissions",
        "user_profiles",
    ]

    for table in tables:
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table} CASCADE;"))

