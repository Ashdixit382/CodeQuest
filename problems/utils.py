import requests
from .models import CodeforcesProblem, CodeforcesUser

def get_division_map():
    url = "https://codeforces.com/api/contest.list"
    response = requests.get(url)
    data = response.json()
    division_map = {}

    if data["status"] != "OK":
        return division_map

    for contest in data["result"]:
        contest_id = contest["id"]
        name = contest["name"]
        division = None

        if "Div. 1" in name:
            division = "Div. 1"
        elif "Div. 2" in name:
            division = "Div. 2"
        elif "Div. 3" in name:
            division = "Div. 3"
        elif "Div. 4" in name:
            division = "Div. 4"
        elif "Educational" in name:
            division = "Educational"
        elif "Global Round" in name:
            division = "Global"

        division_map[contest_id] = division

    return division_map


def fetch_and_store_codeforces_problems():
    print("Fetching problems from Codeforces...")
    problems_url = "https://codeforces.com/api/problemset.problems"
    response = requests.get(problems_url)
    data = response.json()

    if data["status"] != "OK":
        return "Failed to fetch problems."

    problems = data["result"]["problems"]
    division_map = get_division_map()

    count = 0

    for p in problems:
        if "rating" not in p:
            continue  # skip unrated problems

        contest_id = p['contestId']
        index = p['index']
        name = p['name']
        rating = p['rating']
        url = f"https://codeforces.com/contest/{contest_id}/problem/{index}"
        division = division_map.get(contest_id)

        _, created = CodeforcesProblem.objects.get_or_create(
            contest_id=contest_id,
            index=index,
            defaults={
                'name': name,
                'rating': rating,
                'url': url,
                'division': division
            }
        )

        if created:
            count += 1

    return f"✅ {count} problems fetched and stored successfully."


def fetch_user_solved_problems(handle):
    url = f"https://codeforces.com/api/user.status?handle={handle}"
    response = requests.get(url)
    data = response.json()

    if data["status"] != "OK":
        return None

    solved_set = set()
    for submission in data["result"]:
        if submission["verdict"] == "OK":
            problem = submission["problem"]
            key = (problem["contestId"], problem["index"])
            solved_set.add(key)

    user, created = CodeforcesUser.objects.get_or_create(handle=handle)

    for contest_id, index in solved_set:
        try:
            prob = CodeforcesProblem.objects.get(contest_id=contest_id, index=index)
            user.solved_problems.add(prob)
        except CodeforcesProblem.DoesNotExist:
            continue  # skip if the problem isn't stored

    return user

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
        response = requests.get('https://codequest-ylrx.onrender.com/filter-problems/', params=params)
        if response.status_code == 200:
            problems = response.json()
    else:
        response = requests.get('https://codequest-ylrx.onrender.com/filter-problems/')
        if response.status_code == 200:
            problems = response.json()        

    divisions = ["Div. 1", "Div. 2", "Div. 3", "Div. 4", "Educational", "Global"]

    return render(request, 'filter_problems.html', {
        'problems': problems,
        'request': request,
        'divisions': divisions,
    })
