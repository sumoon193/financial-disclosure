package com.example.financialdisclosure.api;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.PositiveOrZero;
import java.math.BigDecimal;

public record VerificationRequest(
        @NotBlank String filingId,
        @NotBlank String factName,
        BigDecimal actualValue,
        BigDecimal expectedValue,
        @PositiveOrZero BigDecimal tolerance,
        @NotBlank String unit,
        @NotBlank String citation) {}
