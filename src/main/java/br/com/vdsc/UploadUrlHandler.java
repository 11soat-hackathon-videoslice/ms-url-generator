package br.com.vdsc;

import br.com.vdsc.config.AppConfig;
import com.amazonaws.HttpMethod;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.model.GeneratePresignedUrlRequest;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URL;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

public class UploadUrlHandler implements RequestHandler<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> {

    private final String bucketName;
    private final String uploadPrefix;
    private final long urlExpirationMs;
    private final AmazonS3 s3Client;
    private final ObjectMapper objectMapper;

    public UploadUrlHandler() {
        // Load configuration from application.yaml
        AppConfig config = new AppConfig();

        this.bucketName = config.getBucketName();
        this.uploadPrefix = config.getUploadPrefix();
        this.urlExpirationMs = config.getUrlExpirationMs();

        this.s3Client = AmazonS3ClientBuilder.standard()
                .withRegion(Regions.fromName(config.getAwsRegion()))
                .build();
        this.objectMapper = new ObjectMapper();
    }

    @Override
    public APIGatewayProxyResponseEvent handleRequest(APIGatewayProxyRequestEvent request, Context context) {

        APIGatewayProxyResponseEvent response = new APIGatewayProxyResponseEvent();

        // Set CORS headers
        Map<String, String> headers = new HashMap<>();
        headers.put("Content-Type", "application/json");
        headers.put("Access-Control-Allow-Origin", "*");
        headers.put("Access-Control-Allow-Methods", "POST, OPTIONS");
        headers.put("Access-Control-Allow-Headers", "Content-Type, Authorization");
        response.setHeaders(headers);

        try {
            context.getLogger().log("Generating pre-signed URL for video upload");

            // Extract fileName from path parameters
            String fileName = extractFileNameFromRequest(request, context);

            if (fileName == null || fileName.trim().isEmpty()) {
                return createErrorResponse("fileName is required in path", 400);
            }

            // Validate and sanitize fileName
            fileName = sanitizeFileName(fileName);

            context.getLogger().log("Generating URL for fileName: " + fileName);

            String s3Key = uploadPrefix + fileName;

            // Calculate expiration time
            Date expiration = new Date();
            expiration.setTime(expiration.getTime() + urlExpirationMs);

            // Generate the presigned URL
            GeneratePresignedUrlRequest generatePresignedUrlRequest =
                    new GeneratePresignedUrlRequest(bucketName, s3Key)
                            .withMethod(HttpMethod.PUT)
                            .withExpiration(expiration);

            URL presignedUrl = s3Client.generatePresignedUrl(generatePresignedUrlRequest);

            context.getLogger().log("Pre-signed URL generated successfully for key: " + s3Key);

            // Response body
            Map<String, Object> responseBody = new HashMap<>();
            responseBody.put("uploadUrl", presignedUrl.toString());
            responseBody.put("fileName", fileName);
            responseBody.put("s3Key", s3Key);
            responseBody.put("expiresIn", "15 minutes");

            response.setStatusCode(200);
            response.setBody(objectMapper.writeValueAsString(responseBody));

        } catch (Exception e) {
            context.getLogger().log("Error generating pre-signed URL: " + e.getMessage());
            e.printStackTrace();

            Map<String, Object> errorBody = new HashMap<>();
            errorBody.put("error", "Failed to generate upload URL");
            errorBody.put("message", e.getMessage());

            try {
                response.setStatusCode(500);
                response.setBody(objectMapper.writeValueAsString(errorBody));
            } catch (Exception jsonEx) {
                response.setBody("{\"error\":\"Internal server error\"}");
            }
        }

        return response;
    }

    /**
     * Extracts fileName from API Gateway path parameters
     */
    private String extractFileNameFromRequest(APIGatewayProxyRequestEvent request, Context context) {
        try {
            // API Gateway passes path parameters in the "pathParameters" key
            Map<String, String> pathParams = request.getPathParameters();
            if (pathParams != null && pathParams.containsKey("fileName")) {
                return pathParams.get("fileName");
            }

            context.getLogger().log("No fileName found in pathParameters");
            return null;
        } catch (Exception e) {
            context.getLogger().log("Error extracting fileName: " + e.getMessage());
            return null;
        }
    }

    /**
     * Sanitizes fileName to prevent security issues
     * Removes path traversal characters and ensures safe filename
     */
    private String sanitizeFileName(String fileName) {
        if (fileName == null) {
            return null;
        }

        // Remove any path traversal attempts
        fileName = fileName.replace("..", "");
        fileName = fileName.replace("/", "");
        fileName = fileName.replace("\\", "");

        // Trim whitespace
        fileName = fileName.trim();

        return fileName;
    }

    /**
     * Creates an error response with the specified message and status code
     */
    private APIGatewayProxyResponseEvent createErrorResponse(String errorMessage, int statusCode) {
        APIGatewayProxyResponseEvent response = new APIGatewayProxyResponseEvent();
        Map<String, Object> errorBody = new HashMap<>();
        errorBody.put("error", errorMessage);

        try {
            response.setStatusCode(statusCode);
            response.setBody(objectMapper.writeValueAsString(errorBody));
        } catch (Exception e) {
            response.setBody("{\"error\":\"" + errorMessage + "\"}");
        }

        Map<String, String> headers = new HashMap<>();
        headers.put("Content-Type", "application/json");
        headers.put("Access-Control-Allow-Origin", "*");
        response.setHeaders(headers);

        return response;
    }

}

