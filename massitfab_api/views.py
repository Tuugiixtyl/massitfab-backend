# Third party libraries
from datetime import datetime, timezone
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

# Local Imports
from massitfab.settings import connectDB, disconnectDB, ps, hashPassword, verifyPassword, verifyToken, log_error
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
            "SELECT username, summary, profile_picture, created_at FROM fab_user WHERE username = %s",
            [username]
        )
        result = cur.fetchone()

        if result is None:
            log_error('get_profile', "{}", 'User does not exist')
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
    except Exception as error:
        log_error('get_profile', "{}", str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.',},
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
        content_data = data['content']  # type: ignore
        schedule = datetime.strptime(
            content_data['schedule'], '%Y-%m-%d %H:%M:%S.%f%z') if content_data['schedule'] else None
        start_date = datetime.strptime(
            content_data['start_date'], '%Y-%m-%d %H:%M:%S.%f%z') if content_data['start_date'] else None
        end_date = datetime.strptime(
            content_data['end_date'], '%Y-%m-%d %H:%M:%S.%f%z') if content_data['end_date'] else None
        opening = (
            content_data['title'],
            content_data['description'],
        )
        ending = (
            content_data['subcategory_id'],
            content_data['hashtags'] if content_data['hashtags'] else '',
            float(content_data['st_price']) if content_data['st_price'] else 0,
        )
        if schedule is not None:
            cur.execute(
                """INSERT INTO product 
                    VALUES (DEFAULT, %s, %s, CAST(%s AS timestamp with time zone), %s, CAST(%s AS timestamp with time zone), CAST(%s AS timestamp with time zone), %s, %s, %s) RETURNING id""",
                (*opening, schedule, auth['user_id'],
                 start_date, end_date, *ending)
            )
        else:
            cur.execute(
                """INSERT INTO product 
                    VALUES (DEFAULT, %s, %s, DEFAULT, %s, CAST(%s AS timestamp with time zone), CAST(%s AS timestamp with time zone), %s, %s, %s) RETURNING id""",
                (*opening, auth['user_id'], start_date, end_date, *ending)
            )
        content_id = cur.fetchone()[0]  # type: ignore

        sources = data['source']        # type: ignore
        for source in sources:
            values = (source, content_id)
            cur.execute(
                """INSERT INTO route(source, product_id) 
                    VALUES (%s, %s)""",
                values
            )

        gallery_data = data['gallery']  # type: ignore
        for data in gallery_data:
            values = (data['resource'], content_id,
                      data['membership_id'] if data['membership_id'] else None)
            cur.execute(
                """INSERT INTO gallery
                    VALUES (DEFAULT, %s, %s, %s)""",
                values
            )

        # Commit the changes to the database
        conn.commit()

        data = {
            'message': 'Байршуулалт амжилттай!'
        }
        return Response(
            data,
            status=status.HTTP_201_CREATED
        )
    
    except Exception as error:
        log_error('create_product', data, str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.',},
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
