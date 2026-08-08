package com.example.financialdisclosure.persistence;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface VerificationEventRepository extends JpaRepository<VerificationEventEntity, String> {
    List<VerificationEventEntity> findByTenantIdAndRunIdOrderByCreatedAtAsc(
            String tenantId, String runId);
}
