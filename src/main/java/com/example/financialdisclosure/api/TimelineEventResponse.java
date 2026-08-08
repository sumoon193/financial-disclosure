package com.example.financialdisclosure.api;

import java.time.Instant;

public record TimelineEventResponse(
        String eventId, String eventType, String actor, String detail, Instant createdAt) {}
