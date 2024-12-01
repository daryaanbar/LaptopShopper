from bs4 import BeautifulSoup
import glob
from textblob import TextBlob
import spacy
import numpy as np
from typing import List, Dict
import re
import os


class LaptopInfoExtractor:

    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')  

        self.TAG_RULES = {
        'Gaming': {'gaming', 'rtx', 'fps', 'gamer', 'game', 'games', 'geforce'},
        'Business': {'business', 'professional', 'work', 'webcam'},
        'Student': {'student', 'college', 'school', 'homework', 'projects'},
        'Creative': {'editing', 'content', 'photo', 'stylus', 'art', 'video'},
        'Portable': {'portable', 'lightweight', 'thin', 'compact', 'slim'},
        'Security': {'secure', 'privacy', 'fingerprint'},
        'Affordable': {'affordable', 'budget', 'cheap', 'deal'},
    }


    # function to extract keywords from product description and specifications
    def extract_keywords(self, description: str, specs: dict) -> List[str]:
        
        # description
        description_doc = self.nlp(description)
        description_keywords = {token.lemma_.lower() for token in description_doc if token.is_alpha and not token.is_stop}

        # specifications
        specs_text = ' '.join([f"{key} {value}" for key, value in specs.items()])  # flatten dict to string
        specs_doc = self.nlp(specs_text)
        specs_keywords = {token.lemma_.lower() for token in specs_doc if token.is_alpha and not token.is_stop}

        # combine keywords from both 
        combined_keywords = description_keywords.union(specs_keywords)
        return list(combined_keywords)


    # function to generate tags
    def generate_tags(self, price_str: str, specs: Dict, keywords: List[str]) -> List[str]:
        tags = set()
        keywords_set = set(keywords)

        # maps extracted keyword to a tag rule
        for tag, related_keywords in self.TAG_RULES.items():
            if keywords_set.intersection(related_keywords):
                tags.add(tag)

        # checks price for affordability
        price = float(re.sub(r'[^\d.]', '', price_str))
        if price < 700:
            tags.add('Affordable')
       
        # checks specs for performance
        high_perf_cpus = ['i7', 'i9', 'Ryzen 7', 'Ryzen 9', 'M1', 'M2']
        cpu = specs.get('Processor', '')
        ram = specs.get('RAM', 0)
        ram_value = int(re.search(r'\d+', ram).group())
        
        high_perf = False
        for model in high_perf_cpus:
            if model in cpu:
                if ram_value >= 16:
                    high_perf = True
        
        if high_perf:
            tags.add('High Performance')

        return list(tags)

    
    # function to extract information from an HTML file
    def extract_laptop_info(self, file_path: str) -> dict:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

            # extract product details (name, price, description)
            name = soup.find('h1').text.strip()
            price = soup.find('p', class_='price').text.strip()
            description = soup.select_one('.product-details > p:nth-of-type(2)').text.strip()
            
            # extract product specifications
            specs = {}
            specs_table = soup.find('table', class_='specs-table')
            if specs_table:
                for row in specs_table.find_all('tr'):
                    key = row.find('th').text.strip()
                    value = row.find('td').text.strip()
                    specs[key] = value

            # extract overall product rating and reviews
            overall_rating = soup.find('div', class_='rating-number').text.strip()
            review_elements = soup.find_all('div', class_='review')
            reviews = []
            for review in review_elements:
                review_title = review.find('span', class_='review-title').text.strip()
                review_text = review.find('p').text.strip()
                review_stars = review.find('div', class_='stars').text.strip()
                reviews.append({'title': review_title, 'text': review_text, 'stars': review_stars})

            # extract keywords from description / specs and generate tags
            keywords = self.extract_keywords(description, specs)
            tags = self.generate_tags(price, specs, keywords) 

            # extracted laptop data
            return {
                'name': name,
                'price': price,
                'description': description,
                'tags': tags,
                'specifications': specs,
                'overall_rating': overall_rating,
                'reviews': reviews,
            }



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

        # Tags section
        if laptop_data['tags']:
            summary.append("\nTags:")
            for tag in laptop_data['tags']:
                summary.append(f"- {tag}")

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
    extractor = LaptopInfoExtractor()
    summarizer = LaptopSummarizer()
    files = glob.glob("WebPages/*.html")

    os.makedirs('kb', exist_ok=True)

    for i, file_path in enumerate(files):
        laptop_data = extractor.extract_laptop_info(file_path)
        summary = summarizer.generate_summary(laptop_data)

        with open(f'kb/{i}.txt', 'w') as f:
            f.write(f'{summary}\n')


if __name__ == "__main__":
    main()

