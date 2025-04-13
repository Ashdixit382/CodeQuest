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
    min_rating = request.query_params.get('min_rating')
    max_rating = request.query_params.get('max_rating')
    index = request.query_params.get('index')
    handle = request.query_params.get('handle')
    division = request.query_params.get('division')
    sort_by = request.query_params.get('sort_by')

    queryset = CodeforcesProblem.objects.all()

    # Apply rating range filters
    if min_rating and max_rating:
        queryset = queryset.filter(rating__gte=min_rating, rating__lte=max_rating)
    elif min_rating:
        queryset = queryset.filter(rating__gte=min_rating)
    elif max_rating:
        queryset = queryset.filter(rating__lte=max_rating)

    # Apply index filter
    if index:
        queryset = queryset.filter(index__startswith=index.upper())

    # Apply division filter
    if division:
        queryset = queryset.filter(division=division)

    # Solved problems check
    solved_ids = set()
    if handle:
        try:
            user = CodeforcesUser.objects.get(handle=handle)
        except CodeforcesUser.DoesNotExist:
            user = fetch_user_solved_problems(handle)
            if user is None:
                return Response({"error": "Invalid handle or fetch failed"}, status=400)
        solved_ids = set(user.solved_problems.values_list('id', flat=True))

    # Apply sorting if required
    if sort_by:
        if sort_by == 'rating':
            queryset = queryset.order_by('rating')
        elif sort_by == 'index':
            queryset = queryset.order_by('index')

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
    min_rating = request.GET.get('min_rating')
    max_rating = request.GET.get('max_rating')
    index = request.GET.get('index')
    handle = request.GET.get('handle')
    division = request.GET.get('division')
    sort_by = request.GET.get('sort_by')

    params = {}
    if min_rating:
        params['min_rating'] = min_rating
    if max_rating:
        params['max_rating'] = max_rating
    if index:
        params['index'] = index
    if handle:
        params['handle'] = handle
    if division:
        params['division'] = division
    if sort_by:
        params['sort_by'] = sort_by

    problems = []
    if params:
        response = requests.get('http://localhost:8000/filter-problems/', params=params)
        if response.status_code == 200:
            problems = response.json()
    else:
        response = requests.get('http://localhost:8000/filter-problems/')
        if response.status_code == 200:
            problems = response.json()        

    divisions = ["Div. 1", "Div. 2", "Div. 3", "Div. 4", "Educational", "Global"]

    return render(request, 'filter_problems.html', {
        'problems': problems,
        'request': request,
        'divisions': divisions,
    })
