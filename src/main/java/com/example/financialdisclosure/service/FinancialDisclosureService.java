package com.example.financialdisclosure.service;

import com.example.financialdisclosure.api.FilingRequest;
import com.example.financialdisclosure.api.FilingResponse;
import com.example.financialdisclosure.api.FilingSummaryResponse;
import com.example.financialdisclosure.api.PageResponse;
import com.example.financialdisclosure.api.VerificationRequest;
import com.example.financialdisclosure.api.VerificationResponse;
import com.example.financialdisclosure.api.VerificationSummaryResponse;
import com.example.financialdisclosure.api.OverviewResponse;
import com.example.financialdisclosure.api.ReviewDecisionResponse;
import com.example.financialdisclosure.api.TimelineEventResponse;
import com.example.financialdisclosure.domain.DeterministicFinancialCalculator;
import com.example.financialdisclosure.persistence.FilingEntity;
import com.example.financialdisclosure.persistence.FilingRepository;
import com.example.financialdisclosure.persistence.VerificationRunEntity;
import com.example.financialdisclosure.persistence.VerificationRunRepository;
import com.example.financialdisclosure.persistence.ReviewDecisionEntity;
import com.example.financialdisclosure.persistence.ReviewDecisionRepository;
import com.example.financialdisclosure.persistence.VerificationEventEntity;
import com.example.financialdisclosure.persistence.VerificationEventRepository;
import com.example.financialdisclosure.storage.ObjectStoragePort;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HexFormat;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.data.domain.PageRequest;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;

@Service
public class FinancialDisclosureService {
    private final FilingRepository filings;
    private final VerificationRunRepository verificationRuns;
    private final ObjectStoragePort objectStorage;
    private final DeterministicFinancialCalculator calculator;
    private final ReviewDecisionRepository reviewDecisions;
    private final VerificationEventRepository verificationEvents;

    public FinancialDisclosureService(
            FilingRepository filings,
            VerificationRunRepository verificationRuns,
            ObjectStoragePort objectStorage,
            DeterministicFinancialCalculator calculator,
            ReviewDecisionRepository reviewDecisions,
            VerificationEventRepository verificationEvents) {
        this.filings = filings;
        this.verificationRuns = verificationRuns;
        this.objectStorage = objectStorage;
        this.calculator = calculator;
        this.reviewDecisions = reviewDecisions;
        this.verificationEvents = verificationEvents;
    }

    @Transactional
    public FilingResponse createFiling(String tenantId, FilingRequest request) {
        return createFiling(
                tenantId,
                request.filingId(),
                request.form(),
                request.format(),
                request.version(),
                "application/octet-stream",
                request.content().getBytes(StandardCharsets.UTF_8));
    }

