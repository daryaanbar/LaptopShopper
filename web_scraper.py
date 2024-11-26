from bs4 import BeautifulSoup
import glob
from textblob import TextBlob
import spacy
from collections import defaultdict
import numpy as np
from typing import List, Dict
import re
import os

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
'''
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
'''
class LaptopSummarizer:
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')

    def get_key_specs(self, specs: Dict) -> Dict:
        #extracting key specifications
        key_specs ={
            'Performance': [],
            'Display': [],
            'Storage': [],
            'Other': []
        }
        for key, value in specs.items():
            if any(term in key.lower() for term in ['processor', 'cpu', 'graphics', 'gpu']):
                key_specs['Performance'].append(f"{key}: {value}")
            elif any(term in key.lower() for term in ['display', 'screen']):
                key_specs['Display'].append(f"{key}: {value}")
            elif any(term in key.lower() for term in ['storage', 'ram', 'memory']):
                key_specs['Storage'].append(f"{key}: {value}")
            else:
                key_specs['Other'].append(f"{key}: {value}")
        return key_specs

    def analyze_reviews(self, reviews: List[Dict]) -> Dict:
        #Analyzing reviews with key points using TextBlob
        sentiments = []
        key_points = {
            'positive': [],
            'negative': []
        }

        for review in reviews:
            blob = TextBlob(review['text'])
            sentiments.append(blob.sentiment.polarity)

            # Process each sentence
            doc = self.nlp(review['text'])
            for sent in doc.sents:
                sent_blob = TextBlob(str(sent))
                if sent_blob.sentiment.polarity > 0.3:
                    key_points['positive'].append(str(sent))
                elif sent_blob.sentiment.polarity < -0.3:
                    key_points['negative'].append(str(sent))

        return {
            'average_sentiment': np.mean(sentiments),
            'key_points': key_points
        }


    def generate_summary(self, laptop_data: Dict) -> str:
        #Generate summary
        # Extract price as float
        price = float(re.sub(r'[^\d.]', '', laptop_data['price']))

        # Analyze specifications
        key_specs = self.get_key_specs(laptop_data['specifications'])

        # Analyze reviews
        review_analysis = self.analyze_reviews(laptop_data['reviews'])

        # Build summary
        summary = []

        # Overview section
        summary.append(f"--- {laptop_data['name']} Summary ---\n")
        summary.append(f"Price: ${price:.2f}")
        summary.append(f"Rating: {laptop_data['overall_rating']}/5.0")
        summary.append(f"\nBrief Description:")
        summary.append(laptop_data['description'])

        # Key Specifications
        summary.append("\nKey Specifications:")
        for category, specs in key_specs.items():
            if specs:
                summary.append(f"\n{category}:")
                for spec in specs:
                    summary.append(f"- {spec}")

        # Review Analysis
        summary.append("\nReview Analysis:")
        sentiment_text = ("Very Positive" if review_analysis['average_sentiment'] > 0.5 else
                         "Positive" if review_analysis['average_sentiment'] > 0 else
                         "Negative" if review_analysis['average_sentiment'] < -0.5 else
                         "Slightly Negative")
        summary.append(f"Overall Sentiment: {sentiment_text}")

        if review_analysis['key_points']['positive']:
            summary.append("\nKey Positive Points:")
            for point in review_analysis['key_points']['positive'][:2]:
                summary.append(f"✓ {point}")

        if review_analysis['key_points']['negative']:
            summary.append("\nKey Negative Points:")
            for point in review_analysis['key_points']['negative'][:2]:
                summary.append(f"✗ {point}")

        # Value Assessment
        value_score = float(laptop_data['overall_rating']) / (price / 1000)
        value_assessment = ("Excellent" if value_score > 4 else
                          "Good" if value_score > 3 else
                          "Fair" if value_score > 2 else
                          "Poor")

        summary.append(f"\nValue Assessment: {value_assessment} value for money")

        return "\n".join(summary)

def main():
    summarizer = LaptopSummarizer()
    files = glob.glob("WebPages/*.html")

    os.makedirs('kb', exist_ok=True)

    for i, file_path in enumerate(files):
        laptop_data = parse_laptop_file(file_path)
        summary = summarizer.generate_summary(laptop_data)

        with open(f'kb/{i}.txt', 'w') as f:
            f.write(f'{summary}\n')



if __name__ == "__main__":
    main()

