# Third party libraries
from datetime import datetime, timezone
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

# Local Imports
from massitfab.settings import connectDB, disconnectDB, verifyToken, log_error
from .serializers import CreateProductSerializer, UpdateProductSerializer, UpdateProfileSerializer


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
                status=status.HTTP_404_NOT_FOUND
            )

        data = {
            'username': result[0],
            'summary': result[1],
            'profile_picture': result[2],
            'created_at': result[3].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
        return Response(
            data,
            status=status.HTTP_200_OK
        )
    except Exception as error:
        log_error('get_profile', "{}", str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.', },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_product(request, id):
    conn = None
    try:
        con = connectDB()
        cur = con.cursor()
        cur.execute("""SELECT title, description, schedule, fab_user_id, start_date, end_date, subcategory_id, hashtags, st_price, is_removed
                          FROM product WHERE id=%s;""", [id])
        result = cur.fetchall()[0]

        if result is None or result[-1] != False:
            log_error('product', "{}", 'This product is removed or does not exist')
            return Response(
                {'message': 'Product does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        resp = {
            "data": {
                "title": result[0],
                "description": result[1],
                "schedule": result[2],
                "owner": result[3],
                "start_date": result[4],
                "end_date": result[5],
                "categories": result[6],
                "hashtags": result[7],
                "price": result[8]
            },
            "message": "Амжилттай!",
        }
        return Response(
            resp,
            status=status.HTTP_200_OK
        )
    except Exception as error:
        log_error('get_product', "{}", str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)

# @api_view(["PUT"])
# def update_profile(request, id):
#     auth_header = request.headers.get('Authorization')
#     auth = verifyToken(auth_header)
#     if(auth['status'] != 200):
#         return Response(
#             {'message': auth['error']},
#             status=status.HTTP_401_UNAUTHORIZED
#         )
#     serializer = UpdateProfileSerializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
#     data = serializer.validated_data

#     conn = None
#     fab_id = auth['user_id']
#     try:
#         conn = connectDB()
#         cur = conn.cursor()

#         values = (id, fab_id)
#         cur.execute('SELECT username, summary, profile_picture, FROM fab_user WHERE id=%s;', values)
#         result = cur.fetchone()

#         if result is None:
#             return Response(
#             {'message': 'You are not authorized to update this profile!'},
#             status=status.HTTP_401_UNAUTHORIZED
#         )

#         values = (
#             data["username"],
#             data["summary"],
#             data["profile_picture"],
#             fab_id
#         )
#         cur.execute("""UPDATE SET username=%s, summary=%s, profile_picture=%s, FROM fab_user WHERE id=%s""", values)

#         conn.commit()

#         data = {
#             'message': 'Амжилттай шинэчлэгдсэн!'
#         }
#         return Response(
#             data,
#             status=status.HTTP_201_CREATED
#         )

#     except Exception as error:
#         log_error('update_profile', "{}", str(error))
#         return Response(
#             {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.',},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )
#     finally:
#         if conn is not None:
#             disconnectDB(conn)


@api_view(['POST'])
def create_product(request):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth['status'] != 200):
        return Response(
            {'message': auth['error']},
            status=status.HTTP_401_UNAUTHORIZED
        )
    serializer = CreateProductSerializer(data=request.data)
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
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.', },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)


@api_view(['PUT'])
def update_product(request, id):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth['status'] != 200):
        return Response(
            {'message': auth['error']},
            status=status.HTTP_401_UNAUTHORIZED
        )
    serializer = UpdateProductSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    conn = None
    try:
        # establish database connection
        conn = connectDB()
        cur = conn.cursor()

        values = (id, auth['user_id'])
        cur.execute(
            'SELECT id, fab_user_id FROM product WHERE id = %s AND fab_user_id = %s', values)
        content_id, uid = cur.fetchone()  # type: ignore

        if content_id is None:
            return Response(
                {'message': 'You are not authorized to edit this product!'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Use the connection's autocommit attribute to ensure all queries
        # are part of the same transaction
        # conn.autocommit = False

        # # Start a new transaction
        # cur.execute("BEGIN")

        # Execute an query using parameters
        content_data = data['content']  # type: ignore
        values = (
            content_data['title'],
            content_data['description'],
            int(content_data['subcategory_id']),
            content_data['hashtags'] if content_data['hashtags'] else '',
            float(content_data['st_price']) if content_data['st_price'] else 0,
            id,
        )
        cur.execute(
            """UPDATE product SET title=%s, description=%s, subcategory_id=%s, hashtags=%s, st_price=%s WHERE id=%s""",
            values
        )

        sources = data['source']        # type: ignore
        for source in sources:
            values = (source, content_id)
            cur.execute(
                "INSERT INTO route(source, product_id) VALUES (%s, %s)",
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
        # conn.commit()

        data = {
            'message': 'Байршуулалт шинэчлэгдлээ!'
        }
        return Response(
            data,
            status=status.HTTP_202_ACCEPTED
        )

    except Exception as error:
        log_error('create_product', data, str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.', },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)


@api_view(['PUT'])
def delete_product(request, id):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth['status'] != 200):
        return Response(
            {'message': auth['error']},
            status=status.HTTP_401_UNAUTHORIZED
        )
    serializer = UpdateProductSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    conn = None
    try:
        # establish database connection
        conn = connectDB()
        cur = conn.cursor()

        values = (id, auth['user_id'])
        cur.execute(
            'SELECT id, fab_user_id FROM product WHERE id = %s AND fab_user_id = %s', values)
        result = cur.fetchone()[0]  # type: ignore

        if result is None:
            return Response(
                {'message': 'You are not authorized to edit this product!'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        cur.execute(
            'UPDATE product SET is_removed = True WHERE id = %s AND fab_user_id = %s', values)

        # Commit the changes to the database
        conn.commit()

        data = {
            'message': 'Амжилттай устгагдлаа!'
        }
        return Response(
            data,
            status=status.HTTP_201_CREATED
        )

    except Exception as error:
        log_error('create_product', data, str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.', },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)
