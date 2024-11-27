from typing import List, Dict

import pandas as pd  # Bibliothek zur Datenanalyse (z. B. für das Arbeiten mit DataFrames)
import streamlit as st  # Streamlit für die Erstellung von Webanwendungen.
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

# Import von benutzerdefinierten Funktionen
from backend.dbpedia_handler import *  # Funktionen für DBpedia-Abfragen (z. B. Symptome/Krankheiten)
from backend.medline_handler import get_article  # Funktion zum Abrufen eines Medline-Artikels.
from backend.Entropy import *  # Funktionen zur Berechnung der Entropie von Symptomen
from backend.wikipedia_handler import get_symptom_text

# Zugriff auf den Session-Status, um Daten während der Interaktion zu speichern.
s_state = st.session_state

# Setzt den Titel der Streamlit-Anwendung.
st.title("Healthcare")

col1, col2 = st.columns(2)

if col1.button("New Query"):
    for key in st.session_state.keys():
        del st.session_state[key]
    s_state.status = "User Input"
    st.rerun()

col2.checkbox("LLM Active", key="llm_active")

# Initialisierung des Status, falls dieser noch nicht existiert.
if "status" not in s_state:
    s_state.status = "User Input"  # Startzustand: Benutzer gibt Symptome ein.

# Zustand "User Input" (Symptomeingabe durch den Nutzer).
if s_state.status == "User Input":
    # Initialisierung der Liste für Symptome, falls diese noch nicht existiert.
    if "symptom_list" not in s_state:
        s_state.symptom_list = []

    # Initialisierung des Wörterbuchs mit Symptomen, falls noch nicht vorhanden.
    if "symptom_dict" not in s_state:
        s_state.symptom_dict = get_all_symptoms()

    # Abrufen aller möglichen Symptome, die noch nicht hinzugefügt wurden.
    s_state.symptom_dict_pos = get_all_possible_symptoms(
        [s_state.symptom_dict[symptom] for symptom in s_state.symptom_list])

    # Trennlinie in der Benutzeroberfläche
    st.divider()
    st.subheader("Symptom Input")  # Unterüberschrift für die Symptomeingabe.

    # Anzeige der Symptome mit Möglichkeit, sie zu löschen.
    for i, symptom in enumerate(s_state.symptom_list):
        with st.container(border=True):  # Umrahmt jedes Symptom.
            col1, col2 = st.columns(2)  # Zwei Spalten für das Symptom und den Löschbutton.
            col1.write(symptom)  # Zeigt das Symptom an.
            if col2.button("Delete Symptom", key=i):  # Löscht das Symptom aus der Liste.
                del s_state.symptom_list[i]
                st.rerun()  # Aktualisiert die App, um die Änderung anzuzeigen.

    # Dropdown-Menü zur Auswahl eines neuen Symptoms aus der verfügbaren Liste.
    selected_symptom = st.selectbox(
        "Symptom",
        sorted(set(s_state.symptom_dict_pos.keys()).difference(set(s_state.symptom_list)))
    )

    # Hinzufügen des ausgewählten Symptoms zur Liste.
    if st.button("Add Symptom"):
        s_state.symptom_list.append(selected_symptom)
        st.rerun()

    # Wenn Symptome vorhanden sind, abrufen möglicher Krankheiten basierend auf den Symptomen.
    if len(s_state.symptom_list) > 0:
        s_state.possible_diseases = get_diseases_by_symptoms(
            [s_state.symptom_dict[x] for x in s_state.symptom_list]
        )
        print(f"Diseases found: {len(s_state.possible_diseases)}")
        if st.button("Finish Input"):  # Wechselt zum nächsten Schritt nach der Symptomeingabe.
            s_state.status = "Symptom Questions"  # Übergang zum Zustand der Symptomfragen.
            st.rerun()

