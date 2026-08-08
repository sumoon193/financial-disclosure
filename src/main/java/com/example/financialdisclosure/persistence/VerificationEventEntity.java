package com.example.financialdisclosure.persistence;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "verification_events")
public class VerificationEventEntity {
    @Id private String id;

    @Column(nullable = false)
    private String tenantId;

    @Column(nullable = false)
    private String runId;

    @Column(nullable = false)
    private String eventType;

    @Column(nullable = false)
    private String actor;

    @Column(nullable = false, length = 2048)
    private String detail;

    @Column(nullable = false)
    private Instant createdAt;

    protected VerificationEventEntity() {}

    public VerificationEventEntity(
            String id,
            String tenantId,
            String runId,
            String eventType,
            String actor,
            String detail,
            Instant createdAt) {
        this.id = id;
        this.tenantId = tenantId;
        this.runId = runId;
        this.eventType = eventType;
        this.actor = actor;
        this.detail = detail;
        this.createdAt = createdAt;
    }

    public String getId() { return id; }
    public String getEventType() { return eventType; }
    public String getActor() { return actor; }
    public String getDetail() { return detail; }
    public Instant getCreatedAt() { return createdAt; }
}
