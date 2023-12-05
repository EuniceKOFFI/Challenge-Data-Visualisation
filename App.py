import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import math
import glob
import os
import seaborn as sns 
from matplotlib import pyplot as plt
import plotly.graph_objects as go
import matplotlib.image as mpimg
import random
from PIL import Image
import warnings
warnings.filterwarnings("ignore")
import requests
from io import StringIO
import plotly.express as px
import calendar
import json
import folium
    

# Configuration de la page 

st.set_page_config(
    page_title="Catnat",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    "<div style='display: flex; flex-wrap: wrap; margin-right: auto;'>"
    "<img src='https://www.science-accueil.org/wp-content/uploads/2020/06/LOGO-ENSAE-2.png' style='width: 110px; height: 100px;'>"
    "<h1 style='font-weight: bold; font-family: Calibri; margin-left: 10px;'>ENSAEML</h1>"
    "</div>",
    unsafe_allow_html=True
)


st.cache_data.clear()
############################################################ Les bases de données ##########################################################
@st.cache_data
def read_csv_from_url_with_encoding(url):
    try:
        content = requests.get(url).content.decode('utf-8')
        return pd.read_table(StringIO(content), sep='|')
    except UnicodeDecodeError:
        try:
            content = requests.get(url).content.decode('ISO-8859-1')
            return pd.read_table(StringIO(content), sep='|')
        except UnicodeDecodeError:
            content = requests.get(url).content.decode('CP1252')
            return pd.read_table(StringIO(content), sep='|')
        

# Application
BasePop = read_csv_from_url_with_encoding('https://raw.githubusercontent.com/EuniceKOFFI/Challenge-Data-Visualisation/main/BasePop.txt')
BaseCouts = read_csv_from_url_with_encoding('https://raw.githubusercontent.com/EuniceKOFFI/Challenge-Data-Visualisation/main/BaseCouts.txt')
BaseGaspar = read_csv_from_url_with_encoding('https://raw.githubusercontent.com/EuniceKOFFI/Challenge-Data-Visualisation/main/BaseGaspar.txt')


# Transformation des dates 
BaseGaspar['dat_deb'] = pd.to_datetime(BaseGaspar['dat_deb'], format='%Y-%m-%d %H:%M:%S')
BaseGaspar['dat_fin'] = pd.to_datetime(BaseGaspar['dat_fin'], format='%Y-%m-%d %H:%M:%S')

# Calcul de la durée 
BaseGaspar['duree'] = BaseGaspar['dat_fin'] - BaseGaspar['dat_deb'] + pd.Timedelta(days=1)
BaseGaspar['annee'] = BaseGaspar['dat_deb'].dt.year
BaseGaspar['mois'] = BaseGaspar['dat_deb'].dt.month

# Dimensions de la table
print("La base de données Gaspard contient", BaseGaspar.shape[0], "observations et", BaseGaspar.shape[1], "variables.")

# Affichage des 5 premières lignes 
BaseGaspar.head()

# Fonction de lecture des tables
def lecture_DVF(chemin_table):
    DVF = pd.read_table(chemin_table, sep="|", low_memory=False)
    DVF = DVF[(DVF["Type local"] == 'Appartement') | (DVF["Type local"] == 'Maison')]
    DVF = DVF[['No disposition', 'Date mutation', 'Nature mutation', 'Valeur fonciere', 'Commune', 'Code departement', 'Code commune']]
    return DVF

# Utilisation de la fonction lecture_DVF
DVF_2021 = lecture_DVF("https://www.data.gouv.fr/fr/datasets/r/817204ac-2202-4b4a-98e7-4184d154d98c")
DVF_2022 = lecture_DVF("https://www.data.gouv.fr/fr/datasets/r/87038926-fb31-4959-b2ae-7a24321c599a")
DVF_2023 = lecture_DVF("https://www.data.gouv.fr/fr/datasets/r/78348f03-a11c-4a6b-b8db-2acf4fee81b1")

# Concaténation des tables
DVF = pd.concat([DVF_2021, DVF_2022, DVF_2023])

# Fonction pour formater les valeurs de la colonne float
def format_float(val):
    formatted_val = f"{int(val):03d}"  # Utilisation de f-strings pour formater le nombre
    return formatted_val

# Application du formatage à la colonne float
DVF['Code commune'] = DVF['Code commune'].apply(format_float)

# Concaténation
DVF['Code_commune'] = DVF['Code departement'] + DVF['Code commune']

