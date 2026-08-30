package com.example.financialdisclosure.api;

import com.example.financialdisclosure.service.FinancialDisclosureService;
import jakarta.validation.Valid;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

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
    public FilingResponse createFiling(
            @AuthenticationPrincipal Jwt jwt, @Valid @RequestBody FilingRequest request) {
        return service.createFiling(tenantId(jwt), request);
    }

    @PostMapping(value = "/api/filings/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ResponseStatus(HttpStatus.CREATED)
    public FilingResponse uploadFiling(
            @AuthenticationPrincipal Jwt jwt,
            @RequestPart("file") MultipartFile file,
            @RequestParam String filingId,
            @RequestParam String form,
            @RequestParam String format,
            @RequestParam String version) {
        if (file.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "filing file is empty");
        }
        if (file.getSize() > 20L * 1024 * 1024) {
            throw new ResponseStatusException(
                    HttpStatus.PAYLOAD_TOO_LARGE, "filing file exceeds 20 MB");
        }
        try {
            return service.createFiling(
                    tenantId(jwt),
                    filingId,
                    form,
                    format,
                    version,
                    file.getContentType() == null
                            ? MediaType.APPLICATION_OCTET_STREAM_VALUE
                            : file.getContentType(),
                    file.getBytes());
        } catch (java.io.IOException exception) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST, "filing file cannot be read", exception);
        }
    }

    @GetMapping("/api/filings")
    public PageResponse<FilingSummaryResponse> listFilings(
            @AuthenticationPrincipal Jwt jwt,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        int safePage = Math.max(page, 0);
        int safeSize = Math.min(Math.max(size, 1), 100);
        return service.listFilings(tenantId(jwt), safePage, safeSize);
    }

    @GetMapping("/api/overview")
    public OverviewResponse overview(@AuthenticationPrincipal Jwt jwt) {
        return service.overview(tenantId(jwt));
    }

    @GetMapping("/api/verification-runs")
    public PageResponse<VerificationSummaryResponse> listVerifications(
            @AuthenticationPrincipal Jwt jwt,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        int safePage = Math.max(page, 0);
        int safeSize = Math.min(Math.max(size, 1), 100);
        return service.listVerifications(tenantId(jwt), safePage, safeSize);
    }

    @PostMapping("/api/verification-runs")
    @ResponseStatus(HttpStatus.CREATED)
    public VerificationResponse createVerification(
            @AuthenticationPrincipal Jwt jwt, @Valid @RequestBody VerificationRequest request) {
        return service.createVerification(tenantId(jwt), request);
    }

    @GetMapping("/api/verification-runs/{runId}/timeline")
    public List<TimelineEventResponse> timeline(
            @AuthenticationPrincipal Jwt jwt,
            @org.springframework.web.bind.annotation.PathVariable String runId) {
        return service.timeline(tenantId(jwt), runId);
    }

    @PostMapping("/api/verification-runs/{runId}/review-decisions")
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAnyRole('financial-reviewer','financial-admin')")
    public ReviewDecisionResponse review(
            @AuthenticationPrincipal Jwt jwt,
            @org.springframework.web.bind.annotation.PathVariable String runId,
            @Valid @RequestBody ReviewDecisionRequest request) {
        return service.review(
                tenantId(jwt), runId, jwt.getSubject(), request.decision(), request.comment());
    }

    private static String tenantId(Jwt jwt) {
        String tenantId = jwt.getClaimAsString("tenant_id");
        if (tenantId == null || tenantId.isBlank()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "tenant_id claim is required");
        }
        return tenantId;
    }
}