# Zustand "Symptom Questions" (Weitere Fragen zu den Symptomen).
if s_state.status == "Symptom Questions":
    st.divider()
    st.subheader("Symptom Questions")

    # Initialisierung der Variablen für den Krankheits- und Frageindex.
    if "no_symptom_list" not in s_state:
        s_state.no_symptom_list = []

    # Anzeige der bekannten und ausgeschlossenen Symptome.
    st.write(f"Already known symptoms: {', '.join(s_state.symptom_list)}")
    st.write(f"Already excluded symptoms: {', '.join(s_state.no_symptom_list)}")

    # Berechnung der Entropie für alle Symptome der gefundenen Krankheiten.
    disease_list = get_diseases_for_symptoms([s_state.symptom_dict[x] for x in s_state.symptom_list])
    disease_symptom_pairs = get_disease_symptom_pairs(disease_list)
    entropy_values = calculate_entropy_for_all_symptoms(disease_symptom_pairs)

    # Entfernt Symptome, die bereits in den Listen vorhanden sind.
    filtered_entropy_values = {
        key: value
        for key, value in entropy_values.items()
        if key not in [s_state.symptom_dict[symptom] for symptom in s_state.no_symptom_list]
    }

    # Sortiert die verbleibenden Einträge nach Entropiewerten in absteigender Reihenfolge.
    sorted_filtered_entropy_values = sorted(filtered_entropy_values.items(), key=lambda x: x[1], reverse=True)

    print(sorted_filtered_entropy_values)

    # Entfernen und Überprüfen der Symptome für die Krankheiten.
    count_distinct_diseases = remove_and_check_symptoms(disease_symptom_pairs,
                                                        [s_state.symptom_dict[symptom] for symptom in
                                                         s_state.no_symptom_list])

    # Überprüfung, ob es noch Symptome gibt, die abgefragt werden müssen.
    if count_distinct_diseases > 1:
        symptom_with_highest_entropy = sorted_filtered_entropy_values[0]
        symptom = next(key for key, value in s_state.symptom_dict.items() if value == symptom_with_highest_entropy[0])

        with st.container(border=True):
            st.write(f"Do you have: {symptom}?")  # Fragt den Nutzer nach dem Symptom.

            # Wenn "Ja", fügt das Symptom der Liste hinzu.
            if st.button("Yes"):
                s_state.symptom_list.append(symptom)
                st.rerun()

            # Wenn "Nein", schließt das Symptom aus.
            if st.button("No"):
                s_state.no_symptom_list.append(symptom)
                st.rerun()
    else:  # Wenn keine weiteren Fragen übrig sind, wechselt zum Plausibilitäts-Check.
        s_state.possible_diseases = get_diseases_by_symptoms(
            [s_state.symptom_dict[x] for x in s_state.symptom_list]
        )
        print("Starting Plausibility Check for diseases:", s_state.possible_diseases)
        s_state.status = "Plausibility Check"
        st.rerun()

