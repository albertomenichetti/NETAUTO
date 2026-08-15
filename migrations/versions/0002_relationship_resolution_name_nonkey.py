"""make RelationshipResolution name non-key metadata

Revision ID: 0002_resolution_name_nonkey
Revises: 0001_m1_schema
Create Date: 2026-08-15
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_resolution_name_nonkey"
down_revision: str | Sequence[str] | None = "0001_m1_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop the obsolete FK-eligible semantic-child key."""
    op.drop_constraint(
        "uq_relationship_resolutions_semantic_child",
        "relationship_resolutions",
        type_="unique",
    )


def downgrade() -> None:
    """Restore the exact pre-correction semantic-child key."""
    op.create_unique_constraint(
        "uq_relationship_resolutions_semantic_child",
        "relationship_resolutions",
        [
            "relationship_definition_id",
            "from_template_id",
            "to_template_id",
            "name",
        ],
    )