    @Transactional
    public synchronized FilingResponse createFiling(
            String tenantId,
            String filingId,
            String form,
            String format,
            String version,
            String contentType,
            byte[] content) {
        if (!format.matches("(?i)xbrl|html|pdf|image")) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "unsupported filing format");
        }
        if (content.length == 0) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "filing content is empty");
        }
        String checksum = sha256(content);
        var existing = filings.findByTenantIdAndContentSha256(tenantId, checksum);
        if (existing.isPresent()) {
            FilingEntity entity = existing.orElseThrow();
            return new FilingResponse(
                    entity.getFilingId(), entity.getId(), entity.getObjectKey(), true);
        }

        String versionId = UUID.randomUUID().toString();
        String safeFilingId = filingId.replaceAll("[^A-Za-z0-9._-]", "_");
        String objectKey =
                tenantId
                        + "/"
                        + safeFilingId
                        + "/"
                        + versionId
                        + "."
                        + format.toLowerCase();
        objectStorage.put(objectKey, content, contentType);
        filings.save(
                new FilingEntity(
                        versionId,
                        tenantId,
                        filingId,
                        form,
                        format,
                        version,
                        checksum,
                        objectKey,
                        Instant.now()));
        return new FilingResponse(filingId, versionId, objectKey, false);
    }

    @Transactional(readOnly = true)
    public PageResponse<FilingSummaryResponse> listFilings(
            String tenantId, int page, int size) {
        var result =
                filings.findByTenantIdOrderByCreatedAtDesc(tenantId, PageRequest.of(page, size));
        var items =
                result.getContent().stream()
                        .map(
                                filing ->
                                        new FilingSummaryResponse(
                                                filing.getId(),
                                                filing.getFilingId(),
                                                filing.getFormType(),
                                                filing.getSourceFormat(),
                                                filing.getVersion(),
                                                filing.getCreatedAt()))
                        .toList();
        return new PageResponse<>(items, page, size, result.getTotalElements());
    }

    @Transactional
    public VerificationResponse createVerification(String tenantId, VerificationRequest request) {
        var result =
                calculator.compare(
                        request.actualValue(), request.expectedValue(), request.tolerance());
        String runId = UUID.randomUUID().toString();
        Instant createdAt = Instant.now();
        verificationRuns.save(
                new VerificationRunEntity(
                        runId,
                        tenantId,
                        request.filingId(),
                        request.factName(),
                        request.actualValue(),
                        request.expectedValue(),
                        result.difference(),
                        result.tolerance(),
                        request.unit(),
                        result.status(),
                        request.citation(),
                        createdAt));
        verificationEvents.save(
                new VerificationEventEntity(
                        UUID.randomUUID().toString(),
                        tenantId,
                        runId,
                        "verification-created",
                        "system",
                        result.status(),
                        createdAt));
        return new VerificationResponse(
                runId,
                request.filingId(),
                request.factName(),
                result.difference(),
                result.tolerance(),
                result.status(),
                request.citation());
    }

    @Transactional(readOnly = true)
    public OverviewResponse overview(String tenantId) {
        var runs = verificationRuns.findByTenantIdOrderByCreatedAtDesc(
                tenantId, PageRequest.of(0, 1000));
        long pending =
                runs.stream()
                        .filter(
                                run ->
                                        reviewDecisions
                                                .findTopByTenantIdAndRunIdOrderByCreatedAtDesc(
                                                        tenantId, run.getId())
                                                .isEmpty())
                        .count();
        return new OverviewResponse(
                filings.countByTenantId(tenantId),
                verificationRuns.countByTenantId(tenantId),
                pending,
                verificationRuns.countByTenantIdAndStatusNot(tenantId, "passed"));
    }

    @Transactional(readOnly = true)
    public PageResponse<VerificationSummaryResponse> listVerifications(
            String tenantId, int page, int size) {
        var result =
                verificationRuns.findByTenantIdOrderByCreatedAtDesc(
                        tenantId, PageRequest.of(page, size));
        var items =
                result.getContent().stream()
                        .map(
                                run ->
                                        new VerificationSummaryResponse(
                                                run.getId(),
                                                run.getFilingId(),
                                                run.getFactName(),
                                                run.getDifference(),
                                                run.getTolerance(),
                                                run.getStatus(),
                                                run.getCitation(),
                                                reviewDecisions
                                                        .findTopByTenantIdAndRunIdOrderByCreatedAtDesc(
                                                                tenantId, run.getId())
                                                        .map(ReviewDecisionEntity::getDecision)
                                                        .orElse("pending"),
                                                run.getCreatedAt()))
                        .toList();
        return new PageResponse<>(items, page, size, result.getTotalElements());
    }

    @Transactional
    public ReviewDecisionResponse review(
            String tenantId,
            String runId,
            String reviewer,
            String decision,
            String comment) {
        verificationRuns
                .findByIdAndTenantId(runId, tenantId)
                .orElseThrow(
                        () -> new ResponseStatusException(HttpStatus.NOT_FOUND, "run not found"));
        Instant createdAt = Instant.now();
        var entity =
                reviewDecisions.save(
                        new ReviewDecisionEntity(
                                UUID.randomUUID().toString(),
                                tenantId,
                                runId,
                                decision,
                                reviewer,
                                comment,
                                createdAt));
        verificationEvents.save(
                new VerificationEventEntity(
                        UUID.randomUUID().toString(),
                        tenantId,
                        runId,
                        "review-recorded",
                        reviewer,
                        decision,
                        createdAt));
        return new ReviewDecisionResponse(
                entity.getId(),
                runId,
                entity.getDecision(),
                entity.getReviewer(),
                entity.getComment(),
                entity.getCreatedAt());
    }

    @Transactional(readOnly = true)
    public java.util.List<TimelineEventResponse> timeline(String tenantId, String runId) {
        verificationRuns
                .findByIdAndTenantId(runId, tenantId)
                .orElseThrow(
                        () -> new ResponseStatusException(HttpStatus.NOT_FOUND, "run not found"));
        return verificationEvents.findByTenantIdAndRunIdOrderByCreatedAtAsc(tenantId, runId)
                .stream()
                .map(
                        event ->
                                new TimelineEventResponse(
                                        event.getId(),
                                        event.getEventType(),
                                        event.getActor(),
                                        event.getDetail(),
                                        event.getCreatedAt()))
                .toList();
    }

    private static String sha256(byte[] content) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(content));
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
    }
}
