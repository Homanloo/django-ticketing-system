from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'username': self.user.username,
            'user_type': self.user.user_type,
        }
        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirmation = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirmation', 
          'first_name', 'last_name']
        # SECURITY: user_type removed from fields to prevent privilege escalation

    extra_kwargs = {
        'first_name': {'required': True},
        'last_name': {'required': True},
        'username': {'required': False},  # Can be auto-generated
    }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirmation']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        
        # Check if username already exists (if provided)
        username = attrs.get('username')
        if username and User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "A user with this username already exists."})
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        password = validated_data.pop('password')
        
        # SECURITY: Force user_type to 'customer' - agents/admins created via admin panel
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user
    
    def to_representation(self, instance):
        """
       This will make sure that the refresh token cannot be used again to generate a new token 
       (if at all someone has acquired it).
        Also, since access token has short life,
        it will be invalidated soon hopefully.
        """
        refresh = RefreshToken.for_user(instance)
        return {
            'user': {
                'id': str(instance.id),
                'email': instance.email,
                'username': instance.username,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'user_type': instance.user_type,
            },
            'access': str(refresh.access_token),
            '_refresh_token': str(refresh),  
        }

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 
                  'user_type', 'date_joined', 'is_active']  
        read_only_fields = ['id', 'email', 'username', 'user_type', 
                            'date_joined', 'is_active']  

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password_confirmation = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirmation']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance

     
