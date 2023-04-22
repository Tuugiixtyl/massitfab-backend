# Third Party Libraries
import jwt
import time
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

# Local Imports
from massitfab.settings import connectDB, disconnectDB, ps, hashPassword, verifyPassword, log_error, SECRET_KEY as sandy
from .serializers import RegisterUserSerializer, LoginUserSerializer, FabUserSerializer
from .classess import Fab_user

class RegisterUserApi(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        conn = None
        try:
            # establish database connection
            conn = connectDB()
            cur = conn.cursor()

            # Check if email or username already exists
            cur.execute(
                "SELECT id FROM fab_user WHERE email = %s OR username = %s",
                (data.get('email'), data.get('username'))   
            )
            result = cur.fetchone()
            # is_active True uyd shalgah
            if result is not None:
                log_error('Register', data, 'Тухайн майл хаяг эсвэл нэр дээр өөр хэрэглэгч бүртгэлтэй байна.')
                return Response(
                    {'message': 'Тухайн майл хаяг эсвэл нэр дээр өөр хэрэглэгч бүртгэлтэй байна.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create user
            password = hashPassword(data.get('password'))   
            cur.execute(
                "INSERT INTO fab_user (username, email, password) VALUES (%s, %s, %s) RETURNING id",
                (data.get('username'), data.get('email'), password) 
            )
            user_id = cur.fetchone()[0] 
            conn.commit()

            # Generate Token
            user_id = Fab_user(user_id)
            refresh = RefreshToken.for_user(user_id)
            access = refresh.access_token
            access['username'] = data.get('username')

            return Response(
                {
                    'access': str(access),
                    # 'refresh': str(refresh),
                    'message': 'Бүртгэл амжилттай!'
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as error:
            log_error('Register', data, str(error))
            return Response(
                {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.',},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if conn is not None:
                disconnectDB(conn)


class LoginUserApi(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = LoginUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        conn = None
        try:
            conn = connectDB()
            cur = conn.cursor()

            # Check if email exists
            cur.execute(
                "SELECT id, username, email, password, summary, profile_picture, balance, refresh_token, created_at FROM fab_user WHERE email = %s",
                (data.get('email'),)    
            )
            result = cur.fetchone()

            if result is None:
                log_error('Login', data, 'Майл хаяг буруу байна.')
                return Response(
                    {'message': 'Майл хаяг эсвэл нууц үг буруу байна.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user_id, username, email, password, summary, profile_picture, balance, refresh_token, created_at = result
            access_payload = {
                'username': username,
                'email': email,
                'summary': summary,
                'profilePic': profile_picture,
                'balance': balance,
                'joinDate': created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            # decoded_token = jwt.decode(refresh_token, sandy, algorithms=["HS256"])
            # current_time = time.time()
            # expiration_time = decoded_token.get("exp")
            # is_expired = current_time > expiration_time

            user_pass = hashPassword(data.get('password'))  
            if not verifyPassword(user_pass, password):
                log_error('Login', data, 'Нууц үг буруу байна.')
                return Response(
                    {'message': 'Майл хаяг эсвэл нууц үг буруу байна.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate Token
            user_id = Fab_user(user_id)
            user_id_serialized = FabUserSerializer(user_id).data
            refresh = RefreshToken.for_user(user_id)
            access = refresh.access_token
            access['username'] = access_payload.get('username')
            # access['email'] = access_payload.get('email')
            # access['summary'] = access_payload.get('summary')
            # access['profilePic'] = access_payload.get('profilePic')
            # access['balance'] = access_payload.get('balance')
            # access['joinDate'] = access_payload.get('joinDate')

            cur.execute(
                f"UPDATE fab_user SET refresh_token = %s WHERE id = %s",
                (str(refresh), user_id_serialized.get('id'))
            )
            conn.commit()

            return Response(
                {
                    'access': str(access),
                    # 'refresh': str(refresh),
                    'message': 'Амжилттай!'
                },
                status=status.HTTP_200_OK
            )
        except Exception as error:
            log_error('Login', data, str(error))
            return Response(
                {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.',},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if conn is not None:
                disconnectDB(conn)