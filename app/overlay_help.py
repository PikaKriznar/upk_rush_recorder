import streamlit as st
import pandas as pd

# KAJ V POROČILO?
# V prototipu je dodan razlagalni sloj (overlay), ki ne-tehničnim uporabnikom pojasni delovanje sistema,
# prikazane metrike in trenutno stanje. Sistem uporabniku jasno in neposredno sporoči, 
# ali trenutno hiti ali ne, na podlagi personaliziranih nastavitev.

def show_intro_overlay():
    """
    Kratek uvodni opis aplikacije – za uporabnike brez ML znanja.
    """
    with st.expander("ℹ️ Kaj ta aplikacija počne?", expanded=True):
        st.markdown(
            """
            **Ta aplikacija prikazuje, kako sistem zaznava, ali uporabnik hiti ali ne.**

            Sistem uporablja podatke o gibanju (akcelerometer iz telefona) in
            naučen model, ki prepozna vzorce:
            - **normalna hoja**
            - **hitenje (hitrejša hoja / tek)**

            Model NE meri stresa ali namena – meri **vzorce gibanja**.
            """
        )


def explain_metrics():
    """
    Razlaga osnovnih pojmov na strani.
    """
    with st.expander("📊 Kaj pomenijo prikazane vrednosti?"):
        st.markdown(
            """
            **p(rush)**  
            Verjetnost (0–1), da je uporabnik v stanju hitenja v določenem časovnem oknu.
            Višja vrednost pomeni bolj intenzivno gibanje.

            **Rush Index**  
            Odstotek časa, ko je sistem zaznal hitenje.
            Primer: *30 %* pomeni, da je uporabnik tretjino časa hodil zelo hitro ali tekel.

            **Globalni prag**  
            Enak prag za vse uporabnike (npr. 0.5).

            **Personaliziran prag**  
            Prag, prilagojen posamezniku na podlagi njegovega običajnega načina hoje.
            """
        )


def show_status_banner(is_rushing: bool, personalized: bool = True):
    """
    Velik, jasen status za uporabnika.
    """
    if is_rushing:
        st.error(
            "🚨 **UPORABNIK TRENUTNO HITI**\n\n"
            "Sistem zaznava hitro gibanje glede na izbrane nastavitve."
        )
    else:
        st.success(
            "✅ **UPORABNIK SE GIBA UMIRJENO**\n\n"
            "Trenutno ni zaznanega hitenja."
        )

    if personalized:
        st.caption("Status temelji na **personaliziranem pragu**.")
    else:
        st.caption("Status temelji na **globalnem pragu**.")

def explain_decision_q():
    """
    Razlaga končne odločitve sistema (q).
    """
    with st.expander("🧠 Kako sistem sprejme odločitev (q)?"):
        st.markdown(
            """
            **q (končna odločitev sistema)**  
            Spremenljivka *q* predstavlja **končno presojo sistema**, ali uporabnik
            trenutno **hiti (q = 1)** ali **ne hiti (q = 0)**.

            Odločitev q ni neposredno izmerjena vrednost, ampak rezultat primerjave:
            - verjetnosti **p(rush)**, ki jo napove model,
            - in izbranega **praga hitenja**.

            **Primer:**
            - p(rush) = 0.72  
            - prag = 0.60  
            → q = 1 (sistem oceni, da uporabnik hiti)

            Če je p(rush) **nižja od praga**, sistem vrne:
            → q = 0 (uporabnik se giba umirjeno)

            Tako sistem pretvori neprekinjeno oceno gibanja v
            **jasno in razumljivo sporočilo za uporabnika**.
            """
        )
