package com.example.financialdisclosure.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.math.BigDecimal;
import org.junit.jupiter.api.Test;

class DeterministicFinancialCalculatorTest {
    private final DeterministicFinancialCalculator calculator =
            new DeterministicFinancialCalculator();

    @Test
    void compares_decimal_values_without_binary_floating_point() {
        var result =
                calculator.compare(
                        new BigDecimal("1200.500"),
                        new BigDecimal("1200.49"),
                        new BigDecimal("0.01"));

        assertThat(result.difference()).isEqualByComparingTo("0.010");
        assertThat(result.status()).isEqualTo("passed");
    }

    @Test
    void rejects_negative_tolerance() {
        assertThatThrownBy(
                        () ->
                                calculator.compare(
                                        BigDecimal.ONE, BigDecimal.ONE, new BigDecimal("-0.01")))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("non-negative");
    }
}
