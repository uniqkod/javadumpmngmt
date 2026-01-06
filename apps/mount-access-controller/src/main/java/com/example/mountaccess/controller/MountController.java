package com.example.mountaccess.controller;

import com.example.mountaccess.model.MountReadyRequest;
import com.example.mountaccess.model.MountRegisterRequest;
import com.example.mountaccess.service.MountService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/app/mount")
public class MountController {

    private static final Logger logger = LoggerFactory.getLogger(MountController.class);

    private final MountService mountService;

    public MountController(MountService mountService) {
        this.mountService = mountService;
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, String>> registerMount(@RequestBody MountRegisterRequest request) {
        logger.info("Received mount register request for app: {}", request.getAppName());
        
        try {
            mountService.registerMount(request.getAppName(), request.getUserId());
            
            Map<String, String> response = new HashMap<>();
            response.put("status", "success");
            response.put("message", "Mount registered successfully");
            response.put("appName", request.getAppName());
            
            return ResponseEntity.ok(response);
            
        } catch (IOException e) {
            logger.error("Failed to register mount for app: {}", request.getAppName(), e);
            
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("status", "error");
            errorResponse.put("message", "Failed to register mount: " + e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    @PostMapping("/ready")
    public ResponseEntity<Map<String, String>> checkMountReady(@RequestBody MountReadyRequest request) {
        logger.info("Received mount ready check for app: {}", request.getAppName());
        
        boolean isReady = mountService.isMountReady(request.getAppName(), request.getUserId());
        
        if (isReady) {
            Map<String, String> response = new HashMap<>();
            response.put("status", "ready");
            response.put("appName", request.getAppName());
            return ResponseEntity.ok(response);
        } else {
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("status", "not_ready");
            errorResponse.put("appName", request.getAppName());
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(errorResponse);
        }
    }
}
