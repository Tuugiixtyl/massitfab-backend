# Third party libraries
import jwt
import json
from datetime import datetime, timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Local Imports
from massitfab.settings import connectDB, disconnectDB, ps, hashPassword, verifyPassword

# @api_view(['GET'])
# def my_view(request):
#     auth_header = request.headers.get('Authorization')
#     if auth_header:
#         auth_token = auth_header.split(' ')[1]
#         try:
#             # Extract the id from the auth
#             payload = jwt.decode(auth_token, 'secret_key', algorithms=['HS256'])
#             user_id = payload['user_id']
#             return Response({'user_id': user_id})
#         except jwt.exceptions.DecodeError:
#             return Response({'error': 'Invalid token'}, status=401)
#     else:
#         return Response({'error': 'Authorization header missing'}, status=401)

@api_view(['GET'])
def get_profile(request, username):
    conn = None

    try:
        # establish database connection
        conn = connectDB()
        cur = conn.cursor()

        # Check if user does not exists while also retrieving the information
        cur.execute(
            "SELECT username, summary, profile_picture, created_at FROM creator WHERE username = %s",
            [username]
        )
        result = cur.fetchone()

        if result is None:
            return Response(
                {'message': 'User does not exist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cusername = result[0]
        summary = result[1]
        profile_picture = result[2]
        created_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        data = {
            'username': cusername,
            'summary': summary,
            'profile_picture': profile_picture,
            'created_at': created_at
        }

        return Response(
            data,
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


@api_view(['POST'])
def create_item(request):
    # Create a new item
    data = request.data
    new_item = {'id': data['id'], 'name': data['name']}
    return Response(new_item)


@api_view(['PUT'])
def update_item(request, id):
    # Update an existing item
    data = request.data
    updated_item = {'id': id, 'name': data['name']}
    return Response(updated_item)


@api_view(['DELETE'])
def delete_item(request, id):
    # Delete an existing item
    return Response({'message': f'Item with ID {id} deleted.'})
