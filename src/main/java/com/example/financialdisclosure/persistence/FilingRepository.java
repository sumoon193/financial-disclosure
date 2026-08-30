package com.example.financialdisclosure.persistence;

import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FilingRepository extends JpaRepository<FilingEntity, String> {
    Optional<FilingEntity> findByTenantIdAndContentSha256(String tenantId, String contentSha256);

    Page<FilingEntity> findByTenantIdOrderByCreatedAtDesc(String tenantId, Pageable pageable);

    long countByTenantId(String tenantId);
}
