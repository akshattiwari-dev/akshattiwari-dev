"""Updates the live GitHub numbers inside dark_mode.svg and light_mode.svg."""
import os
import re
from datetime import datetime

import requests

USER = "akshattiwari-dev"
TOKEN = os.environ["ACCESS_TOKEN"]
HEADERS = {"Authorization": f"bearer {TOKEN}"}


def gql(query, **variables):
    r = requests.post("https://api.github.com/graphql",
                      json={"query": query, "variables": variables}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def get_stats():
    user = gql("""query($u:String!){ user(login:$u){
        createdAt followers{totalCount}
        repositories(first:100, ownerAffiliations:OWNER){ totalCount nodes{stargazerCount} } } }""",
               u=USER)["user"]

    # Commits are only queryable one year at a time, so loop from account creation.
    commits = 0
    for year in range(int(user["createdAt"][:4]), datetime.now().year + 1):
        c = gql("""query($u:String!,$from:DateTime!,$to:DateTime!){ user(login:$u){
            contributionsCollection(from:$from,to:$to){
                totalCommitContributions restrictedContributionsCount } } }""",
                u=USER, **{"from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"}
                )["user"]["contributionsCollection"]
        commits += c["totalCommitContributions"] + c["restrictedContributionsCount"]

    return {
        "repo_data": user["repositories"]["totalCount"],
        "star_data": sum(n["stargazerCount"] for n in user["repositories"]["nodes"]),
        "commit_data": commits,
        "follower_data": user["followers"]["totalCount"],
    }


def update_svg(path, stats):
    svg = open(path, encoding="utf-8").read()
    for key, value in stats.items():
        svg = re.sub(rf'(id="{key}"[^>]*>)[^<]*(</tspan>)', rf"\g<1>{value:,}\g<2>", svg)
    open(path, "w", encoding="utf-8").write(svg)


if __name__ == "__main__":
    stats = get_stats()
    print(stats)
    for f in ("dark_mode.svg", "light_mode.svg"):
        update_svg(f, stats)
