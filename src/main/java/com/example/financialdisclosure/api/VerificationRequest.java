package com.example.financialdisclosure.api;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;
import java.math.BigDecimal;

public record VerificationRequest(
        @NotBlank String filingId,
        @NotBlank String factName,
        @NotNull BigDecimal actualValue,
        @NotNull BigDecimal expectedValue,
        @NotNull @PositiveOrZero BigDecimal tolerance,
        @NotBlank String unit,
        @NotBlank String citation) {}
