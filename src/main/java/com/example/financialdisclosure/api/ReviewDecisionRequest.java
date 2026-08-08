package com.example.financialdisclosure.api;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public record ReviewDecisionRequest(
        @NotBlank @Pattern(regexp = "approved|rejected|needs-review") String decision,
        @NotBlank String comment) {}
