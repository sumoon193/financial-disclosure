package com.example.financialdisclosure.api;

public record FilingResponse(
        String filingId, String documentVersionId, String objectKey, boolean duplicate) {}
