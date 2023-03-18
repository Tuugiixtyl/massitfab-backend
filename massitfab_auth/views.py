# Third Party Libraries
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

# Local Imports
from massitfab.settings import connectDB, disconnectDB, ps, hashPassword, verifyPassword
from .serializers import RegisterUserSerializer, LoginUserSerializer, CreatorSerializer
from .classess import Creator

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
                "SELECT id FROM creator WHERE email = %s OR username = %s",
                (data['email'], data['username'])
            )
            result = cur.fetchone()
            if result is not None:
                return Response(
                    {'message': 'User with this email or username already exists'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create user
            password = hashPassword(data['password'])
            cur.execute(
                "INSERT INTO creator (username, email, password) VALUES (%s, %s, %s) RETURNING id",
                (data['username'], data['email'], password)
            )
            user_id = cur.fetchone()[0]
            conn.commit()

            # Generate Token
            user_id = Creator(user_id)
            refresh = RefreshToken.for_user(user_id)

            return Response(
                {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                },
                status=status.HTTP_201_CREATED
            )
        except (Exception, ps.DatabaseError) as error:
            return Response(
                {'message': str(error)},
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
                "SELECT id, username, password FROM creator WHERE email = %s",
                (data['email'],)
            )
            result = cur.fetchone()

            if result is None:
                return Response(
                    {'message': 'Invalid email or password'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user_id, username, password = result
            user_pass = hashPassword(data['password'])
            if not verifyPassword(user_pass, password):
                return Response(
                    {'message': 'Invalid email or password'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate Token
            user_id = Creator(user_id)
            user_id_serialized = CreatorSerializer(user_id).data
            refresh = RefreshToken.for_user(user_id)
            access_payload = {
                'username': username,
                'user_id': user_id_serialized,
            }
            access = refresh.access_token
            # access['username'] = access_payload['username']

            cur.execute(
                f"UPDATE creator SET refresh_token = %s WHERE id = %s",
                (str(refresh), user_id_serialized['id'])
            )
            conn.commit()

            return Response(
                {
                    'access': str(access),
                    'refresh': str(refresh),
                },
                status=status.HTTP_200_OK
            )
        except (Exception, ps.DatabaseError) as error:
            return Response(
                {'message': str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if conn is not None:
                disconnectDB(conn)