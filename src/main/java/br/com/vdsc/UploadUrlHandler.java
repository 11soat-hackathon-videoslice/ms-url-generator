package br.com.vdsc;

import com.amazonaws.HttpMethod;
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

    // Static variables loaded once during Lambda container initialization
    private static final String BUCKET_NAME = System.getProperty("BUCKET_NAME", "vdsc-prd-s3-videos");
    private static final String UPLOAD_PREFIX = System.getProperty("UPLOAD_PREFIX", "uploads/");
    private static final long URL_EXPIRATION_MS = Long.parseLong(System.getProperty("URL_EXPIRATION_MS", "900000"));
    private static final String AWS_REGION = System.getProperty("AWS_REGION", "us-east-1");

    private static final AmazonS3 s3Client = AmazonS3ClientBuilder.standard()
            .withRegion(AWS_REGION)
            .build();
    private static final ObjectMapper objectMapper = new ObjectMapper();



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

            // Validate fileName
            if (fileName == null || fileName.trim().isEmpty()) {
                context.getLogger().log("fileName is required but was not provided");
                return createErrorResponse("fileName is required in path parameters", 400);
            }

            // Sanitize fileName to prevent path traversal
            fileName = fileName.replaceAll("[^a-zA-Z0-9._-]", "_");

            context.getLogger().log("Generating URL for fileName: " + fileName);

            String s3Key = UPLOAD_PREFIX + fileName;

            // Calculate expiration time
            Date expiration = new Date();
            expiration.setTime(expiration.getTime() + URL_EXPIRATION_MS);

            // Generate the presigned URL
            GeneratePresignedUrlRequest generatePresignedUrlRequest =
                    new GeneratePresignedUrlRequest(BUCKET_NAME, s3Key)
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

