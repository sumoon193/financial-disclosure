package com.example.financialdisclosure.api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.mockito.AdditionalMatchers.aryEq;
import static org.mockito.ArgumentMatchers.eq;

import com.example.financialdisclosure.service.FinancialDisclosureService;
import com.example.financialdisclosure.security.SecurityConfiguration;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;
import java.time.Instant;
import java.util.List;
import java.math.BigDecimal;
import org.springframework.http.MediaType;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.mock.web.MockMultipartFile;

@WebMvcTest(
        controllers = FinancialDisclosureController.class,
        properties = "FINANCIAL_OIDC_ISSUER_URL=http://issuer.invalid/realms/financial")
@Import(SecurityConfiguration.class)
class FrontendReadModelTest {
    @Autowired private MockMvc mvc;

    @MockBean private FinancialDisclosureService service;
    @MockBean private JwtDecoder jwtDecoder;

    @Test
    void health_is_public_but_filing_read_model_requires_authentication() throws Exception {
        mvc.perform(get("/health")).andExpect(status().isOk());
        mvc.perform(get("/api/filings")).andExpect(status().isUnauthorized());
    }

    @Test
    void filing_list_uses_the_tenant_claim_and_ignores_spoofed_headers() throws Exception {
        var summary =
                new FilingSummaryResponse(
                        "version-1", "filing-1", "10-K", "xbrl", "2026-01", Instant.EPOCH);
        when(service.listFilings("tenant-a", 0, 20))
                .thenReturn(new PageResponse<>(List.of(summary), 0, 20, 1));

        mvc.perform(
                        get("/api/filings")
                                .header("X-Tenant-Id", "attacker")
                                .with(tenantJwt("tenant-a")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items[0].filingId").value("filing-1"))
                .andExpect(jsonPath("$.total").value(1));

        verify(service).listFilings("tenant-a", 0, 20);
    }

    @Test
    void overview_and_verification_read_models_are_tenant_scoped() throws Exception {
        when(service.overview("tenant-a")).thenReturn(new OverviewResponse(3, 5, 2, 1));
        var verification =
                new VerificationSummaryResponse(
                        "run-1",
                        "filing-1",
                        "Revenue",
                        new BigDecimal("0.01"),
                        new BigDecimal("0.01"),
                        "passed",
                        "sec://filing-1",
                        "pending",
                        Instant.EPOCH);
        when(service.listVerifications("tenant-a", 0, 20))
                .thenReturn(new PageResponse<>(List.of(verification), 0, 20, 1));

        mvc.perform(get("/api/overview").with(tenantJwt("tenant-a")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.filings").value(3))
                .andExpect(jsonPath("$.pendingReviews").value(2));
        mvc.perform(get("/api/verification-runs").with(tenantJwt("tenant-a")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items[0].runId").value("run-1"));
    }

    @Test
    void reviewer_can_record_a_decision_and_receive_an_audit_timeline() throws Exception {
        var decision =
                new ReviewDecisionResponse(
                        "decision-1",
                        "run-1",
                        "approved",
                        "reviewer-1",
                        "evidence checked",
                        Instant.EPOCH);
        when(service.review("tenant-a", "run-1", "reviewer-1", "approved", "evidence checked"))
                .thenReturn(decision);
        when(service.timeline("tenant-a", "run-1"))
                .thenReturn(
                        List.of(
                                new TimelineEventResponse(
                                        "event-1",
                                        "review-recorded",
                                        "reviewer-1",
                                        "approved",
                                        Instant.EPOCH)));

        mvc.perform(
                        post("/api/verification-runs/run-1/review-decisions")
                                .with(
                                        tenantJwt("tenant-a")
                                                .authorities(
                                                        new SimpleGrantedAuthority(
                                                                "ROLE_financial-reviewer")))
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {"decision":"approved","comment":"evidence checked"}
                                        """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.decision").value("approved"));
        mvc.perform(get("/api/verification-runs/run-1/timeline").with(tenantJwt("tenant-a")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].eventType").value("review-recorded"));
    }

    @Test
    void analyst_cannot_record_a_review_decision() throws Exception {
        mvc.perform(
                        post("/api/verification-runs/run-1/review-decisions")
                                .with(
                                        tenantJwt("tenant-a")
                                                .authorities(
                                                        new SimpleGrantedAuthority(
                                                                "ROLE_financial-analyst")))
                                .contentType(MediaType.APPLICATION_JSON)
                                .content("{\"decision\":\"approved\",\"comment\":\"checked\"}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void authenticated_analyst_can_upload_a_binary_filing_for_the_token_tenant()
            throws Exception {
        var response = new FilingResponse("0001-10-k", "version-1", "object-key", false);
        when(service.createFiling(
                        eq("tenant-a"),
                        eq("0001-10-k"),
                        eq("10-K"),
                        eq("pdf"),
                        eq("2026-01"),
                        eq("application/pdf"),
                        aryEq(
                                "pdf-content"
                                        .getBytes(java.nio.charset.StandardCharsets.UTF_8))))
                .thenReturn(response);
        var file =
                new MockMultipartFile(
                        "file",
                        "filing.pdf",
                        "application/pdf",
                        "pdf-content".getBytes(java.nio.charset.StandardCharsets.UTF_8));

        mvc.perform(
                        multipart("/api/filings/upload")
                                .file(file)
                                .param("filingId", "0001-10-k")
                                .param("form", "10-K")
                                .param("format", "pdf")
                                .param("version", "2026-01")
                                .with(tenantJwt("tenant-a")))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.documentVersionId").value("version-1"));
    }

    private static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.JwtRequestPostProcessor tenantJwt(
            String tenantId) {
        return jwt().jwt(
                        token ->
                                token.subject("reviewer-1")
                                        .claim("tenant_id", tenantId)
                                        .claim(
                                                "realm_access",
                                                java.util.Map.of(
                                                        "roles",
                                                        List.of("financial-analyst"))))
                .authorities(new SimpleGrantedAuthority("ROLE_financial-analyst"));
    }
}