# Transformation des dates
DVF['Date mutation'] = pd.to_datetime(DVF['Date mutation'], format="%d/%m/%Y")
DVF['Annee mutation']= DVF['Date mutation'].dt.year
DVF['Mois mutation'] = DVF['Date mutation'].dt.month
DVF['Date_fin_mois'] = DVF['Date mutation'] + pd.offsets.MonthEnd(0)

# Valeur foncière
DVF['Valeur fonciere'] = DVF['Valeur fonciere'].str.replace(',', '.')
DVF['Valeur fonciere'] = pd.to_numeric(DVF['Valeur fonciere'])

############ Base MAP #############
BaseMap = pd.read_csv('https://raw.githubusercontent.com/EuniceKOFFI/Challenge-Data-Visualisation/main/communes-departement-region.csv', sep=',')
BaseMap = BaseMap[['code_commune_INSEE', 'latitude', 'longitude', 'nom_commune']]
BaseMap = BaseMap.dropna()

############################################################ Initialisation des pages ##########################################################
pages_name = ['Sinistralité', 'Zones à risques','Impact']
# Create a sidebar with a radio button to select the page
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page", pages_name)

##############################################################################################################################
############################################################ Page 1 ##########################################################
##############################################################################################################################

if page == 'Sinistralité':
    st.markdown(
    "<h1 style='text-align: center; color: black; padding: 10px; border-radius: 10px; background-color: #FFD3D3;'>Etude de la sinistralité</h1>",
    unsafe_allow_html=True
    )
