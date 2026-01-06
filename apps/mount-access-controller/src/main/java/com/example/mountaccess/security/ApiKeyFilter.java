package com.example.mountaccess.security;

import org.springframework.beans.factory.annotation.Value;

import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;

public class ApiKeyFilter implements Filter {

    @Value("${api.key}")
    private String apiKey;

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;

        String requestPath = httpRequest.getRequestURI();
        
        // Skip auth for health endpoints
        if (requestPath.startsWith("/api/v1/health") || requestPath.startsWith("/actuator")) {
            chain.doFilter(request, response);
            return;
        }

        String providedApiKey = httpRequest.getHeader("X-API-Key");
        
        if (providedApiKey == null || !providedApiKey.equals(apiKey)) {
            httpResponse.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            httpResponse.getWriter().write("{\"error\":\"Unauthorized - Invalid API Key\"}");
            httpResponse.setContentType("application/json");
            return;
        }

        chain.doFilter(request, response);
    }
}
