# Third party libraries
import os
import uuid
import base64
from datetime import datetime
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

# Local Imports
from massitfab.settings import connectDB, disconnectDB, verifyToken, log_error, json
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

        resp = {
            "data": {
                'username': result[0],
                'summary': result[1],
                'profile_picture': result[2],
                'created_at': result[3].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            },
            "message": "Амжилттай!"
        }
        return Response(
            resp,
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
        cur.execute(
            """SELECT title, description, schedule, fab_user_id, start_date, end_date, subcategory_id, hashtags, st_price, 
                created_at, updated_at, is_removed FROM product WHERE id=%s;""", [id])
        result = cur.fetchone()

        if result is None or result[-1] != False:
            log_error('product', "{}",
                      'This product is removed or does not exist')
            return Response(
                {'message': 'Product does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        cur.execute("SELECT resource FROM gallery WHERE product_id = %s", [id])
        medias = cur.fetchall()
        flat_gallery = [item for sublist in medias for item in sublist]

        cur.execute("SELECT source FROM route WHERE product_id = %s", [id])
        links = cur.fetchall()
        flat_link = [item for sublist in links for item in sublist]

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
                "price": result[8],
                "published": result[9],
                "edited": result[10],
                "gallery": flat_gallery,
                "link": flat_link
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


@api_view(["PUT"])
def update_profile(request):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth['status'] != 200):
        return Response(
            {'message': auth['error']},
            status=status.HTTP_401_UNAUTHORIZED
        )
    serializer = UpdateProfileSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    conn = None
    fab_id = auth['user_id']
    try:
        conn = connectDB()
        cur = conn.cursor()

        cur.execute(
            'SELECT username, summary, profile_picture FROM fab_user WHERE id=%s', [fab_id])
        result = cur.fetchone()

        if result is None:
            return Response(
                {'message': 'You are not authorized to update this profile!'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        upload_folder = os.path.join(settings.MEDIA_ROOT, 'public', 'img')
        pro = data['profile_picture']  # type: ignore
        profile_picture = None
        if pro:
            file_data = base64.b64decode(pro)
            filename = str(uuid.uuid4()) + '.jpg'
            with open(os.path.join(upload_folder, filename), 'wb') as f:
                f.write(file_data)
            profile_picture = os.path.join(
                upload_folder, filename).replace('\\', '/')
        values = (data['username'], data['summary'] if data['summary'] else None, profile_picture, fab_id)  # type: ignore
        cur.execute("UPDATE fab_user SET username=%s, summary=%s, profile_picture=%s WHERE id=%s", values)
        conn.commit()

        data = {
            'message': 'Амжилттай шинэчлэгдсэн!'
        }
        return Response(
            data,
            status=status.HTTP_201_CREATED
        )

    except Exception as error:
        log_error('update_profile', "{}", str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.', },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)


@api_view(['POST'])
def create_product(request, format=None):
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
            content_data['schedule'], '%Y-%m-%d %H:%M:%S.%f') if content_data['schedule'] else None
        start_date = datetime.strptime(
            content_data['start_date'], '%Y-%m-%d %H:%M:%S.%f') if content_data['start_date'] else None
        end_date = datetime.strptime(
            content_data['end_date'], '%Y-%m-%d %H:%M:%S.%f') if content_data['end_date'] else None
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
                    VALUES (DEFAULT, %s, %s, CAST(%s AS timestamp without time zone), %s, CAST(%s AS timestamp without time zone), CAST(%s AS timestamp without time zone), %s, %s, %s, DEFAULT, DEFAULT, %s) RETURNING id""",
                (*opening, schedule, auth['user_id'],
                 start_date, end_date, *ending, None)
            )
        else:
            cur.execute(
                """INSERT INTO product 
                    VALUES (DEFAULT, %s, %s, DEFAULT, %s, CAST(%s AS timestamp without time zone), CAST(%s AS timestamp without time zone), %s, %s, %s, DEFAULT, DEFAULT, %s) RETURNING id""",
                (*opening, auth['user_id'],
                 start_date, end_date, *ending, None)
            )
        content_id = cur.fetchone()[0]  # type: ignore

        sources = data['source']        # type: ignore
        if sources:
            for source in sources:
                values = (source, content_id)
                cur.execute(
                    """INSERT INTO route(source, product_id) 
                        VALUES (%s, %s)""",
                    values
                )

        # Set the upload folder to the public/img directory
        upload_folder = os.path.join(settings.MEDIA_ROOT, 'public', 'img')
        gallery_data = data['gallery']  # type: ignore
        if gallery_data:
            for data in gallery_data:
                file_data = base64.b64decode(data['resource'])

                # Generate a unique filename for the uploaded file
                filename = str(uuid.uuid4()) + '.jpg'

                # Save the uploaded file to disk
                with open(os.path.join(upload_folder, filename), 'wb') as f:
                    f.write(file_data)
                values = (os.path.join(upload_folder, filename).replace('\\', '/'), content_id,
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
        content_id, uid = cur.fetchone() or (None, None)  # type: ignore

        if content_id is None:
            return Response(
                {'message': 'You are not authorized to edit this product!'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # # Use the connection's autocommit attribute to ensure all queries are part of the same transaction
        # conn.autocommit = False

        # # Start a new transaction
        # cur.execute("BEGIN")

        # Update the product data
        content_data = data.get('content', {})
        values = (
            content_data.get('title'),
            content_data.get('description'),
            int(content_data.get('subcategory_id', 0)),
            content_data.get('hashtags', ''),
            float(content_data.get('st_price', 0)),
            id,
        )
        cur.execute(
            """UPDATE product SET title=%s, description=%s, subcategory_id=%s, hashtags=%s, st_price=%s, updated_at=now() WHERE id=%s""",
            values
        )

        # Delete deleted gallery files and rows from the database
        is_deleted = data.get('deleted', {})
        for deleted in is_deleted[0].get('gallery', []):
            # Delete the file from the Django media directory
            full_path = os.path.join(settings.MEDIA_ROOT, deleted)
            if os.path.isfile(full_path):
                os.remove(full_path)
            values = (deleted, id)
            cur.execute(
                "DELETE FROM gallery WHERE resource = %s AND product_id = %s", values
            )

        # Delete deleted source files and rows from the database
        for deleted in is_deleted[0].get('source', []):
            # Delete the file from the Django media directory
            full_path = os.path.join(settings.MEDIA_ROOT, deleted)
            if os.path.isfile(full_path):
                os.remove(full_path)
            values = (deleted, id)
            cur.execute(
                "DELETE FROM route WHERE source = %s AND product_id = %s", values
            )

        # Insert new source files into the database
        sources = data.get('source', [])
        for source in sources:
            values = (source, content_id)
            cur.execute(
                "INSERT INTO route(source, product_id) VALUES (%s, %s)",
                values
            )

        # Insert new gallery files into the database
        upload_folder = os.path.join(settings.MEDIA_ROOT, 'public', 'img')
        gallery_data = data.get('gallery', [])
        for data in gallery_data:
            file_data = base64.b64decode(data.get('resource'))

            # Generate a unique filename for the uploaded file
            filename = str(uuid.uuid4()) + '.jpg'

            # Save the uploaded file to disk
            with open(os.path.join(upload_folder, filename), 'wb') as f:
                f.write(file_data)
            values = (os.path.join(upload_folder, filename).replace('\\', '/'), content_id,
                      data.get('membership_id') if data.get('membership_id') != '' else None)
            cur.execute(
                """INSERT INTO gallery
                    VALUES (DEFAULT, %s, %s, %s)""",
                values
            )

        # Commit the changes to the database
        conn.commit()

        data = {
            'message': 'Амжилттай шинэчлэгдлээ!'
        }
        return Response(
            data,
            status=status.HTTP_202_ACCEPTED
        )

    except Exception as error:
        log_error('update_product', data, str(error))
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

    conn = None
    try:
        # establish database connection
        conn = connectDB()
        cur = conn.cursor()

        values = (id, auth['user_id'])
        cur.execute(
            'SELECT id, fab_user_id FROM product WHERE id = %s AND fab_user_id = %s', values)
        row = cur.fetchone()

        if row is None:
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
        log_error('delete_product', json.dumps(request.data), str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.', },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)