############################################################ Graphique 1 ##########################################################
    left_column_side, right_column_side = st.columns(2)


    # Obtenir la liste des années uniques dans les données
    @st.cache_data
    def get_unique_years(data):
        years_list = data['annee'].unique()
        years_list.sort()  # Trier la liste des années
        return years_list

    # Fonction pour récupérer les données pour une année sélectionnée
    @st.cache_data
    def get_data_for_year(data, year):
        return data[data['annee'] == year]

    # Fonction pour générer le graphique
    @st.cache_data
    def generate_plot(data, year):
        count_by_month_risk = data.groupby(['mois', 'lib_risque_jo'])['cod_nat_catnat'].nunique().unstack().reset_index()

        # Convertir les chiffres des mois en noms de mois complets
        count_by_month_risk['mois'] = count_by_month_risk['mois'].apply(lambda x: calendar.month_name[x])

        # Création d'un dictionnaire pour spécifier l'ordre des mois
        month_order = {month: index for index, month in enumerate(calendar.month_name) if month}

        # Réorganiser les mois dans l'ordre souhaité sur l'axe x
        count_by_month_risk['mois'] = count_by_month_risk['mois'].map(month_order)

        fig = px.bar(count_by_month_risk, x='mois', y=count_by_month_risk.columns[1:], title=f'Nombre de cod_nat_catnat par mois pour l\'année {year}',
                     labels={'value': 'Nombre de cod_nat_catnat unique', 'mois': 'Mois'},
                     color_discrete_sequence=px.colors.qualitative.Safe)  # Utilisation de la palette de couleurs adaptées

        fig.update_layout(barmode='stack', xaxis={'tickmode': 'array', 'tickvals': list(month_order.values()), 'ticktext': list(month_order.keys())})

        return fig

    # Récupérer la liste des années uniques
    years_list = get_unique_years(BaseGaspar)

    with left_column_side:

        # Sélectionner une année
        #selected_year = st.number_input("Année", min_value=1982, max_value=2023, value=1982, step=1)
        selected_year = 1982

        # Récupérer les données pour l'année sélectionnée
        data_for_year = get_data_for_year(BaseGaspar, selected_year)

        fig = generate_plot(data_for_year, selected_year)

        st.plotly_chart(fig)


    ############################################################ Graphique 2 ##########################################################

    # Calculer les durées moyennes des sinistres par année et par type de catastrophe naturelle
    durees_moyennes_par_annee = BaseGaspar.groupby(['annee', 'lib_risque_jo'])['duree'].mean().reset_index()
    durees_moyennes_par_annee['duree'] = durees_moyennes_par_annee['duree'].dt.days


    # Tracer les courbes avec Plotly Express
    fig = px.line(durees_moyennes_par_annee, x='annee', y='duree', color='lib_risque_jo',
                  title='Durées moyennes en jours des sinistres par année et par type de catastrophe naturelle',
                  labels={'annee': 'Année', 'duree': 'Durée moyenne', 'lib_risque_jo': 'Type de catastrophe naturelle'})

    # Afficher le graphique Plotly dans Streamlit
    with right_column_side:
        st.plotly_chart(fig)



    ############################################################ Graphique 4 ##########################################################
    left_column_side_one, right_column_side_one = st.columns(2)

    # Sélection de l'année avec Streamlit slider
    #selected_year = st.slider(
        #"Sélectionner une année:",
        #min_value=min(years_list),
       # max_value=max(years_list),
        #value=2022  # Année par défaut : 2022
    #)

    # Filtrer les données pour l'année sélectionnée
    data_year = BaseGaspar[BaseGaspar['annee'] == 2022]
    count_communes_par_catnat = data_year.groupby('lib_risque_jo')['cod_commune'].nunique().reset_index()
    count_communes_par_catnat = count_communes_par_catnat.rename(columns={'cod_commune': 'Nombre de communes'})
    count_communes_par_catnat['Nombre de communes'] = count_communes_par_catnat['Nombre de communes'].round(decimals=1)

    # Utiliser une palette de couleurs adaptée aux daltoniens
    color_palette = px.colors.qualitative.Safe

    # Appliquer la palette de couleurs
    count_communes_par_catnat['color'] = count_communes_par_catnat['lib_risque_jo'].map(dict(zip(count_communes_par_catnat['lib_risque_jo'].unique(), color_palette)))

    with left_column_side_one:

        # Tracer le graphique circulaire (pie chart) avec Plotly Express
        fig = px.pie(count_communes_par_catnat, values='Nombre de communes', names='lib_risque_jo',
                     title=f'Nombre de communes touchées en 2022 par type de catégorie de catastrophe naturelle',
                     hole=0.4,
                     color='color')  # Utilisation de la colonne de couleurs adaptées

        # Mettre à jour les couleurs des tranches (slices) du pie chart
        fig.update_traces(marker=dict(colors=count_communes_par_catnat['color']))

        # Afficher le graphique Plotly dans Streamlit
        st.plotly_chart(fig)

    ############################################################ Graphique 4 ##########################################################

    with right_column_side_one:
        # Créer une fonction pour afficher le treemap en fonction de la période sélectionnée
        def update_treemap(start_year, end_year):
            filtered_data = BaseGaspar[BaseGaspar['annee'].between(start_year, end_year)]

            count_communes_par_cod_catnat = filtered_data.groupby('cod_nat_catnat')['cod_commune'].nunique().reset_index()
            count_communes_par_cod_catnat = count_communes_par_cod_catnat.rename(columns={'cod_commune': 'Nombre de communes'})

            top_10_communes = count_communes_par_cod_catnat.nlargest(10, 'Nombre de communes')

            fig = go.Figure(go.Treemap(
                labels=top_10_communes['cod_nat_catnat'],
                parents=[''] * len(top_10_communes),
                values=top_10_communes['Nombre de communes'],
                text=[f"Label: {BaseGaspar.loc[BaseGaspar['cod_nat_catnat'] == row['cod_nat_catnat'], 'lib_risque_jo'].iloc[0]}<br>"
                      f"Début: {BaseGaspar.loc[BaseGaspar['cod_nat_catnat'] == row['cod_nat_catnat'], 'dat_deb'].iloc[0]}<br>"
                      f"Durée: {BaseGaspar.loc[BaseGaspar['cod_nat_catnat'] == row['cod_nat_catnat'], 'duree'].iloc[0]} jours <br>"
                      f"Nombre de communes touchées: {row['Nombre de communes']} communes <br>"
                      for _, row in top_10_communes.iterrows()],
            ))

            fig.update_layout(
                title=f'Top 10 des cod_nat_catnat en fonction du nombre de communes touchées ({start_year}-{end_year})',
                treemapcolorway=px.colors.qualitative.Safe
            )

            st.plotly_chart(fig)

        # Créer un slider pour sélectionner la plage temporelle
        #start_year, end_year = st.slider("Sélectionner une période temporelle:", min_value=2013, max_value=2022, value=(2013, 2022))
        start_year = 2013
        end_year = 2022
        # Afficher le treemap en fonction de la plage temporelle sélectionnée
        update_treemap(start_year, end_year)

##############################################################################################################################
############################################################ Page 2 ##########################################################
##############################################################################################################################