# Zustand "Plausibility Check" (Abschlussprüfung der Ergebnisse).
if s_state.status == "Plausibility Check":
    st.divider()
    st.subheader("Plausibility Check")

    if "disease_decision" not in s_state:
        s_state.disease_list = get_diseases_for_symptoms([s_state.symptom_dict[x] for x in s_state.symptom_list])
        print('Checking for ', s_state.disease_list)
        s_state.disease_decision = dict()

    if "current_index" not in s_state:
        s_state.current_index = 0

    # Abrufen der möglichen Krankheiten basierend auf den eingegebenen Symptomen.

    # Abrufen des Wikipedia Signs and Symptoms Kapitels.
    current_disease = list(s_state.possible_diseases.values())[s_state.current_index]

    if "disease_name" not in s_state or "symptom_text" not in s_state or "wiki_page_id" not in s_state:
        s_state.wiki_page_id = get_wikiPageID_of_disease(current_disease)
        print(f"wikiPageID: {s_state['wiki_page_id']}")
        s_state.disease_name, s_state.symptom_text = get_symptom_text(s_state["wiki_page_id"])

    if s_state.get("llm_active", False):
        def format_chat_history(history: List[Dict]) -> str:
            if not history:
                return "No previous questions."
            return "\n".join([f"Q: {h['question']}\nA: {h['answer']}" for h in history])


        if "llm" not in s_state:
            s_state.llm = OllamaLLM(model="llama3.2:3b")

        if "chat_history" not in s_state:
            s_state.chat_history = []

        if "awaiting_answer" not in s_state:
            s_state.awaiting_answer = False

        if "question" not in s_state:
            s_state.question = ""

        # Modern prompt template using ChatPromptTemplate
        question_template = """Generate a single, clear yes/no question to further assess whether the patient has a specific 
        condition. Focus on creating the most relevant question based on the provided symptom description and chat 
        history. If you are finished with your assessment output "END".

            Disease Name: {disease_name}
            Already known Symptoms: {known_symptoms}
            Already excluded Symptoms: {excluded_symptoms}
            Symptom Description: {symptom_text}  
            Chat History (Previous Questions and Answers): {chat_history}  

            If you provide a question, your question should:  
            1. Be directly related to the symptom description.  
            2. Build logically on the chat history.  
            3. Avoid open-ended or explanatory statements.  

            Output:  

            """

        question_prompt_template = PromptTemplate(
            input_variables=["disease_name", "known_symptoms", "excluded_symptoms", "symptom_text", "chat_history"],
            template=question_template
        )

        with st.expander("Chat History"):
            st.write(s_state.chat_history)

        if len(s_state.chat_history) < 3:  # Added maximum questions limit
            try:
                if not s_state.awaiting_answer:
                    print("Invoke LLM")
                    s_state.question = s_state["llm"].stream(question_prompt_template.format(
                        disease_name=s_state["disease_name"],
                        known_symptoms=", ".join(s_state.symptom_list),
                        excluded_symptoms=", ".join(s_state.no_symptom_list),
                        symptom_text=s_state["symptom_text"],
                        chat_history=format_chat_history(s_state["chat_history"])
                    ))

                    s_state.awaiting_answer = True

                with st.container(border=True):
                    st.write_stream(s_state["question"])
                    col1, col2, col3 = st.columns(3)
                    if col1.button("Yes"):
                        s_state["chat_history"].append({
                            "question": s_state["question"],
                            "answer": "yes"
                        })
                        s_state.awaiting_answer = False
                        st.rerun()
                    if col2.button("No"):
                        s_state["chat_history"].append({
                            "question": s_state["question"],
                            "answer": "no"
                        })
                        s_state.awaiting_answer = False
                        st.rerun()
                    if col3.button("I don't know"):
                        s_state["chat_history"].append({
                            "question": s_state["question"],
                            "answer": "I don't know"
                        })
                        s_state.awaiting_answer = False
                        st.rerun()



            except IndexError as e:
                print(f"\nError during diagnosis: {str(e)}")

        else:
            # Modern prompt template using ChatPromptTemplate
            assessment_template = """Based on the name of the disease, the symptom description and the chat history, please give an assessment, if the diagnosis is plausible and how critical the disease state is.
    
                Disease Name: {disease_name}
                Already known Symptoms: {known_symptoms}
                Already excluded Symptoms: {excluded_symptoms}
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
                input_variables=["disease_name", "known_symptoms", "excluded_symptoms", "symptom_text", "chat_history"],
                template=assessment_template
            )

            st.write_stream(s_state["llm"].stream(assessment_prompt_template.format(
                disease_name=s_state["disease_name"],
                known_symptoms=", ".join(s_state.symptom_list),
                excluded_symptoms=", ".join(s_state.no_symptom_list),
                symptom_text=s_state["symptom_text"],
                chat_history=format_chat_history(s_state["chat_history"])
            )))
    else:
        with st.container(border=True):
            st.write("Does the following list of symptoms match your condition?")
            if st.button("Yes"):
                s_state.disease_decision[list(s_state.possible_diseases.keys())[s_state.current_index]] = True
                if s_state.current_index == len(s_state.disease_list) - 1:
                    s_state.status = "Display Results"
                else:
                    s_state.current_index += 1
                st.rerun()
            if st.button("No"):
                s_state.disease_decision[list(s_state.possible_diseases.keys())[s_state.current_index]] = False
                if s_state.current_index == len(s_state.disease_list) - 1:
                    s_state.status = "Display Results"
                else:
                    s_state.current_index += 1
                st.rerun()

        if "An error occurred" not in s_state["symptom_text"]:  # Wenn eine Medline-ID gefunden wurde, Artikel und Symptome anzeigen.
            st.write(f"Possible Disease: {list(s_state.possible_diseases.keys())[s_state.current_index]}")
            st.markdown(s_state["symptom_text"])  # Anzeige der Symptome im Artikel.
        else:
            # Wenn keine Medline-ID gefunden wird, wird die Krankheit ohne Medline-ID angezeigt.
            st.write(f"Possible Disease: {list(s_state.possible_diseases.keys())[s_state.current_index]}")
            st.write("Unfortunately no symptoms were found in Wikipedia")

if s_state.status == "Display Results":
    st.divider()
    st.subheader("Results")

    # Anzeige der ausgewählten Symptome.
    st.write(f"Selected Symptoms: {', '.join(s_state.symptom_list)}")

    # Anzeige der möglichen Krankheiten.
    st.write("Disease Symptom Answers:")
    st.write(s_state.disease_decision)
