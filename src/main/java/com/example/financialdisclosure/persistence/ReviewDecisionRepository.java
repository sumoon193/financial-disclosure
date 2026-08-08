package com.example.financialdisclosure.persistence;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ReviewDecisionRepository extends JpaRepository<ReviewDecisionEntity, String> {
    Optional<ReviewDecisionEntity> findTopByTenantIdAndRunIdOrderByCreatedAtDesc(
            String tenantId, String runId);
}
