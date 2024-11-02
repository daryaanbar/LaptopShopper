from bs4 import BeautifulSoup
import glob

# function to parse each HTML file
def parse_laptop_file(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        
        # extract product details
        name = soup.find('h1').text.strip()
        price = soup.find('p', class_='price').text.strip()
        description = soup.select_one('.product-details > p:nth-of-type(2)').text.strip()
        
        # extract specifications
        specs = {}
        specs_table = soup.find('table', class_='specs-table')
        if specs_table:
            for row in specs_table.find_all('tr'):
                key = row.find('th').text.strip()
                value = row.find('td').text.strip()
                specs[key] = value
        
        # extract overall rating and reviews
        overall_rating = soup.find('div', class_='rating-number').text.strip()
        review_elements = soup.find_all('div', class_='review')
        reviews = []
        for review in review_elements:
            review_title = review.find('span', class_='review-title').text.strip()
            review_text = review.find('p').text.strip()
            review_stars = review.find('div', class_='stars').text.strip()
            reviews.append({'title': review_title, 'text': review_text, 'stars': review_stars})
        
        return {
            'name': name,
            'price': price,
            'description': description,
            'specifications': specs,
            'overall_rating': overall_rating,
            'reviews': reviews
        }
    
# function to summarize the data
def summarize_data(data):
    summary = []
    for laptop in data:
        
        # format specifications and reviews
        specs = "\n".join(f"{key}: {value}" for key, value in laptop['specifications'].items())
        reviews = "\n\n".join(
            f"Review Title: {review['title']}\n"
            f"Review Text: {review['text']}\n"
            f"Rating: {review['stars']} stars"
            for review in laptop['reviews']
        )
        
        # build summary
        laptop_summary = (
            f"Model: {laptop['name']}\n"
            f"Price: {laptop['price']}\n"
            f"Description: {laptop['description']}\n"
            f"\nSpecifications:\n{specs}\n"
            f"\nOverall Rating: {laptop['overall_rating']} stars\n"
            f"Top Review: {laptop['reviews'][0]['title']} - {laptop['reviews'][0]['text']}\n"
            f"\nReviews:\n{reviews}\n"
            "\n-----------------------------\n"
        )
        summary.append(laptop_summary)
    
    return "\n".join(summary)


def main():
    files = glob.glob("WebPages/*.html")  # path to html files
    laptop_data = []
    
    for file_path in files:
        laptop_data.append(parse_laptop_file(file_path))
    
    summary = summarize_data(laptop_data)
    print("Laptops Summary:\n", summary)


if __name__ == "__main__":
    main()

