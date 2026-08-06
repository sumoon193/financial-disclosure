package com.example.financialdisclosure.persistence;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "filings")
public class FilingEntity {
    @Id private String id;

    @Column(nullable = false)
    private String filingId;

    @Column(nullable = false)
    private String formType;

    @Column(nullable = false)
    private String sourceFormat;

    @Column(nullable = false)
    private String version;

    @Column(nullable = false, unique = true)
    private String contentSha256;

    @Column(nullable = false)
    private String objectKey;

    @Column(nullable = false)
    private Instant createdAt;

    protected FilingEntity() {}

    public FilingEntity(
            String id,
            String filingId,
            String formType,
            String sourceFormat,
            String version,
            String contentSha256,
            String objectKey,
            Instant createdAt) {
        this.id = id;
        this.filingId = filingId;
        this.formType = formType;
        this.sourceFormat = sourceFormat;
        this.version = version;
        this.contentSha256 = contentSha256;
        this.objectKey = objectKey;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getFilingId() {
        return filingId;
    }

    public String getContentSha256() {
        return contentSha256;
    }

    public String getObjectKey() {
        return objectKey;
    }
}
