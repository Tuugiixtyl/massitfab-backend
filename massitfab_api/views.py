# Third party libraries
from datetime import datetime, timezone
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status

# Local Imports
from massitfab.settings import connectDB, disconnectDB, ps, hashPassword, verifyPassword, verifyToken
from .serializers import CreateContentSerializer


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
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

        data = {
            'username': result[0],
            'summary': result[1],
            'profile_picture': result[2],
            'created_at': result[3].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
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
def create_product(request):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth['status'] != 200):
        return Response(
            {'message': auth['error']},
            status=status.HTTP_401_UNAUTHORIZED
        )
    serializer = CreateContentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    conn = None
    try:
        # establish database connection
        conn = connectDB()
        cur = conn.cursor()

        # Use the connection's autocommit attribute to ensure all queries
        # are part of the same transaction
        conn.autocommit = False

        # Start a new transaction
        cur.execute("BEGIN")

        # Execute an query using parameters
        values = (data['title'], data['description'], data['schedule'], data['start_date'], # type: ignore
                  data['end_date'], data['subcategory_id'], data['hashtags'], data['st_price'])   # type: ignore
        cur.execute(
            """INSERT INTO product 
                VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            values
        )
        content_id = cur.fetchone()[0]  # type: ignore

        # values = (data['source'], content_id)  # type: ignore
        # cur.execute(
        #     """INSERT INTO route(source, product_id) 
        #         VALUES (%s, %s)""",
        #     values
        # )

        # values = (data['resource'], content_id, data['membership_id'])  # type: ignore
        # cur.execute(
        #     """INSERT INTO gallery
        #         VALUES (DEFAULT, %s, %s, %s)""",
        #     values
        # )

        # Commit the changes to the database
        conn.commit()

        data = {
            'message': 'Амжилттай!'
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
