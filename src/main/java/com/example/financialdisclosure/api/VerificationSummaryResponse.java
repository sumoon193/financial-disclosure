package com.example.financialdisclosure.api;

import java.math.BigDecimal;
import java.time.Instant;

public record VerificationSummaryResponse(
        String runId,
        String filingId,
        String factName,
        BigDecimal difference,
        BigDecimal tolerance,
        String status,
        String citation,
        String reviewStatus,
        Instant createdAt) {}
