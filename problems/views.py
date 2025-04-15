from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import fetch_and_store_codeforces_problems, fetch_user_solved_problems , filter_codeforces_problems 
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

    problems, solved_ids = filter_codeforces_problems(min_rating, max_rating, index, handle, division, sort_by)

    if problems is None:
        return Response({"error": "Invalid handle or fetch failed"}, status=400)

    results = []
    for prob in problems:
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

    problems, solved_ids = filter_codeforces_problems(min_rating, max_rating, index, handle, division, sort_by)

    if problems is None:
        return render(request, 'filter_problems.html', {'error': 'Failed to fetch problems or invalid handle'})

    # ✅ Add status to each problem
    for prob in problems:
        prob.status = "solved" if prob.id in solved_ids else "unsolved"

    divisions = ["Div. 1", "Div. 2", "Div. 3", "Div. 4", "Educational", "Global"]
    return render(request, 'filter_problems.html', {
        'problems': problems,
        'request': request,
        'divisions': divisions,
    })


#sd