"""Compatibility import seam for the centralized M2 lock planner."""

from netauto.persistence.locking import AdvisoryGate, acquire_advisory_gate

__all__ = ["AdvisoryGate", "acquire_advisory_gate"]
