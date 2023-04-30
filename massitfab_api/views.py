# Third party libraries
import os
from datetime import datetime
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import FileSystemStorage
import math
import json

# Local Imports
from massitfab.settings import connectDB, disconnectDB, verifyToken, log_error
from .serializers import CreateProductSerializer, CreateReviewSerializer, UpdateProductSerializer, UpdateProfileSerializer, AddToWishlistSerializer

# ==============================================================================
# PROFILE
# ==============================================================================


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
            "SELECT id, username, email, summary, profile_picture, balance, created_at FROM fab_user WHERE username = %s",
            [username]
        )
        result = cur.fetchone()

        if result is None:
            log_error('get_profile', json.dumps(
                {"username": username}), 'User does not exist')
            return Response(
                {'message': 'User does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get the page number and page size from the query parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 9))

        # Calculate the offset based on the page number and page size
        offset = (page - 1) * page_size

        # Query the related products with pagination
        cur.execute(
            """
                SELECT p.id, title, description, MIN(resource) as banner, st_price, created_at FROM product p
                INNER JOIN gallery g on p.id = g.product_id
                WHERE fab_user_id = %s AND is_removed = false
                GROUP BY p.id
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """,
            [result[0], page_size, offset]
        )
        results = cur.fetchall()

        # Convert the result rows to a list of dictionaries
        products = []
        for row in results:
            products.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'banner': row[3],
                'st_price': float(row[-2]),
                'created_at': row[-1].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            })

        # Get the total count of related products
        cur.execute(
            "SELECT COUNT(*) FROM product WHERE fab_user_id = %s AND is_removed = False",
            [result[0]]
        )
        total_count = cur.fetchone()[0]

        # Calculate the number of pages based on the total count and page size
        num_pages = math.ceil(total_count / page_size)

        resp = {
            "data": {
                'username': result[1],
                # 'email': result[2],
                'summary': result[3],
                'profile_picture': result[4],
                'balance': result[5],
                'created_at': result[6].strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'related_products': products,
                'list': {
                    'page': page,
                    'page_size': page_size,
                    'num_pages': num_pages,
                    'total_count': total_count
                }
            },
            "message": "Амжилттай!"
        }
        return Response(
            resp,
            status=status.HTTP_200_OK
        )
    except Exception as error:
        log_error('get_profile', json.dumps(
            {"username": username, 'data': request.data}), str(error))
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
    if(auth.get('status') != 200):
        return Response(
            {'message': auth.get('error')},
            status=status.HTTP_401_UNAUTHORIZED
        )
    serializer = UpdateProfileSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    conn = None
    fab_id = auth.get('user_id')
    try:
        conn = connectDB()
        cur = conn.cursor()

        cur.execute(
            'SELECT username, summary, profile_picture FROM fab_user WHERE id=%s', [fab_id])
        colnames = [desc[0] for desc in cur.description]
        result = cur.fetchone()

        if result is None:
            return Response(
                {'message': 'You are not authorized to update this profile!'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        else:
            result_dict = {}
            for i, value in enumerate(result):
                result_dict[colnames[i]] = value

        # Get the old profile picture from the database
        cur.execute(
            "SELECT profile_picture FROM fab_user WHERE id=%s", [fab_id])
        oldpro = str(cur.fetchone()[0])
        pro = data.get('profile_picture')
        profile_picture = None

        # Check if the request is valid
        if pro:
            file_path = os.path.join(settings.MEDIA_ROOT, 'public', 'img')
            storage = FileSystemStorage(location=file_path)

            # Remove the old profile picture from local storage
            if oldpro != 'public/img/sandy.png':
                full_path = os.path.join(settings.MEDIA_ROOT, oldpro)
                if os.path.isfile(full_path):
                    os.remove(full_path)
            filename = storage.save(pro.name, pro)
            profile_picture = os.path.join(
                file_path, filename).replace('\\', '/')
        result_dict['profile_picture'] = profile_picture

        # Add the local path into the database
        values = (data.get('username'), data.get('summary') if data.get('summary')
                  else None, profile_picture, fab_id)
        cur.execute(
            "UPDATE fab_user SET username=%s, summary=%s, profile_picture=%s WHERE id=%s", values)
        conn.commit()

        result_dict['username'] = data.get('username')
        result_dict['summary'] = data.get(
            'summary') if data.get('summary') else None
        resp = {
            "data": result_dict,
            'message': 'Амжилттай шинэчлэгдсэн!',
        }
        return Response(
            resp,
            status=status.HTTP_202_ACCEPTED
        )
    except Exception as error:
        log_error('update_profile', json.dumps(
            {"user_id": fab_id, "data": data}), str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.', },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)

# ==============================================================================
# PRODUCTS
# ==============================================================================


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_products(request):  # Recently uploaded products
    conn = None
    try:
        # establish database connection
        conn = connectDB()
        cur = conn.cursor()

        # Get pagination parameters from query string
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 9))
        offset = (page - 1) * page_size

        # Get total number of products
        cur.execute("SELECT COUNT(*) FROM product WHERE is_removed = false")
        total_count = cur.fetchone()[0]

        # Get paginated products data
        cur.execute("""
            SELECT p.id, title, description, MIN(resource) as banner, subcategory_id, st_price, created_at
            FROM product p INNER JOIN gallery g ON p.id = g.product_id
            WHERE is_removed = FALSE
            GROUP BY p.id
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, [page_size, offset])
        rows = cur.fetchall()

        # Serialize product data
        products = []
        for row in rows:
            product = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'banner': row[3],
                'subcategory_id': row[-3],
                'st_price': float(row[-2]),
                'created_at': row[-1].strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            }
            products.append(product)

        # Build response dictionary with pagination information
        resp = {
            'data': {
                "products": products,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'num_pages': math.ceil(total_count / page_size),
                    'total_count': total_count,
                }
            },
            'message': 'Амжилттай!',
        }
        return Response(resp, status=status.HTTP_200_OK)
    except Exception as error:
        log_error('get_products', json.dumps(
            {'data': request.data}), str(error))
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
def get_product_details(request, id):
    conn = None
    try:
        con = connectDB()
        cur = con.cursor()
        cur.execute(
            """SELECT title, description, schedule, fab_user_id, start_date, end_date, subcategory_id, hashtags, st_price, 
                created_at, updated_at, is_removed FROM product WHERE id=%s;""", [id])
        result = cur.fetchone()

        if result is None or result[-1] != False:
            log_error('get_product', json.dumps({'product_id': id}),
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
                "id": id,
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
        log_error('get_product', json.dumps(
            {'product_id': id, 'data': request.data}), str(error))
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
    if(auth.get('status') != 200):
        return Response(
            {'message': auth.get('error')},
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

        # content_data = data.get('content')
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
        #         (*opening, schedule, auth.get('user_id'),
        #          start_date, end_date, *ending, None)
        #     )
        # else:
        #     cur.execute(
        #         """INSERT INTO product
        #             VALUES (DEFAULT, %s, %s, DEFAULT, %s, CAST(%s AS timestamp without time zone), CAST(%s AS timestamp without time zone), %s, %s, %s, DEFAULT, DEFAULT, %s) RETURNING id""",
        #         (*opening, auth.get('user_id'),
        #          start_date, end_date, *ending, None)
        #     )
        title = data.get('title'),
        description = data.get('description'),
        user_id = auth.get('user_id'),
        subcategory_id = int(data.get('subcategory_id')),
        st_price = float(data.get('st_price')),

        # Execute an query using parameters
        values = (
            title,
            description,
            user_id,
            subcategory_id,
            st_price,
        )
        cur.execute("""INSERT INTO product(title, description, fab_user_id, subcategory_id, st_price)
                        VALUES (%s, %s, %s, %s, %s) RETURNING id;""", values)
        content_id = cur.fetchone()[0]

        sources_list = []
        sources = data.get('source')
        if sources:
            sauces = sources.split("&")
            sources_list = sources_list + sauces
            for source in sauces:
                values = (source, content_id)
                cur.execute(
                    """INSERT INTO route(source, product_id) 
                        VALUES (%s, %s)""",
                    values
                )

        # Set the upload folder to the public/img directory
        file_path = os.path.join(settings.MEDIA_ROOT, 'public', 'img')
        gallery_data = data.get('resource')
        filenames = []
        if gallery_data:
            storage = FileSystemStorage(location=file_path)
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

        resp = {
            'data': {
                'title': title[0],
                'description': description[0],
                'user_id': user_id[0],
                'subcategory_id': subcategory_id[0],
                'st_price': st_price[0],
                'link': sources_list,
                'files': filenames,
            },
            'message': 'Байршуулалт амжилттай!'
        }
        return Response(
            resp,
            status=status.HTTP_201_CREATED
        )
    except Exception as error:
        log_error('create_product', json.dumps(
            {"user_id": auth.get('user_id'), "data": data}), str(error))
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
    if(auth.get('status') != 200):
        return Response(
            {'message': auth.get('error')},
            status=status.HTTP_401_UNAUTHORIZED
        )
    serializer = UpdateProductSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    user_id = auth.get('user_id')

    conn = None
    try:
        # establish database connection
        conn = connectDB()
        cur = conn.cursor()

        values = (id, auth.get('user_id'))
        cur.execute(
            'SELECT id, fab_user_id FROM product WHERE id = %s AND fab_user_id = %s', values)
        content_id, uid = cur.fetchone() or (None, None)

        if content_id is None:
            return Response(
                {'message': 'You are not authorized to edit this product!'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Update the product data
        values = []
        query = "UPDATE product SET updated_at=now()"
        title = data.get('title')
        description = data.get('description')
        subcategory_id = data.get('subcategory_id')
        st_price = data.get('st_price')
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

        deleted_files = []
        # Delete deleted gallery files and rows from the database
        resource_deleted = data.get('resource_deleted')
        if resource_deleted:
            res_list = resource_deleted.split('&')
            deleted_files = deleted_files + res_list
            for deleted in res_list:
                # Delete the file from the Django media directory
                full_path = os.path.join(settings.MEDIA_ROOT, deleted)
                if os.path.isfile(full_path):
                    os.remove(full_path)
                values = (deleted, id)
                cur.execute(
                    "DELETE FROM gallery WHERE resource = %s AND product_id = %s", values
                )

        deleted_sources = []
        # Delete deleted source files and rows from the database
        source_deleted = data.get('source_deleted')
        if source_deleted:
            src_list = source_deleted.split('&')
            deleted_sources = deleted_sources + src_list
            for deleted in src_list:
                # Delete the file from the Django media directory
                full_path = os.path.join(settings.MEDIA_ROOT, deleted)
                if os.path.isfile(full_path):
                    os.remove(full_path)
                values = (deleted, id)
                cur.execute(
                    "DELETE FROM route WHERE source = %s AND product_id = %s", values
                )

        sources_list = []
        # Insert new source files into the database
        sources = data.get('source')
        if sources:
            srcs = sources.split('&')
            sources_list = sources_list + srcs
            for source in srcs:
                values = (source, content_id)
                cur.execute(
                    "INSERT INTO route(source, product_id) VALUES (%s, %s)",
                    values
                )

        # Insert new gallery files into the database
        file_path = os.path.join(settings.MEDIA_ROOT, 'public', 'img')
        gallery_data = data.get('resource')
        filenames = []
        if gallery_data:
            storage = FileSystemStorage(location=file_path)
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

        resp = {
            'data': {
                'title': title[0] if title else None,
                'description': description if description else None,
                'user_id': user_id,
                'subcategory_id': subcategory_id[0] if subcategory_id else None,
                'st_price': st_price[0] if st_price else None,
                'link': sources_list,
                'files': filenames,
                'deleted_link': deleted_sources,
                'deleted_files': deleted_files,
            },
            'message': 'Амжилттай шинэчлэгдлээ!'
        }
        return Response(
            resp,
            status=status.HTTP_202_ACCEPTED
        )
    except Exception as error:
        log_error('update_product', json.dumps(
            {"user_id": auth.get("user_id"), "data": data}), str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.', },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)


@api_view(['DELETE'])
def delete_product(request, id):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth.get('status') != 200):
        return Response(
            {'message': auth.get('error')},
            status=status.HTTP_401_UNAUTHORIZED
        )

    conn = None
    try:
        # establish database connection
        conn = connectDB()
        cur = conn.cursor()

        values = (id, auth.get('user_id'))
        cur.execute(
            'SELECT id, fab_user_id FROM product WHERE id = %s AND fab_user_id = %s', values)
        colnames = [desc[0] for desc in cur.description]
        row = cur.fetchone()

        if row is None:
            return Response(
                {'message': 'You are not authorized to edit this product!'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        else:
            result_dict = {}
            for i, value in enumerate(row):
                result_dict[colnames[i]] = value

        cur.execute(
            'UPDATE product SET is_removed = True WHERE id = %s AND fab_user_id = %s', values)

        # Commit the changes to the database
        conn.commit()

        resp = {
            'data': result_dict,
            'message': 'Амжилттай устгагдлаа!'
        }
        return Response(
            resp,
            status=status.HTTP_202_ACCEPTED
        )

    except Exception as error:
        log_error('delete_product', json.dumps({"user_id": auth.get(
            'user_id'), "product_id": id, "data": request.data}), str(error))
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
def search_products(request):
    keyword = str(request.GET.get('keyword', ''))
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 9))

    conn = None
    try:
        conn = connectDB()
        cur = conn.cursor()

        # get the total number of matching products
        cur.execute(
            "SELECT COUNT(*) FROM product WHERE title ILIKE %s AND is_removed = false", ['%'+keyword+'%'])
        total_count = cur.fetchone()[0]

        # get a list of products matching the keyword, paginated
        cur.execute(
            """SELECT p.id, title, description, MIN(resource) as banner, subcategory_id, st_price, created_at 
                FROM product p INNER JOIN gallery g ON p.id = g.product_id
                WHERE is_removed = false AND title ILIKE %s
                GROUP BY p.id 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s""",
            ['%'+keyword+'%', limit, (page-1)*limit]
        )
        rows = cur.fetchall()

        products = []
        for row in rows:
            products.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'banner': row[3],
                'subcategory_id': row[-3],
                'price': row[-2],
                'created_at': row[-1].strftime('%Y-%m-%dT%H:%M:%S')
            })

        resp = {
            'data': {
                'products': products,
                'pagination': {
                    'page': page,
                    'page_size': limit,
                    'num_pages': math.ceil(total_count / limit),
                    'total_count': total_count,
                }
            },
            'message': 'Амжилттай!'
        }

        return Response(resp, status=status.HTTP_200_OK)
    except Exception as error:
        log_error('search_product', json.dumps(
            {"keyword": keyword, "page": page, "limit": limit, 'data': request.data}), str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.', },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)

# ==============================================================================
# WISHLISTING
# ==============================================================================


@api_view(['POST'])
# User should not be able to add it's own products to this list
def add_n_remove_from_wishlist(request):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth.get('status') != 200):
        return Response(
            {'message': auth.get('error')},
            status=status.HTTP_401_UNAUTHORIZED
        )
    serializer = AddToWishlistSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    product_id = int(data.get('product_id'))
    user_id = auth.get('user_id')

    conn = None
    try:
        conn = connectDB()
        cur = conn.cursor()

        # Check if product exists
        cur.execute(
            "SELECT id FROM product WHERE id = %s",
            [product_id]
        )
        result = cur.fetchone()
        if result is None:
            log_error('add_to_wishlist', json.dumps(
                {"message": 'Энэхүү бүтээгдэхүүн нь систэмд бүртгэлгүй байна.', "data": data}), 'error. result is none')
            return Response({'message': 'Энэхүү бүтээгдэхүүн нь систэмд бүртгэлгүй байна.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if product is already in wishlist
        cur.execute(
            "SELECT id FROM wishlist WHERE fab_user_id = %s AND product_id = %s",
            [user_id, product_id]
        )
        result = cur.fetchone()
        if result is not None:
            cur.execute("DELETE FROM wishlist WHERE id=%s", [result])
            conn.commit()
            return Response({'message': 'Хүслийн жагсаалтнаас амжилттай хасагдлаа!'}, status=status.HTTP_200_OK)

        # Add product to wishlist
        cur.execute(
            "INSERT INTO wishlist (fab_user_id, product_id) VALUES (%s, %s) RETURNING id",
            [user_id, product_id]
        )
        wishlist_id = cur.fetchone()[0]
        conn.commit()

        resp = {
            'data': {
                'product_id': product_id,
                'wishlist_id': wishlist_id,
                'user_id': user_id,
            },
            'message': 'Хүслийн жагсаалтад амжилттай бүртгэгдлээ!',
        }
        return Response(resp, status=status.HTTP_201_CREATED)
    except Exception as e:
        log_error('add_to_wishlist', json.dumps(
            {'user_id': user_id, 'product_id': product_id, "data": data}), str(e))
        return Response({'message': 'Unable to add product to wishlist'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if conn is not None:
            disconnectDB(conn)


@api_view(['GET'])
def get_wishlist(request):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth.get('status') != 200):
        return Response(
            {'message': auth.get('error')},
            status=status.HTTP_401_UNAUTHORIZED
        )
    user_id = auth.get('user_id')
    page_size = request.query_params.get('page_size', 10)
    page_number = request.query_params.get('page_number', 1)

    conn = None
    try:
        conn = connectDB()
        cur = conn.cursor()

        # Get count of total wishlist items
        cur.execute(
            "SELECT COUNT(*) FROM wishlist WHERE fab_user_id = %s",
            [user_id]
        )
        total_items = cur.fetchone()[0]

        # Calculate offset and limit for pagination
        offset = (page_number - 1) * page_size
        limit = page_size

        # Get wishlist items for the requested page
        cur.execute(
            "SELECT product.id, product.title, product.st_price FROM product JOIN wishlist ON wishlist.product_id = product.id WHERE wishlist.fab_user_id = %s ORDER BY wishlist.created_at DESC OFFSET %s LIMIT %s",
            [user_id, offset, limit]
        )
        wishlist_items = []
        for row in cur.fetchall():
            wishlist_items.append({
                'id': row[0],
                'title': row[1],
                'st_price': row[2],
            })

        # Build response
        resp = {
            'data': {
                'wishlist_items': wishlist_items,
                'total_items': total_items,
                'page_size': page_size,
                'page_number': page_number,
            },
            'message': 'Амжилттай!',
        }

        return Response(resp, status=status.HTTP_200_OK)
    except Exception as e:
        log_error('get_wishlist', json.dumps(
            {"user_id": user_id, "data": request.data}), str(e))
        return Response({'message': 'Хүслийн жагсаалт руу хандаж чадсангүй!'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if conn is not None:
            disconnectDB(conn)
            
@api_view(['GET'])
def get_allWishlist(request):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth.get('status') != 200):
        return Response(
            {'message': auth.get('error')},
            status=status.HTTP_401_UNAUTHORIZED
        )
    user_id = auth.get('user_id')

    conn = None
    try:
        conn = connectDB()
        cur = conn.cursor()

        # Get count of total wishlist items
        cur.execute(
            "SELECT COUNT(*) FROM wishlist WHERE fab_user_id = %s",
            [user_id]
        )
        total_items = cur.fetchone()[0]

        # Get wishlist items for the requested page
        cur.execute(
            "SELECT product.id, product.title, product.st_price FROM product JOIN wishlist ON wishlist.product_id = product.id WHERE wishlist.fab_user_id = %s ORDER BY wishlist.created_at DESC",
            [user_id]
        )
        wishlist_items = []
        for row in cur.fetchall():
            wishlist_items.append({
                'id': row[0],
                'title': row[1],
                'st_price': row[2],
            })

        # Build response
        resp = {
            'data': {
                'wishlist_items': wishlist_items,
                'total_items': total_items,
            },
            'message': 'Амжилттай!',
        }

        return Response(resp, status=status.HTTP_200_OK)
    except Exception as e:
        log_error('get_allWishlist', json.dumps(
            {"user_id": user_id, "data": request.data}), str(e))
        return Response({'message': 'Хүслийн жагсаалт руу хандаж чадсангүй!'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if conn is not None:
            disconnectDB(conn)

# ==============================================================================
# REVIEWS
# ==============================================================================


@api_view(['POST'])
def create_review(request, product_id):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth.get('status') != 200):
        return Response(
            {'message': auth.get('error')},
            status=status.HTTP_401_UNAUTHORIZED
        )
    serializer = CreateReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    user_id = auth.get('user_id')

    conn = None
    try:
        conn = connectDB()
        cur = conn.cursor()

        # check if the product exists
        cur.execute(
            "SELECT id FROM product WHERE id = %s", [product_id]
        )
        result = cur.fetchone()

        if result is None:
            log_error('create_review', json.dumps(
                {"product_id": product_id}), 'Product does not exist')
            return Response(
                {'message': 'Product does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )

        # insert review into the database
        cur.execute(
            "INSERT INTO review (score, comment, fab_user_id, product_id) VALUES (%s, %s, %s, %s) RETURNING id",
            [int(data.get('score')), data.get('comment', None),
             user_id, product_id]
        )
        review_id = cur.fetchone()[0]
        conn.commit()

        resp = {
            "data": {
                "id": review_id,
                "score": data.get('score'),
                "comment": data.get('comment', None),
                "fab_user_id": user_id,
                "product_id": product_id,
                "created_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            },
            "message": "Амжилттай!"
        }
        return Response(
            resp,
            status=status.HTTP_201_CREATED
        )
    except Exception as error:
        log_error('create_review', json.dumps(
            {"product_id": product_id, 'data': request.data}), str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг хийхэд алдаа гарлаа.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_reviews(request, product_id):
    conn = None
    try:
        # establish database connection
        conn = connectDB()
        cur = conn.cursor()

        # get pagination parameters from request
        limit = int(request.GET.get('limit', 20))
        cursor = int(request.GET.get('cursor', 0))

        # retrieve reviews using cursor-based pagination
        cur.execute(
            """SELECT id, score, comment, fab_user_id, created_at FROM review WHERE product_id=%s AND id > %s ORDER BY id LIMIT %s""",
            [product_id, cursor, limit]
        )
        rows = cur.fetchall()

        # construct response data
        reviews = []
        for row in rows:
            review = {
                'id': row[0],
                'score': row[1],
                'comment': row[2],
                'user_id': row[3],
                'created_at': row[4].strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            }
            reviews.append(review)

        # construct response with pagination information
        resp = {
            "data": {
                'reviews': reviews,
                "pagination": {
                    "has_next": bool(rows),
                    "cursor": rows[-1][0] if rows else None
                },
            },
            "message": "Амжилттай!"
        }

        return Response(resp, status=status.HTTP_200_OK)
    except Exception as error:
        log_error('get_reviews', json.dumps(
            {"product_id": product_id, 'data': request.data}), str(error))
        return Response({'message': 'Дотоод алдаа!'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if conn is not None:
            disconnectDB(conn)


@api_view(['DELETE'])
def delete_review(request, review_id):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth.get('status') != 200):
        return Response(
            {'message': auth.get('error')},
            status=status.HTTP_401_UNAUTHORIZED
        )

    conn = None
    try:
        # establish database connection
        conn = connectDB()
        cur = conn.cursor()

        # Check if review exists
        cur.execute(
            "SELECT * FROM review WHERE id = %s", [review_id]
        )
        colnames = [desc[0] for desc in cur.description]
        result = cur.fetchone()

        if result is None:
            log_error('delete_review', "{}", 'Review does not exist')
            return Response(
                {'message': 'Review does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
        else:
            result_dict = {}
            for i, value in enumerate(result):
                result_dict[colnames[i]] = value

        # Check if user is authorized to delete the review
        user_id = auth.get('user_id')
        if user_id != result[3]:
            log_error('delete_review', "{}", 'Unauthorized')
            return Response(
                {'message': 'Unauthorized'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Delete the review
        cur.execute(
            "DELETE FROM review WHERE id = %s", [review_id]
        )
        conn.commit()

        resp = {
            'data': result_dict,
            "message": "Амжилттай устгалаа!"
        }
        return Response(
            resp,
            status=status.HTTP_200_OK
        )

    except Exception as error:
        log_error('delete_review', json.dumps(
            {"review_id": review_id, 'data': request.data}), str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.', },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)

# ==============================================================================
# CART
# ==============================================================================


@api_view(['GET'])
def get_cart_details(request):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth.get('status') != 200):
        return Response(
            {'message': auth.get('error')},
            status=status.HTTP_401_UNAUTHORIZED
        )
    user_id = auth.get('user_id')

    conn = None
    try:
        # establish database connection
        conn = connectDB()
        cur = conn.cursor()

        cur.execute(
            """SELECT p.id, title, MIN(resource), st_price FROM customer c 
                INNER JOIN product p ON p.id=c.product_id INNER JOIN gallery g ON p.id=g.product_id
                WHERE in_cart = TRUE AND is_bought = FALSE AND c.fab_user_id = %s
                GROUP BY p.id, title, st_price""",
            [user_id]
        )
        rows = cur.fetchall()

        # construct response data
        columns = cur.description
        respRow = [{columns[index][0]:column for index,
                    column in enumerate(value)} for value in rows]

        # calculate the total price of each rows
        total_price = 0
        for row in respRow:
            total_price += row.get("st_price", 0)

        # construct response with information
        resp = {
            "data": {
                'in_cart': respRow,
                'total_in_cart': len(respRow),
                'total_price': total_price,
            },
            "message": "Амжилттай!"
        }

        return Response(resp, status=status.HTTP_200_OK)
    except Exception as error:
        log_error('get_wishlist_details', json.dumps(
            {"user_id": user_id, 'data': request.data}), str(error))
        return Response({'message': 'Дотоод алдаа!'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if conn is not None:
            disconnectDB(conn)


@api_view(['POST'])
def add_n_remove_from_cart(request, product_id):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth.get('status') != 200):
        return Response(
            {'message': auth.get('error')},
            status=status.HTTP_401_UNAUTHORIZED
        )
    user_id = auth.get('user_id')

    conn = None
    try:
        conn = connectDB()
        cur = conn.cursor()

        # Check if it's already in the cart
        cur.execute(
            "SELECT * FROM customer WHERE product_id = %s AND in_cart = true",
            [product_id]
        )
        result = cur.fetchone()

        if result is not None:
            # Check if user is authorized to modify
            user_id = auth.get('user_id')
            if user_id != result[1]:
                log_error('add_n_remove_from_cart', json.dumps(), 'Unauthorized')
                return Response(
                    {'message': 'Unauthorized'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if result[-1] == True:
                log_error('add_n_remove_from_cart', "{}",
                        'Product is already purchased')
                return Response(
                    {'message': 'Product is already purchased'},
                    status=status.HTTP_404_NOT_FOUND
                )

            cur.execute("DELETE FROM customer WHERE id = %s", [result[0]])
            conn.commit()
            return Response({'message': 'Сагснаас амжилттай хасагдлаа!'}, status=status.HTTP_200_OK)

        # Add product to cart
        cur.execute("INSERT INTO customer (fab_user_id, product_id) VALUES (%s, %s) RETURNING id", [
                    user_id, product_id])

        cart_id = cur.fetchone()[0]
        conn.commit()

        resp = {
        'data': {
            "cart_id": cart_id,
            "user_id": user_id,
            "product_id": product_id,
        },
        "message": "Сагсанд амжилттай нэмэгдлээ!",
        }
        return Response(
            resp,
            status=status.HTTP_201_CREATED,
        )
    except Exception as error:
        log_error('add_n_remove_from_cart', json.dumps(
            {"product_id": product_id, "user_id": user_id, 'data': request.data}), str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.', },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)


@api_view(['POST'])
# One click buy everything. Also check if there are any items favorited and update the wishlist
def checkout_cart(request):
    auth_header = request.headers.get('Authorization')
    auth = verifyToken(auth_header)
    if(auth.get('status') != 200):
        return Response(
            {'message': auth.get('error')},
            status=status.HTTP_401_UNAUTHORIZED
        )
    user_id = auth.get('user_id')

    conn = None
    try:
        conn = connectDB()
        cur = conn.cursor()

        # Calculate total price
        cur.execute("""SELECT SUM(st_price) as total_price FROM customer c LEFT JOIN product p on c.product_id=p.id
                        WHERE c.fab_user_id = %s AND c.in_cart = true""", [user_id])
        total_amount = cur.fetchone()[0] or (0)

        # Get the user's current balance
        cur.execute("SELECT balance FROM fab_user WHERE id = %s", [user_id])
        user_balance = cur.fetchone()[0]

        # Check if the user can purchase the items in the cart
        equals = user_balance - total_amount
        if equals < 0:
            return Response({'message': 'Уучлаарай, үлдэгдэл хүрэлцэхгүй байна.'},
                            status=status.HTTP_406_NOT_ACCEPTABLE
                            )

        # Finalize the request
        cur.execute(
            "UPDATE customer SET in_cart = false, is_bought = true WHERE fab_user_id = %s AND in_cart = true", [user_id])
        affected_rows = cur.rowcount
        cur.execute("UPDATE fab_user SET balance = %s WHERE id = %s", [
                    equals, user_id])
        conn.commit()

        resp = {
            'data': {
                'balance': equals,
                'bought_items': affected_rows,
            },
            "message": "Амжилттай!",
        }
        return Response(
            resp,
            status=status.HTTP_202_ACCEPTED
        )
    except Exception as error:
        log_error('checkout_cart', json.dumps(
            {"user_id": user_id, 'data': request.data}), str(error))
        return Response(
            {'message': 'Уучлаарай, үйлдлийг гүйцэтгэхэд алдаа гарлаа.', },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if conn is not None:
            disconnectDB(conn)


@api_view(['DELETE'])
def remove_all_from_cart(request):
    pass

# ==============================================================================
# EXTRAS
# ==============================================================================


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_categories(request):
    conn = None
    try:
        # establish database connection
        conn = connectDB()
        cur = conn.cursor()

        # Get all categories from the "category" table
        cur.execute("SELECT * from category")
        categories = cur.fetchall()

        # Loop through each category and get its related subcategories
        resp = []
        for category in categories:
            flattened_dict = {}
            cur.execute(
                "SELECT id, name FROM subcategory WHERE category_id = %s", (category[0],))
            subcategories = cur.fetchall()
            for item in subcategories:
                flattened_dict.update({item[0]: item[1]})

            # Assign the subcategories to the category key in a dictionary
            category_dict = {
                "id": category[0],
                "category": category[1],
                "subcategories": flattened_dict,
            }
            resp.append(category_dict)

        # construct response with information
        resp = {
            "data": {
                "categories": resp,
            },
            "message": "Амжилттай!"
        }

        return Response(resp, status=status.HTTP_200_OK)
    except Exception as error:
        log_error('get_categories', json.dumps(
            {'data': request.data}), str(error))
        return Response({'message': 'Дотоод алдаа!'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if conn is not None:
            disconnectDB(conn)


@api_view(['PUT'])
def change_email(request):
    pass


@api_view(['PUT'])
def change_password(request):
    pass


@api_view(['PUT'])
def one_click_buy(request):  # check if the product was in wish list and update that as well
    pass
