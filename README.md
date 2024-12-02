# LaptopShopper
This project was made by Andrew Sen, Darya Anbar, and Ethan Ferneyhough CS 6320.


## Project Scope
We built a **Discord** bot to improve the online laptop shopping experience for users by:
- Asking questions about their needs and preferences
- Scraping laptop data from multiple online sources (AI-generated for this project)
- Summarizing product details
- Leveraging an LLM and Retrieval-Argument Generation (RAG) to generate a response


## Team Member Contributions 
1. Ethan: 
    - Using textblob, I was able to do sentiment analysis on user reviews and categorize them into positive and negative sentiments. I also developed a laptop summarizer for data for the chatbot to use. 
        - (see LaptopSummarizer in web_scraper.py)
2. Andrew: 
    - I created the main chatbot that users interact with. The chatbot is built on the Llama 3.2 LLM, and I feed the bot information of relevant laptop summaries so it can generate optimal recommendations for user queries. 
        - (see discord_bot.py)
3. Darya: 
    - I implemented the information extraction functionality to “scrape” mock product pages for laptop information. Using SpaCy, I extracted keywords and generated tags based on product descriptions and specifications. 
        - (see LaptopInfoExtractor in web_scraper.py)


# Resources
- https://stackoverflow.com/questions/73141460/web-scrapping-using-python-for-nlp-project
- https://www.datacamp.com/tutorial/web-scraping-python-nlp
- https://huggingface.co/models
- https://www.projectpro.io/article/python-libraries-for-web-scraping/625
