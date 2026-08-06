package com.example.financialdisclosure.api;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public record FilingRequest(
        @NotBlank String filingId,
        @NotBlank String form,
        @NotBlank @Pattern(regexp = "(?i)xbrl|html|pdf|image") String format,
        @NotBlank String content,
        @NotBlank String version) {}
