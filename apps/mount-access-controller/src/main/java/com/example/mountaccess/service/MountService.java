package com.example.mountaccess.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@Service
public class MountService {

    private static final Logger logger = LoggerFactory.getLogger(MountService.class);

    @Value("${mount.base.path:/mnt/dump}")
    private String mountBasePath;

    public void registerMount(String appName, String userId) throws IOException {
        logger.info("Registering mount for app: {}, user: {}", appName, userId);

        Path appPath = Paths.get(mountBasePath, appName);
        Path heapPath = Paths.get(mountBasePath, appName, "heap");

        // Create directories
        executeCommand("mkdir", "-p", heapPath.toString());
        
        // Change ownership
        executeCommand("chown", "-R", userId + ":" + userId, appPath.toString());
        executeCommand("chown", "-R", userId + ":" + userId, heapPath.toString());

        logger.info("Successfully registered mount for app: {}", appName);
    }

    public boolean isMountReady(String appName, String userId) {
        logger.info("Checking mount readiness for app: {}, user: {}", appName, userId);

        try {
            Path heapPath = Paths.get(mountBasePath, appName, "heap");
            
            if (!Files.exists(heapPath)) {
                logger.warn("Heap path does not exist: {}", heapPath);
                return false;
            }

            // Check ownership by UID
            Object uidObj = Files.getAttribute(heapPath, "unix:uid");
            String ownerUid = uidObj.toString();
            boolean isReady = ownerUid.equals(userId);
            
            logger.info("Mount ready check for app: {}, owner UID: {}, expected UID: {}, result: {}", 
                        appName, ownerUid, userId, isReady);
            return isReady;
            
        } catch (IOException e) {
            logger.error("Error checking mount readiness", e);
            return false;
        }
    }

    private void executeCommand(String... command) throws IOException {
        ProcessBuilder processBuilder = new ProcessBuilder(command);
        processBuilder.redirectErrorStream(true);
        
        Process process = processBuilder.start();
        
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                logger.debug("Command output: {}", line);
            }
        }

        try {
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                throw new IOException("Command failed with exit code: " + exitCode);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IOException("Command interrupted", e);
        }
    }
}
