from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import fetch_and_store_codeforces_problems, fetch_user_solved_problems
from .models import CodeforcesUser,CodeforcesProblem
from django.shortcuts import render
import requests



@api_view(['GET'])
def sync_problems(request):
    result = fetch_and_store_codeforces_problems()
    return Response({"message": result})


@api_view(['POST'])
def register_user_handle(request):
    handle = request.data.get("handle")
    if not handle:
        return Response({"error": "No handle provided"}, status=400)

    user = fetch_user_solved_problems(handle)
    if user is None:
        return Response({"error": "Failed to fetch user submissions"}, status=400)

    return Response({"message": f"{handle} registered successfully!"})


@api_view(['GET'])
def filter_problems(request):
    rating = request.query_params.get('rating')
    index = request.query_params.get('index')
    handle = request.query_params.get('handle')
    division = request.query_params.get('division')

    # Build the queryset based on the filters
    queryset = CodeforcesProblem.objects.all()
    if rating:
        queryset = queryset.filter(rating=rating)
    if index:
        queryset = queryset.filter(index__startswith=index.upper())
    if division:
        queryset = queryset.filter(division=division)

    # If user handle is provided, fetch solved problems
    solved_ids = set()
    if handle:
        try:
            user = CodeforcesUser.objects.get(handle=handle)
        except CodeforcesUser.DoesNotExist:
            user = fetch_user_solved_problems(handle)
            if user is None:
                return Response({"error": "Invalid handle or fetch failed"}, status=400)

        solved_ids = set(user.solved_problems.values_list('id', flat=True))

    # Serialize data
    results = []
    for prob in queryset:
        results.append({
            "name": prob.name,
            "contestId": prob.contest_id,
            "index": prob.index,
            "rating": prob.rating,
            "url": prob.url,
            "status": "solved" if prob.id in solved_ids else "unsolved"
        })

    return Response(results)



def filter_problems_page(request):
    rating = request.GET.get('rating')
    index = request.GET.get('index')
    handle = request.GET.get('handle')
    division = request.GET.get('division')

    problems = []
    params = {}

    if rating:
        params['rating'] = rating
    if index:
        params['index'] = index
    if handle:
        params['handle'] = handle
    if division:
        params['division'] = division

    if params:
        response = requests.get('http://localhost:8000/api/filter-problems/', params=params)
        if response.status_code == 200:
            problems = response.json()
    else:
        response = requests.get('http://localhost:8000/api/filter-problems/')
        if response.status_code == 200:
            problems = response.json()

    # Pass division list to template
    divisions = ["Div. 1", "Div. 2", "Div. 3", "Div. 4", "Educational", "Global"]

    return render(request, 'filter_problems.html', {
        'problems': problems,
        'request': request,
        'divisions': divisions
    })
