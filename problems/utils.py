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
