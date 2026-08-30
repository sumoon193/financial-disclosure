package com.example.financialdisclosure.api;

import java.time.Instant;

public record FilingSummaryResponse(
        String documentVersionId,
        String filingId,
        String form,
        String format,
        String version,
        Instant createdAt) {}
