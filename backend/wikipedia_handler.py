from typing import List, Dict

import wikipediaapi
import wikipedia
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


def get_text(section, section_level=1):
    full_text = f"{'#' * (section_level + 1)} {section.title}:\n"
    full_text += f"{section.text}\n\n"
    if len(section.sections) > 0:
        for subsection in section.sections:
            full_text += get_text(subsection, section_level + 1)
    return full_text


def get_symptom_text(wikiPageId):
    try:
        temp = wikipedia.page(pageid=int(wikiPageId))
        print(temp.title)
        wiki_wiki = wikipediaapi.Wikipedia('Chrome', 'en')
        page = wiki_wiki.page(temp.title)
        for section_title in ["Signs and symptoms", "Symptoms"]:
            section = page.section_by_title(section_title)
            if section:
                break
        return temp.title, get_text(section)
    except Exception as e:
        print(f"An error occurred: {e}")
        return "ERROR", f"An error occurred: {e}"


def plausibility_check(wiki_page_id: int):
    def format_chat_history(history: List[Dict]) -> str:
        if not history:
            return "No previous questions."
        return "\n".join([f"Q: {h['question']}\nA: {h['answer']}" for h in history])

    disease_name, symptom_text = get_symptom_text(wiki_page_id)

    # Initialize the LLM with modern configuration
    llm = OllamaLLM(model="gemma2:27b")

    # Modern prompt template using ChatPromptTemplate
    question_template = """Generate a single, clear yes/no question to further assess whether the patient has a specific 
    condition. Focus on creating the most relevant question based on the provided symptom description and chat 
    history. If you are finished with your assessment output "END".

        Disease Name: {disease_name}
        Symptom Description: {symptom_text}  
        Chat History (Previous Questions and Answers): {chat_history}  
        
        If you provide a question, your question should:  
        1. Be directly related to the symptom description.  
        2. Build logically on the chat history.  
        3. Avoid open-ended or explanatory statements.  
        
        Output:  

        """

    question_prompt_template = PromptTemplate(
        input_variables=["disease_name", "symptom_text", "chat_history"],
        template=question_template
    )

    diagnosis_determined = False
    chat_history = []

    while not diagnosis_determined and len(chat_history) < 8:  # Added maximum questions limit
        try:
            # Invoke chain with modern syntax
            question = llm.invoke(question_prompt_template.format(
                disease_name=disease_name,
                symptom_text=symptom_text,
                chat_history=format_chat_history(chat_history)
            ))
            if question == "END":
                break

            print(question)
            user_response = input("Answer (yes/no): ").strip().lower()

            chat_history.append({
                "question": question,
                "answer": user_response
            })

        except IndexError as e:
            print(f"\nError during diagnosis: {str(e)}")
            break

    # Modern prompt template using ChatPromptTemplate
    assessment_template = """Based on the name of the disease, the symptom description and the chat history, please give an assessment, if the diagnosis is plausible and how critical the disease state is.

        Symptom Description: {symptom_text}  
        Chat History (Previous Questions and Answers): {chat_history}  

        Possible Disease States:
        1. Critical, Call an Ambulanz
        2. Critical, Visit the local hospital
        3. Non-Critical, Visit a doctor
        4. Non-Critical, Monitor the symptoms
        
        Output:  

        """

    assessment_prompt_template = PromptTemplate(
        input_variables=["symptom_text", "chat_history"],
        template=assessment_template
    )

    return llm.invoke(assessment_prompt_template.format(
                disease_name=disease_name,
                symptom_text=symptom_text,
                chat_history=format_chat_history(chat_history)
            ))


if __name__ == "__main__":
    print(plausibility_check(19572217))
