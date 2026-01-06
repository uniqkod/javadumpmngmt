package com.example.mountaccess.model;

public class MountRegisterRequest {
    private String appName;
    private String userId;

    public MountRegisterRequest() {
    }

    public MountRegisterRequest(String appName, String userId) {
        this.appName = appName;
        this.userId = userId;
    }

    public String getAppName() {
        return appName;
    }

    public void setAppName(String appName) {
        this.appName = appName;
    }

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }
}
