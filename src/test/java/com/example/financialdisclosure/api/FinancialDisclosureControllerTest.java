package com.example.financialdisclosure.api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.example.financialdisclosure.service.FinancialDisclosureService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(FinancialDisclosureController.class)
class FinancialDisclosureControllerTest {
    @Autowired private MockMvc mvc;

    @MockBean private FinancialDisclosureService service;

    @Test
    void verification_requires_decimal_inputs_at_the_http_boundary() throws Exception {
        mvc.perform(
                        post("/api/verification-runs")
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
