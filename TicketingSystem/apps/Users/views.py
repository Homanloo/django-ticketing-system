from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.conf import settings
from apps.Users.serializers import CustomTokenObtainPairSerializer, UserRegistrationSerializer, UserProfileSerializer, ChangePasswordSerializer


@extend_schema(
    tags=['v1 - Authentication'],
    summary='User Login',
    description='Authenticate user and receive access token. Refresh token is set as HttpOnly cookie.',
    responses={
        200: CustomTokenObtainPairSerializer,
        401: OpenApiResponse(description='Invalid credentials'),
    }
)
class LoginView(TokenObtainPairView):
    """
    Login view that sets refresh token as HttpOnly cookie.
    Only access token is returned in response body.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def finalize_response(self, request, response, *args, **kwargs):
        """Set refresh token as HttpOnly cookie"""
        if response.status_code == 200 and 'refresh' in response.data:
            # Extract refresh token from response
            refresh_token = response.data.pop('refresh')
            
            # Set as HttpOnly cookie
            response.set_cookie(
                key=settings.REFRESH_TOKEN_COOKIE_NAME,
                value=refresh_token,
                max_age=settings.REFRESH_TOKEN_COOKIE_MAX_AGE,
                httponly=settings.REFRESH_TOKEN_COOKIE_HTTPONLY,
                secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
                samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
            )
        
        return super().finalize_response(request, response, *args, **kwargs)


@extend_schema(
    tags=['v1 - Authentication'],
    summary='User Registration',
    description='Register a new customer account. Access token returned in body, refresh token set as HttpOnly cookie.',
    responses={
        201: UserRegistrationSerializer,
        400: OpenApiResponse(description='Validation error'),
    }
)
class RegisterView(generics.CreateAPIView):
    """
    Registration view that sets refresh token as HttpOnly cookie.
    Only access token is returned in response body.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def finalize_response(self, request, response, *args, **kwargs):
        """Set refresh token as HttpOnly cookie"""
        if response.status_code == 201 and '_refresh_token' in response.data:
            # Extract internal refresh token
            refresh_token = response.data.pop('_refresh_token')
            
            # Set as HttpOnly cookie
            response.set_cookie(
                key=settings.REFRESH_TOKEN_COOKIE_NAME,
                value=refresh_token,
                max_age=settings.REFRESH_TOKEN_COOKIE_MAX_AGE,
                httponly=settings.REFRESH_TOKEN_COOKIE_HTTPONLY,
                secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
                samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
            )
        
        return super().finalize_response(request, response, *args, **kwargs)

@extend_schema(
    tags=['v1 - Authentication'],
    summary='User Logout',
    description='Blacklist refresh token from HttpOnly cookie and clear it. Client should delete access token.',
    responses={
        205: OpenApiResponse(description='Successfully logged out'),
        400: OpenApiResponse(description='Invalid or missing refresh token'),
    }
)
class LogoutView(APIView):
    """
    Logout view that reads refresh token from HttpOnly cookie,
    blacklists it, and clears the cookie.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Get refresh token from HttpOnly cookie (NOT from request body)
            refresh_token = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
            
            if not refresh_token:
                return Response(
                    {"error": "Refresh token not found in cookie."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Blacklist the token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Create response
            response = Response(
                {"message": "Successfully logged out."},
                status=status.HTTP_205_RESET_CONTENT
            )
            
            # Clear the refresh token cookie
            response.delete_cookie(
                key=settings.REFRESH_TOKEN_COOKIE_NAME,
                samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
            )
            
            return response
            
        except (TokenError, InvalidToken) as e:
            # Still clear the cookie even if token is invalid
            response = Response(
                {"error": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST
            )
            response.delete_cookie(
                key=settings.REFRESH_TOKEN_COOKIE_NAME,
                samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
            )
            return response
        except Exception as e:
            return Response(
                {"error": "An error occurred during logout."},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=['v1 - User Profile'],
    summary='Get/Update User Profile',
    description='Retrieve or update the authenticated user profile',
    responses={
        200: UserProfileSerializer,
        401: OpenApiResponse(description='Unauthorized'),
    }
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=['v1 - User Profile'],
    summary='Change Password',
    description='Change the authenticated user password',
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(description='Password changed successfully'),
        400: OpenApiResponse(description='Validation error or wrong password'),
    }
)
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Validate old password first
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {"old_password": "Wrong password."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Update password
            serializer.update(user, serializer.validated_data)
            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['v1 - Authentication'],
    summary='Refresh Access Token',
    description='Get a new access token using the refresh token from HttpOnly cookie. New refresh token is also rotated.',
    responses={
        200: OpenApiResponse(
            description='New access token',
            response={'type': 'object', 'properties': {'access': {'type': 'string'}}}
        ),
        401: OpenApiResponse(description='Invalid or missing refresh token'),
    }
)
class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that reads refresh token from HttpOnly cookie
    instead of request body, and sets the new rotated refresh token back as cookie.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Get refresh token from HttpOnly cookie
        refresh_token = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
        
        if not refresh_token:
            return Response(
                {"error": "Refresh token not found in cookie."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Add refresh token to request data for the parent class to process
        request.data['refresh'] = refresh_token
        
        # Call parent's post method
        response = super().post(request, *args, **kwargs)
        
        # If token rotation is enabled, set new refresh token as cookie
        if response.status_code == 200 and 'refresh' in response.data:
            new_refresh_token = response.data.pop('refresh')
            
            response.set_cookie(
                key=settings.REFRESH_TOKEN_COOKIE_NAME,
                value=new_refresh_token,
                max_age=settings.REFRESH_TOKEN_COOKIE_MAX_AGE,
                httponly=settings.REFRESH_TOKEN_COOKIE_HTTPONLY,
                secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
                samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
            )
        
        return response