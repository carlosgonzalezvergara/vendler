import streamlit as st

def mostrar_info():
    # Detectamos el idioma desde el estado de la sesión (predeterminado a 'ES')
    lang = st.session_state.get('lang', 'ES')

    if lang == 'ES':
        st.header("Información y Créditos")
        
        st.subheader("Créditos")
        st.markdown("""
        **Autor:** Carlos González Vergara  
        **Afiliación:** Facultad de Letras, Pontificia Universidad Católica de Chile.  
        **Desarrollo:** Este software fue desarrollado en Python como una herramienta de apoyo para la investigación y docencia en el marco de la **Gramática de Papel y Referencia (RRG)**.
        """)

        st.subheader("Bibliografía de Referencia")
        st.markdown("""
        * Van Valin, Jr., R. D. (2023). Principles of Role and Reference Grammar. En D. Bentley, R. Mairal Usón, W. Nakamura y R. D. Van Valin, Jr. (Eds.), The Cambridge Handbook of Role and Reference Grammar (pp. 17–178). Cambridge University Press.
        * Van Valin, Jr., R. D. (2005). *Exploring the Syntax-Semantics Interface*. Cambridge University Press.
        * Van Valin, Jr., R. D., & LaPolla, R. J. (1997). *Syntax: Structure, meaning, and function*. Cambridge University Press.
        """)

        st.subheader("Contacto Institucional")
        st.info("Para consultas académicas o reporte de errores, contactar a: **cgonzalv@uc.cl**")

    else:
        st.header("Information and Credits")
        
        st.subheader("Credits")
        st.markdown("""
        **Author:** Carlos González Vergara  
        **Affiliation:** Facultad de Letras, Pontificia Universidad Católica de Chile.  
        **Development:** This software was developed in Python as a support tool for research and teaching within the **Role and Reference Grammar (RRG)** framework.
        """)

        st.subheader("Reference Bibliography")
        st.markdown("""
        * Van Valin, Jr., R. D. (2023). Principles of Role and Reference Grammar. In D. Bentley, R. Mairal Usón, W. Nakamura y R. D. Van Valin, Jr. (Eds.), The Cambridge Handbook of Role and Reference Grammar (pp. 17–178). Cambridge University Press.
        * Van Valin, Jr., R. D. (2005). *Exploring the Syntax-Semantics Interface*. Cambridge University Press.
        * Van Valin, Jr., R. D., & LaPolla, R. J. (1997). *Syntax: Structure, meaning, and function*. Cambridge University Press.
        """)

        st.subheader("Institutional Contact")
        st.info("For academic inquiries or bug reports, please contact: **cgonzalv@uc.cl**")

    st.divider()
    st.caption("Vendler Suite - 2026")