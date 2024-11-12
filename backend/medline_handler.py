import requests
from lxml import html

def get_article(medline_id):
    # Define the URL and the XPath
    url = f"https://medlineplus.gov/ency/article/{medline_id}.htm"
    xpath_full_text = '//*[@id="d-article"]/div[2]'
    xpath_symptoms = '//section[.//h2[text()="Symptoms"]]'

    # Send a request to fetch the page content
    response = requests.get(url)
    if response.status_code == 200:
        # Parse the content
        tree = html.fromstring(response.content)

        # Find any section where the header text is "Symptoms"
        symptoms_sections = tree.xpath(xpath_symptoms)

        if symptoms_sections:
            # Get the text of the first matching "Symptoms" section
            symptoms_text = symptoms_sections[0].xpath('.//text()')
            symptoms_text = " ".join(symptoms_text).strip()
        else:
            symptoms_text = None

        # Extract the article text using XPath
        article_text = tree.xpath(xpath_full_text + '//text()')

        # Join the text elements into a single string
        article_text = " ".join(article_text)

        return article_text, symptoms_text

    else:
        print(f"Failed to retrieve page, status code: {response.status_code}")
        return None, None
