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
from django.core.files.storage import FileSystemStorage

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
        cur.execute(
            "SELECT profile_picture FROM fab_user WHERE id=%s", [fab_id])
        oldpro = str(cur.fetchone()[0])  # type: ignore
        pro = data.get('profile_picture').read()  # type: ignore
        profile_picture = None
        if pro:
            # file_data = base64.b64decode(pro)
            file_data = pro
            filename = str(uuid.uuid4()) + '.jpg'
            if oldpro != 'public/img/sandy.png':
                full_path = os.path.join(settings.MEDIA_ROOT, oldpro)
                if os.path.isfile(full_path):
                    os.remove(full_path)
            with open(os.path.join(upload_folder, filename), 'wb') as f:
                f.write(file_data)
            profile_picture = os.path.join(
                upload_folder, filename).replace('\\', '/')
        values = (data.get('username'), data.get('summary') if data.get('summary')  # type: ignore
                  else None, profile_picture, fab_id)  # type: ignore
        cur.execute(
            "UPDATE fab_user SET username=%s, summary=%s, profile_picture=%s WHERE id=%s", values)
        conn.commit()

        data = {
            'message': 'Амжилттай шинэчлэгдсэн!'
        }
        return Response(
            data,
            status=status.HTTP_202_ACCEPTED
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

        # content_data = data.get('content')  # type: ignore
        # schedule = datetime.strptime(content_data.get('schedule'), '%Y-%m-%d %H:%M:%S.%f') if content_data.get('schedule') else None
        # start_date = datetime.strptime(content_data.get('start_date'), '%Y-%m-%d %H:%M:%S.%f') if content_data.get('start_date') else None
        # end_date = datetime.strptime(content_data.get('end_date'), '%Y-%m-%d %H:%M:%S.%f') if content_data.get('end_date') else None
        # opening = (
        #     content_data.get('title'),
        #     content_data.get('description'),
        # )
        # ending = (
        #     content_data.get('subcategory_id'),
        #     content_data.get('hashtags') if content_data.get('hashtags') else '',
        #     float(content_data.get('st_price')) if content_data.get('st_price') else 0,
        # )
        # if schedule is not None:
        #     cur.execute(
        #         """INSERT INTO product
        #             VALUES (DEFAULT, %s, %s, CAST(%s AS timestamp without time zone), %s, CAST(%s AS timestamp without time zone), CAST(%s AS timestamp without time zone), %s, %s, %s, DEFAULT, DEFAULT, %s) RETURNING id""",
        #         (*opening, schedule, auth['user_id'],
        #          start_date, end_date, *ending, None)
        #     )
        # else:
        #     cur.execute(
        #         """INSERT INTO product
        #             VALUES (DEFAULT, %s, %s, DEFAULT, %s, CAST(%s AS timestamp without time zone), CAST(%s AS timestamp without time zone), %s, %s, %s, DEFAULT, DEFAULT, %s) RETURNING id""",
        #         (*opening, auth['user_id'],
        #          start_date, end_date, *ending, None)
        #     )

        # Execute an query using parameters
        values = (
            data.get('title'),  # type: ignore
            data.get('description'),  # type: ignore
            auth['user_id'],
            int(data.get('subcategory_id')),  # type: ignore
            float(data.get('st_price', 0)) # type: ignore
        )
        cur.execute("""INSERT INTO product(title, description, fab_user_id, subcategory_id, st_price)
                        VALUES (%s, %s, %s, %s, %s) RETURNING id;""", values)
        content_id = cur.fetchone()[0]  # type: ignore

        sources = data.get('source')        # type: ignore
        if sources:
            sauces = sources.split("&")
            for source in sauces:
                values = (source, content_id)
                cur.execute(
                    """INSERT INTO route(source, product_id) 
                        VALUES (%s, %s)""",
                    values
                )

        # Set the upload folder to the public/img directory
        file_path = os.path.join(settings.MEDIA_ROOT, 'public', 'img')
        gallery_data = data.get('resource')  # type: ignore
        if gallery_data:
            storage = FileSystemStorage(location=file_path)
            filenames = []
            for image_file in gallery_data:
                filename = storage.save(image_file.name, image_file)
                filenames.append(filename)
                values = (os.path.join(file_path, filename).replace(
                    '\\', '/'), content_id)
                cur.execute(
                    """INSERT INTO gallery (resource, product_id)
                        VALUES (%s, %s)""",
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

        # Update the product data
        values = []
        query = "UPDATE product SET updated_at=now()"
        title = data.get('title') # type: ignore
        description = data.get('description') # type: ignore
        subcategory_id = data.get('subcategory_id') # type: ignore
        st_price = data.get('st_price') # type: ignore
        if title:
            query += ", title=%s"
            values.append(title)
        if description:
            query += ", description=%s"
            values.append(description)
        if subcategory_id:
            query += ", subcategory_id=%s"
            values.append(int(subcategory_id))
        if st_price:
            query += ", st_price=%s"
            values.append(float(st_price))
        query += " WHERE id=%s"
        values.append(id)
        cur.execute(query, values)

        # Delete deleted gallery files and rows from the database
        resource_deleted = data.get('resource_deleted') # type: ignore
        if resource_deleted:
            res_list = resource_deleted.split('&')
            for deleted in res_list:
                # Delete the file from the Django media directory
                full_path = os.path.join(settings.MEDIA_ROOT, deleted)
                if os.path.isfile(full_path):
                    os.remove(full_path)
                values = (deleted, id)
                cur.execute(
                    "DELETE FROM gallery WHERE resource = %s AND product_id = %s", values
                )

        # Delete deleted source files and rows from the database
        source_deleted = data.get('source_deleted') # type: ignore
        if source_deleted:
            src_list = source_deleted.split('&')
            for deleted in src_list:
                # Delete the file from the Django media directory
                full_path = os.path.join(settings.MEDIA_ROOT, deleted)
                if os.path.isfile(full_path):
                    os.remove(full_path)
                values = (deleted, id)
                cur.execute(
                    "DELETE FROM route WHERE source = %s AND product_id = %s", values
                )

        # Insert new source files into the database
        sources = data.get('source') # type: ignore
        if sources:
            srcs = sources.split('&')
            for source in srcs:
                values = (source, content_id)
                cur.execute(
                    "INSERT INTO route(source, product_id) VALUES (%s, %s)",
                    values
                )

        # Insert new gallery files into the database
        file_path = os.path.join(settings.MEDIA_ROOT, 'public', 'img')
        gallery_data = data.get('resource')  # type: ignore
        if gallery_data:
            storage = FileSystemStorage(location=file_path)
            filenames = []
            for image_file in gallery_data:
                filename = storage.save(image_file.name, image_file)
                filenames.append(filename)
                values = (os.path.join(file_path, filename).replace(
                    '\\', '/'), content_id)
                cur.execute(
                    """INSERT INTO gallery (resource, product_id)
                        VALUES (%s, %s)""",
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
