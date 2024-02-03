import requests
from consensus import query_consensus

def summarize_supplement(supplement):
    aspects = ["benefits", "side effects", "dosage"]
    summary = {"supplement": supplement, "data": {}}

    for aspect in aspects:
        query = f"What are the {aspect} of {supplement}?"
        result = query_consensus(query)

        if result and result.get("papers"):
            summary["data"][aspect] = [{"title": paper["title"],
                                        "summary": paper["display_text"],
                                        "year": paper["year"],
                                        "journal": paper["journal"]} for paper in result["papers"]]
        else:
            summary["data"][aspect] = "No data found"

    return summary

# Example usage
supplements = ["vitamin C", "vitamin D", "magnesium"]
summaries = [summarize_supplement(supplement) for supplement in supplements]

for summary in summaries:
    print(f"Supplement: {summary['supplement']}\n")
    for aspect, papers in summary['data'].items():
        print(f"{aspect.capitalize()}:")
        if isinstance(papers, list):
            for paper in papers:
                print(f"- Title: {paper['title']}")
                print(f"  Summary: {paper['summary']}")
                print(f"  Journal: {paper['journal']} ({paper['year']})\n")
        else:
            print(papers)
        print("\n")
