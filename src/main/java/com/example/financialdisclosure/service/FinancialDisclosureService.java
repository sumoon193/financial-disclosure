package com.example.financialdisclosure.service;

import com.example.financialdisclosure.api.FilingRequest;
import com.example.financialdisclosure.api.FilingResponse;
import com.example.financialdisclosure.api.VerificationRequest;
import com.example.financialdisclosure.api.VerificationResponse;
import com.example.financialdisclosure.domain.DeterministicFinancialCalculator;
import com.example.financialdisclosure.persistence.FilingEntity;
import com.example.financialdisclosure.persistence.FilingRepository;
import com.example.financialdisclosure.persistence.VerificationRunEntity;
import com.example.financialdisclosure.persistence.VerificationRunRepository;
import com.example.financialdisclosure.storage.ObjectStoragePort;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HexFormat;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class FinancialDisclosureService {
    private final FilingRepository filings;
    private final VerificationRunRepository verificationRuns;
    private final ObjectStoragePort objectStorage;
    private final DeterministicFinancialCalculator calculator;

    public FinancialDisclosureService(
            FilingRepository filings,
            VerificationRunRepository verificationRuns,
            ObjectStoragePort objectStorage,
            DeterministicFinancialCalculator calculator) {
        this.filings = filings;
        this.verificationRuns = verificationRuns;
        this.objectStorage = objectStorage;
        this.calculator = calculator;
    }

    @Transactional
    public FilingResponse createFiling(FilingRequest request) {
        byte[] content = request.content().getBytes(StandardCharsets.UTF_8);
        String checksum = sha256(content);
        var existing = filings.findByContentSha256(checksum);
        if (existing.isPresent()) {
            FilingEntity entity = existing.orElseThrow();
            return new FilingResponse(
                    entity.getFilingId(), entity.getId(), entity.getObjectKey(), true);
        }

        String versionId = UUID.randomUUID().toString();
        String objectKey = request.filingId() + "/" + versionId + "." + request.format().toLowerCase();
        objectStorage.put(objectKey, content, "application/octet-stream");
        filings.save(
                new FilingEntity(
                        versionId,
                        request.filingId(),
                        request.form(),
                        request.format(),
                        request.version(),
                        checksum,
                        objectKey,
                        Instant.now()));
        return new FilingResponse(request.filingId(), versionId, objectKey, false);
    }

    @Transactional
    public VerificationResponse createVerification(VerificationRequest request) {
        var result =
                calculator.compare(
                        request.actualValue(), request.expectedValue(), request.tolerance());
        String runId = UUID.randomUUID().toString();
        verificationRuns.save(
                new VerificationRunEntity(
                        runId,
                        request.filingId(),
                        request.factName(),
                        request.actualValue(),
                        request.expectedValue(),
                        result.difference(),
                        result.tolerance(),
                        request.unit(),
                        result.status(),
                        request.citation(),
                        Instant.now()));
        return new VerificationResponse(
                runId,
                request.filingId(),
                request.factName(),
                result.difference(),
                result.tolerance(),
                result.status(),
                request.citation());
    }

    private static String sha256(byte[] content) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(content));
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
    }
}