elif page == 'Zones à risques':
    st.markdown(
    "<h1 style='text-align: center; color: black; padding: 10px; border-radius: 10px; background-color: #FFD3D3;'>Identifications des zones à risques</h1>",
    unsafe_allow_html=True
    )
    nombre_cat_nat_par_commune = pd.DataFrame(BaseGaspar.groupby('lib_commune')['cod_commune'].count().reset_index())
    nombre_cat_nat_par_commune = nombre_cat_nat_par_commune.rename(columns={'cod_commune': 'Nombre_cat_nat'})

    nombre_inondation_commune = pd.DataFrame(BaseGaspar[BaseGaspar['lib_risque_jo'] =='Inondations'].groupby('lib_commune')['cod_commune'].count().reset_index())
    nombre_inondation_commune = nombre_inondation_commune.rename(columns={'cod_commune': 'Nombre_inondations'})

    nombre_secheresse_commune = pd.DataFrame(BaseGaspar[BaseGaspar['lib_risque_jo'] =='Sécheresse'].groupby('lib_commune')['cod_commune'].count().reset_index())
    nombre_secheresse_commune = nombre_secheresse_commune.rename(columns={'cod_commune': 'Nombre_secheresse'})

    nombre_mvt_commune = pd.DataFrame(BaseGaspar[BaseGaspar['lib_risque_jo'] =='Mouvement de Terrain'].groupby('lib_commune')['cod_commune'].count().reset_index())
    nombre_mvt_commune = nombre_mvt_commune.rename(columns={'cod_commune': 'Nombre_mvt'})

    # Fusionner les DataFrames pour chaque type de catastrophe avec le DataFrame contenant le nombre total de cat_nat par commune
    data_zone = pd.merge(nombre_cat_nat_par_commune, nombre_inondation_commune, on='lib_commune', how='left')
    data_zone = pd.merge(data_zone, nombre_secheresse_commune, on='lib_commune', how='left')
    data_zone = pd.merge(data_zone, nombre_mvt_commune, on='lib_commune', how='left')
    data_zone = pd.merge(data_zone, BaseGaspar[['lib_commune', 'cod_commune']], on='lib_commune', how='left')

    # Si des valeurs sont manquantes (NaN), les remplacer par 0
    data_zone = data_zone.fillna(0)

    # Supprimer les doublons
    data_zone = data_zone.drop_duplicates()
    data_zone = pd.DataFrame(data_zone.groupby('lib_commune').sum().reset_index().drop('cod_commune', axis=1))

    DVF_stat  = DVF.groupby('Code_commune')['Valeur fonciere'].mean().reset_index()
    DVF_stat  = DVF_stat.rename(columns={'Valeur fonciere': 'Valeur moyenne'})

    DVF_stat2 = DVF.groupby('Code_commune')['Date mutation'].count().reset_index()
    DVF_stat2 = DVF_stat2.rename(columns={'Date mutation': 'Nombre_mutation'})

    DVF_stats = pd.merge(BasePop, DVF_stat, left_on='CODGEO', right_on='Code_commune', how='left')
    DVF_stats = pd.merge(DVF_stats, DVF_stat2, left_on='Code_commune', right_on='Code_commune', how='left')
    DVF_stats = DVF_stats.fillna(0)
    
    DVF_stats = pd.merge(DVF_stats, BaseMap, left_on='CODGEO', right_on='code_commune_INSEE', how='left')
    
    data_zone = pd.merge(data_zone, BaseGaspar[['lib_commune', 'cod_commune']], on='lib_commune', how='left')
    data_zone = pd.merge(data_zone, BaseMap, left_on='lib_commune', right_on='code_commune_INSEE', how='left')
    data_zone = data_zone.dropna()
