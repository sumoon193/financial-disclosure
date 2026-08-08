package com.example.financialdisclosure.persistence;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "review_decisions")
public class ReviewDecisionEntity {
    @Id private String id;

    @Column(nullable = false)
    private String tenantId;

    @Column(nullable = false)
    private String runId;

    @Column(nullable = false)
    private String decision;

    @Column(nullable = false)
    private String reviewer;

    @Column(nullable = false, length = 2048)
    private String comment;

    @Column(nullable = false)
    private Instant createdAt;

    protected ReviewDecisionEntity() {}

    public ReviewDecisionEntity(
            String id,
            String tenantId,
            String runId,
            String decision,
            String reviewer,
            String comment,
            Instant createdAt) {
        this.id = id;
        this.tenantId = tenantId;
        this.runId = runId;
        this.decision = decision;
        this.reviewer = reviewer;
        this.comment = comment;
        this.createdAt = createdAt;
    }

    public String getId() { return id; }
    public String getDecision() { return decision; }
    public String getReviewer() { return reviewer; }
    public String getComment() { return comment; }
    public Instant getCreatedAt() { return createdAt; }
}
