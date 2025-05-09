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
    response = requests.get(url, timeout=10)  # timeout added

    try:
        data = response.json()
    except Exception:
        return None

    if data.get("status") != "OK":
        return None

    solved_set = set()
    for submission in data["result"]:
        if submission.get("verdict") == "OK":
            prob = submission.get("problem", {})
            cid, idx = prob.get("contestId"), prob.get("index")
            if cid and idx:
                solved_set.add((cid, idx))

    user, _ = CodeforcesUser.objects.get_or_create(handle=handle)

    # Optimize DB queries
    all_probs = CodeforcesProblem.objects.filter(
        contest_id__in=[cid for cid, _ in solved_set],
        index__in=[idx for _, idx in solved_set]
    )
    problem_map = {(p.contest_id, p.index): p for p in all_probs}

    user.solved_problems.set([
        problem_map[key] for key in solved_set if key in problem_map
    ])

    return user



from django.core.paginator import Paginator

def filter_codeforces_problems(min_rating=None, max_rating=None, index=None, handle=None, division=None, sort_by=None, page=1):
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
                return queryset, set()  # ✅ Fix: safe fallback
        solved_ids = set(user.solved_problems.values_list('id', flat=True))

    # Apply sorting if required
    if sort_by:
        if sort_by == 'rating':
            queryset = queryset.order_by('rating')
        elif sort_by == 'index':
            queryset = queryset.order_by('index')

    # Paginate the queryset
    paginator = Paginator(queryset, 20)  # 20 problems per page
    page_obj = paginator.get_page(page)

    return page_obj, solved_ids