############################

    left_one, left_two, right_one, right_two = st.columns(4)

    with left_one:
        st.markdown("<h1 style='font-family:Lucida Caligraphy;font-size:14px;color:DarkSlateBlue;text-align: center;'> Top 100 des communes avec les plus grandes valeurs de 'Valeur moyenne' </h1>", unsafe_allow_html=True)
        top_100_communes = DVF_stats.sort_values(by='Valeur moyenne', ascending=False).head(100)
        # Afficher uniquement les 20 premières communes sur la carte
        st.map(top_100_communes,
            latitude='latitude',
            longitude='longitude',
            size='Valeur moyenne'
        )
    with left_two:
        st.markdown("<h1 style='font-family:Lucida Caligraphy;font-size:14px;color:DarkSlateBlue;text-align: center;'> Top 100 des communes avec les plus grandes valeurs de 'Valeur moyenne' </h1>", unsafe_allow_html=True)
        top_100_communes = DVF_stats.sort_values(by='Valeur moyenne', ascending=False).head(100)
        st.map(top_100_communes,
            latitude='latitude',
            longitude='longitude',
            size='Valeur moyenne'
        )
    with right_one:
        st.markdown("<h1 style='font-family:Lucida Caligraphy;font-size:14px;color:DarkSlateBlue;text-align: center;'> Top 100 des communes avec les plus grandes valeurs de 'Valeur moyenne' </h1>", unsafe_allow_html=True)
        top_100_communes_freq = data_zone.sort_values(by='Nombre_cat_nat', ascending=False).head(100)
        st.map(top_100_communes_freq,
            latitude='latitude',
            longitude='longitude',
            size='Nombre_cat_nat'
        )
    with right_two:
        st.markdown("<h1 style='font-family:Lucida Caligraphy;font-size:14px;color:DarkSlateBlue;text-align: center;'> Top 100 des communes avec les plus grandes valeurs de 'Valeur moyenne' </h1>", unsafe_allow_html=True)
        top_100_communes = DVF_stats.sort_values(by='Valeur moyenne', ascending=False).head(100)
        st.map(top_100_communes,
            latitude='latitude',
            longitude='longitude',
            size='Valeur moyenne'
        )
        
##############################################################################################################################
############################################################ Page 3 ##########################################################
##############################################################################################################################

