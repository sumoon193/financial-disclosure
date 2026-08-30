package com.example.financialdisclosure.api;

import java.math.BigDecimal;

public record VerificationResponse(
        String runId,
        String filingId,
        String factName,
        BigDecimal difference,
        BigDecimal tolerance,
        String status,
        String citation) {}
