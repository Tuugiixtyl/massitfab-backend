# Third Party Libraries
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

# Local Imports
from massitfab.settings import connectDB, disconnectDB, ps, hashPassword, verifyPassword, log_error
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
                (data['email'], data['username'])   # type: ignore
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
            password = hashPassword(data['password'])   # type: ignore
            cur.execute(
                "INSERT INTO fab_user (username, email, password) VALUES (%s, %s, %s) RETURNING id",
                (data['username'], data['email'], password) # type: ignore
            )
            user_id = cur.fetchone()[0] # type: ignore
            conn.commit()

            # Generate Token
            user_id = Fab_user(user_id)
            refresh = RefreshToken.for_user(user_id)

            return Response(
                {
                    'access': str(refresh.access_token),
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
                "SELECT id, username, password FROM fab_user WHERE email = %s",
                (data['email'],)    # type: ignore
            )
            result = cur.fetchone()

            if result is None:
                log_error('Login', data, 'Майл хаяг буруу байна.')
                return Response(
                    {'message': 'Майл хаяг эсвэл нууц үг буруу байна.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user_id, username, password = result
            user_pass = hashPassword(data['password'])  # type: ignore
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
            access_payload = {
                'username': username,
                'user_id': user_id_serialized,
            }
            access = refresh.access_token
            # access['username'] = access_payload['username']

            cur.execute(
                f"UPDATE fab_user SET refresh_token = %s WHERE id = %s",
                (str(refresh), user_id_serialized['id'])
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