else :
    st.markdown(
    "<h1 style='text-align: center; color: black; padding: 10px; border-radius: 10px; background-color: #FFD3D3;'>Impact pour les assureurs</h1>",
    unsafe_allow_html=True
    )
    
    left_column, right_column = st.columns(2)
    
    cout = {
        'Pas de sinistre répertorié à CCR': 0,
        'Entre 0 et 1 0' : 5,
        'Entre 0 k¬ et 100 k¬': 50000,
        'Entre 100 k¬ et 500 k¬': 300000,
        'Entre 500 k¬ et 2 M¬': 1250000,
        'Entre 2 M¬ et 5 M¬': 3500000,
        'Entre 5 M¬ et 10 M¬': 7500000,
        'Entre 10 M¬ et 50 M¬': 27500000,
        'Supérieur à 10 M¬': 15000000,
        'Entre 50 M¬ et 100 M¬': 75000000,
        'Supérieur à 50 M¬': 75000000,
        'Supérieur à 100 M¬': 150000000
    }

    cout_moyen = {
        'Pas de sinistre répertorié à CCR': 0,
        'Entre 0 et 2,5 k¬': 1250,
        'Entre 2,5 et 5 k¬': 3750,
        'Entre 0 et 1 0' : 5,
        'Entre 5 et 10 k¬': 7500,
        'Entre 10 et 20k¬': 15000,
        'Plus de 20 k¬': 30000
    }


    frequence = centres_classes = {
        'Pas de sinistre ou de risque répertoriés à CCR': 0,
        'Entre 0 et 1 0': 0.5,
        'Entre 0 et 1 0' : 5,
        'Entre 1 et 2 0': 1.5,
        'Entre 2 et 5 0': 3.5,
        'Entre 2 et 5 0': 3.5,
        'Entre 5 et 10 0': 7.5,
        'Plus de 10 0': 15
    }

    ratio = {
        'Pas de sinistre ou de prime répertoriés à CCR': 0,
        'Entre 0 et 10 %': 5,
        'Entre 0 et 1 0' : 5,
        'Entre 10 et 50 %': 30,
        'Entre 50 et 100%': 75,
        'Entre 100 et 200 %': 150,
        'Plus de 200%': 250,
    }

    BaseCouts['Coût\nsécheresse'] = BaseCouts['Coût\nsécheresse'].replace(cout)
    BaseCouts['Coût moyen des sinistres\nsécheresse'] = BaseCouts['Coût moyen des sinistres\nsécheresse'].replace(cout_moyen)
    BaseCouts['Fréquence moyenne de sinistres\nsécheresse'] = BaseCouts['Fréquence moyenne de sinistres\nsécheresse'].replace(frequence)
    BaseCouts['S/P\nsécheresse'] = BaseCouts['S/P\nsécheresse'].replace(ratio)

    BaseCouts['Coût inondation '] = BaseCouts['Coût inondation '].replace(cout)
    BaseCouts['Coût moyen \ninondation'] = BaseCouts['Coût moyen \ninondation'].replace(cout_moyen)
    BaseCouts['Fréquence\ninondation'] = BaseCouts['Fréquence\ninondation'].replace(frequence)
    BaseCouts['S/P\ninondation\n'] = BaseCouts['S/P\ninondation\n'].replace(ratio)

    BaseCouts['Coût\nmouvement de terrain'] = BaseCouts['Coût\nmouvement de terrain'].replace(cout)
    BaseCouts['Coût moyen des sinistres\nmouvement de terrain'] = BaseCouts['Coût moyen des sinistres\nmouvement de terrain'].replace(cout_moyen)
    BaseCouts['Fréquence moyenne de sinistres\nmouvement de terrain'] = BaseCouts['Fréquence moyenne de sinistres\nmouvement de terrain'].replace(frequence)
    BaseCouts['S/P\nmouvement de terrain'] = BaseCouts['S/P\nmouvement de terrain'].replace(ratio)
    
    Sech = BaseCouts[['Code INSEE', 'Coût\nsécheresse', 'Coût moyen des sinistres\nsécheresse',
                  'Fréquence moyenne de sinistres\nsécheresse', 'S/P\nsécheresse']]
    Sech = Sech.rename(columns={
        'Coût\nsécheresse': 'Coût total',
        'Coût moyen des sinistres\nsécheresse': 'Coût moyen',
        'S/P\nsécheresse': 'Ratio',
        'Fréquence moyenne de sinistres\nsécheresse': 'Fréquence moyenne'
    })
    Sech['Cat_nat'] = 'Secheresses'

    Inon = BaseCouts[['Code INSEE', 'Coût inondation ', 'Coût moyen \ninondation',
                      'Fréquence\ninondation', 'S/P\ninondation\n']]
    Inon = Inon.rename(columns={
        'Coût inondation ': 'Coût total',
        'Coût moyen \ninondation': 'Coût moyen',
        'S/P\ninondation\n': 'Ratio',
        'Fréquence\ninondation': 'Fréquence moyenne'
    })
    Inon['Cat_nat'] = 'Inondations'

    Mvt = BaseCouts[['Code INSEE', 'Coût\nmouvement de terrain', 'Coût moyen des sinistres\nmouvement de terrain',
                      'Fréquence moyenne de sinistres\nmouvement de terrain', 'S/P\nmouvement de terrain']]
    Mvt = Mvt.rename(columns={
        'Coût\nmouvement de terrain': 'Coût total',
        'Coût moyen des sinistres\nmouvement de terrain': 'Coût moyen',
        'S/P\nmouvement de terrain': 'Ratio',
        'Fréquence moyenne de sinistres\nmouvement de terrain': 'Fréquence moyenne'
    })
    Mvt['Cat_nat'] = 'Mouvements de terrains'

    # Concaténation des DataFrames
    result = pd.concat([Sech, Inon, Mvt], ignore_index=True)
    result = pd.merge(BasePop, result, left_on='CODGEO', right_on='Code INSEE', how='left')

    # Trier par la colonne 'Code INSEE'
    result = result.sort_values(by='Code INSEE')
    
    with left_column :
        # Sélection de la palette de couleurs pour les daltoniens
        color_palettes = ['viridis', 'plasma', 'inferno', 'magma', 'cividis']
        selected_palette = st.selectbox('Palette de couleurs:', color_palettes)

        # Calcul de la matrice de corrélation
        correlation_matrix = result.drop(['Code INSEE', 'CODGEO', 'Cat_nat'], axis=1).corr()

        # Affichage de la matrice de corrélation avec seaborn et matplotlib
        mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))

        plt.figure(figsize=(8, 6))
        sns.heatmap(correlation_matrix, annot=True, cmap=selected_palette, mask=mask, vmin=-1, vmax=1)
        plt.title('Matrice de corrélation (triangulaire)')
        st.pyplot(plt)  # Afficher le graphique dans Streamlit

    with right_column :

        # Votre DataFrame pivotée
        pivot_df = BaseGaspar.pivot_table(index='mois', columns='lib_risque_jo', values='cod_nat_catnat', aggfunc='count', fill_value=0)
        df2 = pd.DataFrame(pivot_df)

        # Mapping des indices aux noms des mois
        mois_mapping = {
            1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
            7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
        }

        # Remplacement des indices par les noms des mois
        df2.index = df2.index.map(mois_mapping)

        # Création du graphique radar avec Plotly
        fig = go.Figure()

        for risk_type in df2.columns:
            fig.add_trace(go.Scatterpolar(
                r=df2[risk_type],
                theta=df2.index,
                fill='toself',
                name=risk_type
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                )
            ),
            showlegend=True
        )

        # Afficher le graphique radar dans Streamlit avec une taille personnalisée
        st.write(fig, width=800, height=600)


