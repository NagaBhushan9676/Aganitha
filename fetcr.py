import argparse
import csv
import logging
import re
from typing import List, Dict
from Bio import Entrez

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

Entrez.email = "bhushanbesamrt9676@gmail.com"

NON_ACADEMIC_KEYWORDS = ["Pharma", "Biotech", "Inc", "Ltd", "Therapeutics", "Biosciences"]
ACADEMIC_KEYWORDS = ["University", "Institute", "Laboratory", "Research Center"]

def fetch_pubmed_papers(query: str) -> List[Dict[str, str]]:
    try:
        search_handle = Entrez.esearch(db="pubmed", term=query, retmax=10)
        search_results = Entrez.read(search_handle)
        search_handle.close()
        
        paper_ids = search_results.get("IdList", [])
        if not paper_ids:
            logging.warning("No papers found for query: %s", query)
            return []
        
        papers = []
        for paper_id in paper_ids:
            fetch_handle = Entrez.efetch(db="pubmed", id=paper_id, rettype="medline", retmode="text")
            paper_data = fetch_handle.read()
            fetch_handle.close()
            
            title = re.search(r"TI  - (.+)", paper_data)
            date = re.search(r"DP  - (\d{4})", paper_data)
            authors = re.findall(r"FAU - (.+)", paper_data)
            affiliations = re.findall(r"AD  - (.+)", paper_data)
            email_match = re.search(r"[\w\.-]+@[\w\.-]+", paper_data)
            
            title = title.group(1) if title else "Unknown"
            date = date.group(1) if date else "Unknown"
            email = email_match.group(0) if email_match else "N/A"
            
            company_authors, company_names = filter_non_academic_authors(authors, affiliations)
            
            papers.append({
                "PubmedID": paper_id,
                "Title": title,
                "Publication Date": date,
                "Non-academic Authors": ", ".join(company_authors),
                "Company Affiliations": ", ".join(company_names),
                "Corresponding Author Email": email
            })
        
        return papers
    except Exception as e:
        logging.error("Error fetching papers: %s", e)
        return []

def filter_non_academic_authors(authors: List[str], affiliations: List[str]) -> (List[str], List[str]):
    company_authors = []
    company_names = []
    
    for author, affiliation in zip(authors, affiliations):
        if any(keyword in affiliation for keyword in NON_ACADEMIC_KEYWORDS) and not any(keyword in affiliation for keyword in ACADEMIC_KEYWORDS):
            company_authors.append(author)
            company_names.append(affiliation)
    
    return company_authors, company_names

def save_to_csv(papers: List[Dict[str, str]], filename: str):
    with open(filename, "w", newline="") as csvfile:
        fieldnames = ["PubmedID", "Title", "Publication Date", "Non-academic Authors", "Company Affiliations", "Corresponding Author Email"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(papers)
    logging.info("Results saved to %s", filename)

def main():
    parser = argparse.ArgumentParser(description="Fetch PubMed research papers with non-academic authors.")
    parser.add_argument("query", help="PubMed search query")
    parser.add_argument("-f", "--file", help="Output CSV filename", default=None)
    parser.add_argument("-d", "--debug", help="Enable debug mode", action="store_true")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    papers = fetch_pubmed_papers(args.query)
    
    if args.file:
        save_to_csv(papers, args.file)
    else:
        for paper in papers:
            print(paper)

if __name__ == "__main__":
    main()
