package com.example.financialdisclosure.storage;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import io.minio.BucketExistsArgs;
import io.minio.MakeBucketArgs;
import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;

class MinioObjectStorageAdapterTest {
    @Test
    void concurrentFirstWritesCreateBucketOnce() throws Exception {
        MinioClient client = mock(MinioClient.class);
        when(client.bucketExists(any(BucketExistsArgs.class))).thenReturn(false);
        doAnswer(invocation -> {
            Thread.sleep(25);
            return null;
        }).when(client).makeBucket(any(MakeBucketArgs.class));

        MinioObjectStorageAdapter adapter = new MinioObjectStorageAdapter(client, "filings");
        CountDownLatch start = new CountDownLatch(1);
        ExecutorService pool = Executors.newFixedThreadPool(2);
        pool.submit(() -> writeAfter(start, adapter, "one"));
        pool.submit(() -> writeAfter(start, adapter, "two"));
        start.countDown();
        pool.shutdown();
        if (!pool.awaitTermination(5, TimeUnit.SECONDS)) {
            throw new AssertionError("concurrent writes did not finish");
        }

        verify(client).makeBucket(any(MakeBucketArgs.class));
        verify(client, org.mockito.Mockito.times(2)).putObject(any(PutObjectArgs.class));
    }

    private static void writeAfter(
            CountDownLatch start, MinioObjectStorageAdapter adapter, String objectKey) {
        try {
            start.await();
            adapter.put(objectKey, objectKey.getBytes(), "text/plain");
        } catch (Exception exception) {
            throw new RuntimeException(exception);
        }
    }
}
