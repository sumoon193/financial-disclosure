package com.example.financialdisclosure.persistence;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FilingRepository extends JpaRepository<FilingEntity, String> {
    Optional<FilingEntity> findByContentSha256(String contentSha256);
}
