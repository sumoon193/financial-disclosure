package com.example.financialdisclosure.source;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class SecEdgarClient {
    private final HttpClient client =
            HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
    private final String userAgent;

    public SecEdgarClient(@Value("${financial.sec.user-agent:}") String userAgent) {
        this.userAgent = userAgent;
    }

    public String fetchCompanyFacts(String cik) {
        if (userAgent.isBlank()) {
            throw new IllegalStateException("FINANCIAL_SEC_USER_AGENT is required for SEC access");
        }
        String normalizedCik = String.format("%010d", Long.parseLong(cik));
        HttpRequest request =
                HttpRequest.newBuilder()
                        .uri(URI.create("https://data.sec.gov/api/xbrl/companyfacts/CIK" + normalizedCik + ".json"))
                        .header("User-Agent", userAgent)
                        .header("Accept-Encoding", "gzip, deflate")
                        .timeout(Duration.ofSeconds(30))
                        .GET()
                        .build();
        try {
            HttpResponse<String> response =
                    client.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() != 200) {
                throw new IllegalStateException("SEC EDGAR returned status " + response.statusCode());
            }
            return response.body();
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("SEC EDGAR request interrupted", exception);
        } catch (IOException exception) {
            throw new IllegalStateException("SEC EDGAR request failed", exception);
        }
    }
}
