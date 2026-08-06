package com.example.financialdisclosure.storage;

public interface ObjectStoragePort {
    void put(String objectKey, byte[] content, String contentType);
}
