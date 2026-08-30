package com.example.financialdisclosure.api;

public record OverviewResponse(
        long filings, long verifications, long pendingReviews, long discrepancies) {}
