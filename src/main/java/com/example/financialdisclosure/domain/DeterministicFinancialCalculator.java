package com.example.financialdisclosure.domain;

import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import org.springframework.stereotype.Component;

@Component
public class DeterministicFinancialCalculator {
    private static final MathContext CALCULATION_CONTEXT =
            new MathContext(34, RoundingMode.HALF_EVEN);

    public CalculationResult compare(
            BigDecimal actualValue, BigDecimal expectedValue, BigDecimal tolerance) {
        if (actualValue == null || expectedValue == null || tolerance == null) {
            throw new IllegalArgumentException("actualValue, expectedValue and tolerance are required");
        }
        if (tolerance.signum() < 0) {
            throw new IllegalArgumentException("tolerance must be non-negative");
        }
        BigDecimal difference =
                actualValue.subtract(expectedValue, CALCULATION_CONTEXT).abs(CALCULATION_CONTEXT);
        return new CalculationResult(
                difference, tolerance, difference.compareTo(tolerance) <= 0 ? "passed" : "review");
    }

    public record CalculationResult(BigDecimal difference, BigDecimal tolerance, String status) {}
}
