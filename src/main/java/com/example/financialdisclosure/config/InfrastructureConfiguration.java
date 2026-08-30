package com.example.financialdisclosure.config;

import io.minio.MinioClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class InfrastructureConfiguration {
    @Bean
    MinioClient minioClient(
            @Value("${financial.storage.endpoint:http://127.0.0.1:9000}") String endpoint,
            @Value("${financial.storage.access-key:minioadmin}") String accessKey,
            @Value("${financial.storage.secret-key:minioadmin}") String secretKey) {
        return MinioClient.builder().endpoint(endpoint).credentials(accessKey, secretKey).build();
    }
}
