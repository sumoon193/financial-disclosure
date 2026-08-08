package com.example.financialdisclosure.persistence;

import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface VerificationRunRepository extends JpaRepository<VerificationRunEntity, String> {
    Page<VerificationRunEntity> findByTenantIdOrderByCreatedAtDesc(
            String tenantId, Pageable pageable);

    Optional<VerificationRunEntity> findByIdAndTenantId(String id, String tenantId);

    long countByTenantId(String tenantId);

    long countByTenantIdAndStatusNot(String tenantId, String status);
}
