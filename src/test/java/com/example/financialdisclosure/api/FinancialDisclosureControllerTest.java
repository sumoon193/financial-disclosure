package com.example.financialdisclosure.api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;

import com.example.financialdisclosure.service.FinancialDisclosureService;
import com.example.financialdisclosure.security.SecurityConfiguration;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(
        controllers = FinancialDisclosureController.class,
        properties = "FINANCIAL_OIDC_ISSUER_URL=http://issuer.invalid/realms/financial")
@Import(SecurityConfiguration.class)
class FinancialDisclosureControllerTest {
    @Autowired private MockMvc mvc;

    @MockBean private FinancialDisclosureService service;
    @MockBean private JwtDecoder jwtDecoder;

    @Test
    void verification_requires_decimal_inputs_at_the_http_boundary() throws Exception {
        mvc.perform(
                        post("/api/verification-runs")
                                .with(
                                        jwt().jwt(
                                                        token ->
                                                                token.claim(
                                                                        "tenant_id", "tenant-a"))
                                                .authorities(
                                                        new SimpleGrantedAuthority(
                                                                "ROLE_financial-analyst")))
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(
                                        """
                                        {
                                          "filingId":"filing-1",
                                          "factName":"Revenue",
                                          "unit":"USD",
                                          "citation":"sec://filing-1"
                                        }
                                        """))
                .andExpect(status().isBadRequest());
    }
}
