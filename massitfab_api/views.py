from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Define your CRUD functions here
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_items(request):
    # Return a list of items
    items = [
        {'id': 1, 'name': 'item 1'},
        {'id': 2, 'name': 'item 2'},
        {'id': 3, 'name': 'item 3'}
    ]
    return Response(items)

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def create_item(request):
    # Create a new item
    data = request.data
    new_item = {'id': data['id'], 'name': data['name']}
    return Response(new_item)

@api_view(['PUT'])
@permission_classes((IsAuthenticated,))
def update_item(request, id):
    # Update an existing item
    data = request.data
    updated_item = {'id': id, 'name': data['name']}
    return Response(updated_item)

@api_view(['DELETE'])
@permission_classes((IsAuthenticated,))
def delete_item(request, id):
    # Delete an existing item
    return Response({'message': f'Item with ID {id} deleted.'})