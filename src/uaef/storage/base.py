# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Pluggable storage backend abstraction for UAEF.

``StorageBackend`` defines the contract the public API (``uaef.api``) needs
from a persistence layer. The built-in implementation is
:class:`uaef.storage.dynamodb_s3.DynamoS3Storage`; alternative backends (e.g.
a local filesystem store for offline development) only need to implement
this ABC and be injected via ``uaef.api.set_store``.

Method signatures intentionally mirror the existing ``DynamoS3Storage``
implementation so the DynamoDB+S3 backend satisfies the ABC without changes.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageBackend(ABC):
    """Abstract interface for experiment persistence backends."""

    @abstractmethod
    def save_experiment(
        self,
        experiment_id: str,
        experiment_name: str,
        evaluation_results: List[Dict[str, Any]],
        experiment_objective: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save or update an experiment with its evaluation results.

        Returns:
            The persisted experiment record (backend-specific dict).
        """

    @abstractmethod
    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment metadata by ID, or None if not found."""

    @abstractmethod
    def get_experiment_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find an experiment by name, or None if not found."""

    @abstractmethod
    def get_full_results(self, experiment_id: str) -> Dict[str, Any]:
        """Get the full evaluation results (including all evaluations)."""

    @abstractmethod
    def list_experiments(self, created_by: Optional[str] = None) -> List[Dict[str, Any]]:
        """List experiments, optionally scoped to an owner (``created_by``)."""

    @abstractmethod
    def delete_experiment(self, experiment_id: str) -> None:
        """Delete an experiment and its full results."""

    # ------------------------------------------------------------------
    # Provisioning (optional)
    # ------------------------------------------------------------------

    def create_table_if_not_exists(self) -> None:
        """Provision the metadata store if needed. Default: no-op."""

    def create_bucket_if_not_exists(self) -> None:
        """Provision the results store if needed. Default: no-op."""
