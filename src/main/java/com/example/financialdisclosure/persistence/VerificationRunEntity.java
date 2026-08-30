package com.example.financialdisclosure.persistence;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "verification_runs")
public class VerificationRunEntity {
    @Id private String id;

    @Column(nullable = false)
    private String tenantId;

    @Column(nullable = false)
    private String filingId;

    @Column(nullable = false)
    private String factName;

    @Column(nullable = false, precision = 38, scale = 12)
    private BigDecimal actualValue;

    @Column(nullable = false, precision = 38, scale = 12)
    private BigDecimal expectedValue;

    @Column(nullable = false, precision = 38, scale = 12)
    private BigDecimal difference;

    @Column(nullable = false, precision = 38, scale = 12)
    private BigDecimal tolerance;

    @Column(nullable = false)
    private String unit;

    @Column(nullable = false)
    private String status;

    @Column(nullable = false, length = 1024)
    private String citation;

    @Column(nullable = false)
    private Instant createdAt;

    protected VerificationRunEntity() {}

    public VerificationRunEntity(
            String id,
            String tenantId,
            String filingId,
            String factName,
            BigDecimal actualValue,
            BigDecimal expectedValue,
            BigDecimal difference,
            BigDecimal tolerance,
            String unit,
            String status,
            String citation,
            Instant createdAt) {
        this.id = id;
        this.tenantId = tenantId;
        this.filingId = filingId;
        this.factName = factName;
        this.actualValue = actualValue;
        this.expectedValue = expectedValue;
        this.difference = difference;
        this.tolerance = tolerance;
        this.unit = unit;
        this.status = status;
        this.citation = citation;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getFilingId() { return filingId; }
    public String getFactName() { return factName; }
    public BigDecimal getActualValue() { return actualValue; }
    public BigDecimal getExpectedValue() { return expectedValue; }
    public BigDecimal getDifference() { return difference; }
    public BigDecimal getTolerance() { return tolerance; }
    public String getUnit() { return unit; }
    public String getStatus() { return status; }
    public String getCitation() { return citation; }
    public Instant getCreatedAt() { return createdAt; }
}
