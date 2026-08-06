package com.example.financialdisclosure.api;

import com.example.financialdisclosure.service.FinancialDisclosureService;
import jakarta.validation.Valid;
import java.time.Instant;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class FinancialDisclosureController {
    private final FinancialDisclosureService service;

    public FinancialDisclosureController(FinancialDisclosureService service) {
        this.service = service;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of("status", "ok", "timestamp", Instant.now().toString());
    }

    @PostMapping("/api/filings")
    @ResponseStatus(HttpStatus.CREATED)
    public FilingResponse createFiling(@Valid @RequestBody FilingRequest request) {
        return service.createFiling(request);
    }

    @PostMapping("/api/verification-runs")
    @ResponseStatus(HttpStatus.CREATED)
    public VerificationResponse createVerification(
            @Valid @RequestBody VerificationRequest request) {
        return service.createVerification(request);
    }
}
