import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
export default defineConfig({
    plugins: [vue()],
    resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
    server: {
        port: 5101,
        proxy: { '/api': { target: 'http://127.0.0.1:8001', changeOrigin: true } },
    },
    test: {
        environment: 'jsdom',
        setupFiles: ['./src/test/setup.ts'],
        exclude: ['e2e/**', 'node_modules/**', 'dist/**'],
    },
});
