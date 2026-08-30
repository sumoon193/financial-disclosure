package com.example.financialdisclosure.ocr;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Duration;
import java.util.concurrent.TimeUnit;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class TesseractOcrAdapter {
    private final String binary;
    private final String language;

    public TesseractOcrAdapter(
            @Value("${financial.ocr.binary:tesseract}") String binary,
            @Value("${financial.ocr.language:eng}") String language) {
        this.binary = binary;
        this.language = language;
    }

    public String extract(Path image) {
        Process process = null;
        try {
            process =
                    new ProcessBuilder(binary, image.toAbsolutePath().toString(), "stdout", "-l", language)
                            .redirectErrorStream(true)
                            .start();
            if (!process.waitFor(Duration.ofSeconds(45).toMillis(), TimeUnit.MILLISECONDS)) {
                process.destroyForcibly();
                throw new IllegalStateException("Tesseract OCR timed out");
            }
            String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            if (process.exitValue() != 0) {
                throw new IllegalStateException("Tesseract OCR failed with exit code " + process.exitValue());
            }
            if (output.isBlank()) {
                throw new IllegalStateException("Tesseract OCR quality gate rejected empty text");
            }
            return output.strip();
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Tesseract OCR interrupted", exception);
        } catch (IOException exception) {
            throw new IllegalStateException("Tesseract OCR unavailable", exception);
        } finally {
            if (process != null && process.isAlive()) {
                process.destroyForcibly();
            }
        }
    }
}
