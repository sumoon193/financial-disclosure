package com.example.financialdisclosure.api;

import java.time.Instant;

public record ReviewDecisionResponse(
        String decisionId,
        String runId,
        String decision,
        String reviewer,
        String comment,
        Instant createdAt) {}
