import dash
import json
import numpy as np
import pandas as pd
import calendar
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO
from dash import Dash, html, dcc,Input, Output,callback
from jupyter_dash import JupyterDash
from dash.dash_table import DataTable
from plotly.subplots import make_subplots
from dash.dash_table import DataTable, FormatTemplate
from dash.dash_table.Format import Format, Group

with open("C:/Users/mauri/Downloads/departements.geojson") as f:
    carte = json.loads(f.read())

    
#################################################################################################################################
#                                           Base de données de transformations                                                  #
#################################################################################################################################



def read_csv_from_url_with_encoding(url):
    try:
        content = requests.get(url).content.decode('utf-8')
        return pd.read_table(StringIO(content), sep='|',low_memory=False)
    except UnicodeDecodeError:
        try:
            content = requests.get(url).content.decode('ISO-8859-1')
            return pd.read_table(StringIO(content), sep='|',low_memory=False)
        except UnicodeDecodeError:
            content = requests.get(url).content.decode('CP1252')
            return pd.read_table(StringIO(content), sep='|',low_memory=False)

# Application
BasePop = read_csv_from_url_with_encoding('https://raw.githubusercontent.com/EuniceKOFFI/Challenge-Data-Visualisation/main/BasePop.txt')
BaseCouts = read_csv_from_url_with_encoding('https://raw.githubusercontent.com/EuniceKOFFI/Challenge-Data-Visualisation/main/BaseCouts.txt')
BaseGaspar = read_csv_from_url_with_encoding('https://raw.githubusercontent.com/EuniceKOFFI/Challenge-Data-Visualisation/main/BaseGaspar.txt')

DVF = pd.read_table("C:/Users/mauri/Downloads/DVF.txt", sep="|", low_memory=False)

# Transformation des dates
BaseGaspar['dat_deb'] = pd.to_datetime(BaseGaspar['dat_deb'], format='%Y-%m-%d %H:%M:%S')
BaseGaspar['dat_fin'] = pd.to_datetime(BaseGaspar['dat_fin'], format='%Y-%m-%d %H:%M:%S')

# Calcul de la durée 
BaseGaspar['duree'] = BaseGaspar['dat_fin'] - BaseGaspar['dat_deb'] + pd.Timedelta(days=1)
BaseGaspar['annee'] = BaseGaspar['dat_deb'].dt.year
BaseGaspar['mois'] = BaseGaspar['dat_deb'].dt.month

DVF_stat  = DVF.groupby('Code_commune')['Valeur fonciere'].mean().reset_index()
DVF_stat['Valeur fonciere'] = np.log(DVF_stat['Valeur fonciere'])
DVF_stat  = DVF_stat.rename(columns={'Valeur fonciere': 'Valeur moyenne'})

DVF_stat2 = DVF.groupby('Code_commune')['Date mutation'].count().reset_index()
DVF_stat2 = DVF_stat2.rename(columns={'Date mutation': 'Nombre_mutation'})

DVF_stats = pd.merge(BasePop, DVF_stat, left_on='CODGEO', right_on='Code_commune', how='left')
DVF_stats = pd.merge(DVF_stats, DVF_stat2, left_on='Code_commune', right_on='Code_commune', how='left')
DVF_stats = DVF_stats.fillna(0)

DVF_stats['cod_dpt'] = DVF_stats['CODGEO'].str[:2]

carte_bh = pd.DataFrame(DVF_stats.groupby('cod_dpt')['Valeur moyenne'].sum().reset_index())
carte_pop = pd.DataFrame(DVF_stats.groupby('cod_dpt')['Population en 2020'].sum().reset_index())

numeric_colsF1 = result.select_dtypes(include=np.number).columns
correlation_matrixF1 = result[numeric_colsF1].corr()

# Création d'un masque pour la partie triangulaire inférieure
maskF1 = np.tril(np.ones_like(correlation_matrixF1, dtype=bool))

# Remplacez la partie triangulaire inférieure par NaN pour la masquer
correlation_matrixF1 = correlation_matrixF1.mask(maskF1)



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


frequence =  {
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
result = pd.concat([Sech, Inon, Mvt], ignore_index=True).sort_values(by='Code INSEE')
result = pd.merge(BasePop, result, left_on='CODGEO', right_on='Code INSEE', how='left')
result.Ratio = result.Ratio.fillna(0)
result['cod_dpt'] = result['CODGEO'].str[:2]
result = result.sort_values(by='Code INSEE')
carte_ratio = pd.DataFrame(result[result['Ratio']!=0].groupby('cod_dpt')['Ratio'].mean().reset_index())


def ppp():
    
    pivot_df = BaseGaspar.pivot_table(index='mois', columns='lib_risque_jo', values='cod_nat_catnat', aggfunc='count', fill_value=0)
    df2 = pd.DataFrame(pivot_df)

    # Mapping des indices aux noms des mois
    mois_mapping = {
        1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
        7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
    }

    # Remplacement des indices par les noms des mois
    df2.index = df2.index.map(mois_mapping)
    #df2.index = df2.index.map(mois_mapping)[::-1]

    # Création du graphique radar avec Plotly
    fig = go.Figure()

    for risk_type in df2.columns:
        fig.add_trace(go.Scatterpolar(
            r=df2[risk_type],
            theta=df2.index,
            fill='toself',
            name=risk_type ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
            )),
        showlegend=True,
        title="Etude de la saisonnalité des CatNats")
    
    return fig




#################################################################################################################################
#                                           Interfaces graphiques de l'application                                              #
#################################################################################################################################

tab_selected_style1 = {
    'borderTop': '3px solid #000000',
    'borderBottom': '0px solid yellow',
    'backgroundColor': '#FFD400',  
    'color': 'black',
    'padding': '20px'
}
tab_selected_style2 = {
    'borderTop': '0px solid #000000',
    'borderBottom': '0px solid yellow',
    'backgroundColor': '#FFD400', 
    'color': 'black',
    'padding': '20px' 
}

onglets=    html.Div([

        html.Div([
        html.Div([
        
        html.Div([
                html.Img(src='https://www.science-accueil.org/wp-content/uploads/2020/06/LOGO-ENSAE-2.png',
                                 style={'width': '100px','height':'50px'}),
                html.Div("ENSAEML", style={ 'fontWeight': 'bold',  'fontSize': 21} )
                    ], style={"display": "flex", "flexWrap": "wrap",'margin-right': 'auto'}),
            
        dcc.Tabs([
                dcc.Tab(label="Sinistralité 1", value="sinistre1", selected_style= tab_selected_style1),
                dcc.Tab(label="Sinistralité 2", value="sinistre2", selected_style= tab_selected_style1),
                dcc.Tab(label="Zones à risque", value="sinistre3", selected_style= tab_selected_style1),
                dcc.Tab(label="Impact", value="sinistre4", selected_style= tab_selected_style1)
                ],id="onglets", value="sinistre1",vertical=True, style={'height':200,'width': 200,'font-family':'Calibri'})
    
           ],style = {'background-color': 'white','height':880,'width':205}),
    
         html.Div(id='page',style = {'background-color': 'white','height':880,'width':1370})],
          style = { "display": "flex", "flexWrap": "wrap"} ) 
                
                ])

############################################################ Les pages ##########################################################

#### Tableaux

years_list = BaseGaspar['annee'].unique()
durees_moyennes_par_annee = BaseGaspar.groupby(['annee', 'lib_risque_jo'])['duree'].mean().reset_index()
durees_moyennes_par_annee['duree']=durees_moyennes_par_annee['duree'].dt.days

page_freq1= html.Div([ 
    
html.Div("Etude de la sinistralité", style={ 'fontWeight': 'bold',  'fontSize': 20, 'padding': '10px',
                            'height': '15px', 'width': '1400px', 'textAlign': 'center' , 'backgroundColor': '#FFB6C1'} ),

html.Div([
        html.Div( [ 
                html.Div([
                   html.B("Période"),
                   dcc.RangeSlider(2000, max(years_list),1,value=[2000,2023],
                                   marks={i: f'{i}' for i in range(2000,
                                                                   max(years_list))},
                                id='Perimetre_temporel1',tooltip={"placement": "bottom", "always_visible": True},
                                  persistence=True, persistence_type='local')],
                                style = {'background-color': 'white',  'margin-left': 'auto',
                                                            'margin-right': 'auto'} )
                   ]),
html.Div([  
    
    html.Div([
        dcc.Loading([dcc.Graph(id="graphe_sina1")], type="circle",fullscreen=False),
        
    ],style = {'background-color': 'white','width':650,'height':400}), 
    
    #html.Div(children=[],style = {'background-color': 'black','width':5,'height':400}),
    html.Div(children=[],style = {'background-color': 'white','width':15,'height':400}),
    
    html.Div([
        dcc.Loading([dcc.Graph(id="graphe_sinb1")], type="circle",fullscreen=False)],
         style = {'background-color': 'white','width':700,'height':400})
    
],style = { 'margin-left': 'auto','margin-right': 'auto',"display": "flex", "flexWrap": "wrap"} ),
    
html.Div([  
    
    html.Div([
        dcc.Loading([dcc.Graph(id="graphe_sinc1")], type="circle",fullscreen=False),
        
    ],style = {'background-color': 'white','width':650,'height':400}), 
    
    #html.Div(children=[],style = {'background-color': 'black','width':5,'height':400}),
    html.Div(children=[],style = {'background-color': 'white','width':15,'height':400}),
    
    html.Div([
        ],
         style = {'background-color': 'white','width':700,'height':400})
    
],style = { 'margin-left': 'auto','margin-right': 'auto',"display": "flex", "flexWrap": "wrap"} )
    
    
],style={'font-family':'Calibri'})
             ],style = { 'margin-left': 'auto','margin-right': 'auto',"display": "flex", "flexWrap": "wrap"} )

page_freq2= html.Div([ 
    
html.Div("Etude de la sinistralité", style={ 'fontWeight': 'bold',  'fontSize': 20, 'padding': '10px',
                            'height': '15px', 'width': '1400px', 'textAlign': 'center' , 'backgroundColor': '#FFB6C1'} ),

html.Div([
     
html.Div([  
    
    html.Div([
        dcc.Graph(id="graphe_sina2",figure= ppp() )]
        
    ,style = {'background-color': 'white','width':650,'height':400}), 
    
    #html.Div(children=[],style = {'background-color': 'black','width':5,'height':400}),
    html.Div(children=[],style = {'background-color': 'white','width':15,'height':400}),
    
    html.Div([
        dcc.Graph(id="graphe_sinb2",figure = px.line(durees_moyennes_par_annee, x='annee', y='duree', color='lib_risque_jo',
              title='Durées moyennes en jours des sinistres par année et par type de catnat',
              labels={'annee': 'Année', 'duree': 'Durée moyenne', 'lib_risque_jo': 'Type de cat nat'}))],
         style = {'background-color': 'white','width':700,'height':400})
    
],style = { 'margin-left': 'auto','margin-right': 'auto',"display": "flex", "flexWrap": "wrap"} ),
    
    
    
],style={'font-family':'Calibri'})
             ],style = { 'margin-left': 'auto','margin-right': 'auto',"display": "flex", "flexWrap": "wrap"} )


page_freq3= html.Div([ 
    
html.Div("Identifications des zones à risques", style={ 'fontWeight': 'bold',  'fontSize': 20, 'padding': '10px',
                            'height': '15px', 'width': '1400px', 'textAlign': 'center' , 'backgroundColor': '#FFB6C1'} ),

html.Div([
        html.Div( [ 
                html.Div([
                   html.B("Période"),
                   dcc.RangeSlider(2000, max(years_list),1,value=[2000,2023],
                                   marks={i: f'{i}' for i in range(2000,
                                                                   max(years_list))},
                                id='Perimetre_temporel3',tooltip={"placement": "bottom", "always_visible": True},
                                  persistence=True, persistence_type='local')],
                                style = {'background-color': 'white',  'margin-left': 'auto',
                                                            'margin-right': 'auto'} )
                   ]),
html.Div([ 
    
     html.Div([
        dcc.RadioItems(
        ['Inondations', 'Sécheresse', 'Mouvement de Terrain'], 'Inondations',id='idcarte', inline=True)
        
    ],style = {'background-color': 'white','width':900,'height':40}),
    
    html.Div([
        
        dcc.Loading([dcc.Graph(id="graphe_sina3")], type="circle",fullscreen=False),
        
    ],style = {'background-color': 'white','width':650,'height':400}), 
    
    #html.Div(children=[],style = {'background-color': 'black','width':5,'height':400}),
    html.Div(children=[],style = {'background-color': 'white','width':15,'height':400}),
    
    html.Div([
        dcc.Graph(id="graphe_sinb3",figure=px.choropleth_mapbox(data_frame=carte_bh, geojson=carte,locations='cod_dpt',featureidkey='properties.code',
                                    mapbox_style="white-bg",zoom=4.3,center = {"lat": 47.0, "lon": 4.0},
                                    color = carte_bh['Valeur moyenne'],
                                    hover_name='cod_dpt',
                                    #color_continuous_scale= "Viridis",
                                    title="Les départements avec les biens les plus onéreux"))],
         style = {'background-color': 'white','width':700,'height':400})
    
],style = { 'margin-left': 'auto','margin-right': 'auto',"display": "flex", "flexWrap": "wrap"} ),
    
    
html.Div([  
    
    html.Div([
        dcc.Graph(id="graphe_sinc3",figure=px.choropleth_mapbox(data_frame=carte_pop, geojson=carte,locations='cod_dpt',featureidkey='properties.code',
                                    mapbox_style="white-bg",zoom=4.3,center = {"lat": 47.0, "lon": 4.0},
                                    color = carte_pop['Population en 2020'],
                                    hover_name='cod_dpt',
                                    #color_continuous_scale= "Viridis",
                                    title="Nombre d'habitants par département"))
        
    ],style = {'background-color': 'white','width':650,'height':400}), 
    
    #html.Div(children=[],style = {'background-color': 'black','width':5,'height':400}),
    html.Div(children=[],style = {'background-color': 'white','width':15,'height':400}),
    
    html.Div([
        dcc.Graph(id="graphe_sind3",figure = px.choropleth_mapbox(data_frame=carte_ratio, geojson=carte,locations='cod_dpt',featureidkey='properties.code',
                                    mapbox_style="white-bg",zoom=4.3,center = {"lat": 47.0, "lon": 4.0},
                                    color = carte_ratio['Ratio'],
                                    hover_name='cod_dpt',
                                    #color_continuous_scale= "Viridis",
                                    title="Le Ratio moyen par département"))],
         style = {'background-color': 'white','width':700,'height':400})
    
],style = { 'margin-left': 'auto','margin-right': 'auto',"display": "flex", "flexWrap": "wrap"} )
    
    
],style={'font-family':'Calibri'})
             ],style = { 'margin-left': 'auto','margin-right': 'auto',"display": "flex", "flexWrap": "wrap"} )

page_freq4= html.Div([ 
    
html.Div("Etude de la sinistralité", style={ 'fontWeight': 'bold',  'fontSize': 20, 'padding': '10px',
                            'height': '15px', 'width': '1400px', 'textAlign': 'center' , 'backgroundColor': '#FFB6C1'} ),

html.Div([
        
dcc.Graph(id="graphe_sina4", figure = px.imshow(correlation_matrixF1,
                                    labels=dict(x="Variables", y="Variables", color="Corrélation"),
                                    x=correlation_matrix.columns,
                                    y=correlation_matrix.columns,
                                    color_continuous_scale="viridis",
                                    title="Matrice de corrélation triangulaire entre coûts de sinistre, population, ...")
) ]) ])
    
         



#################################################################################################################################
#                                                            Application                                                        #
#################################################################################################################################

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets,suppress_callback_exceptions=True)

# Layout
app.layout = html.Div([
                        onglets
                        ])


@app.callback(
    Output('page', 'children'),
    Input('onglets', 'value')) 

def mja(a):
    if a == 'sinistre1':
        return page_freq1
    elif a =='sinistre2':
        return page_freq2
    elif a =='sinistre3':
        return page_freq3
    else:
        return page_freq4
    

@app.callback(
    [Output('graphe_sina1', 'figure'),Output('graphe_sinb1', 'figure'),
     Output('graphe_sinc1', 'figure')],
    Input('Perimetre_temporel1', 'value'))

def mja(a):

    df2=BaseGaspar.copy() 
    df2=df2[(df2.annee>=a[0]) & (df2.annee<=a[1])]
    data_for_year = df2
    count_by_month_risk = data_for_year.groupby(['mois', 'lib_risque_jo'])['cod_nat_catnat'].nunique().unstack().reset_index()

    # Convertir les chiffres des mois en noms de mois complets
    count_by_month_risk['mois'] = count_by_month_risk['mois'].apply(lambda x: calendar.month_name[x])

    # Création d'un dictionnaire pour spécifier l'ordre des mois
    month_order = {month: index for index, month in enumerate(calendar.month_name) if month}

    # Réorganiser les mois dans l'ordre souhaité sur l'axe x
    count_by_month_risk['mois'] = count_by_month_risk['mois'].map(month_order)

    fig = px.bar(count_by_month_risk, x='mois', y=count_by_month_risk.columns[1:], 
                 title=f'Nombre de catnat par mois entre {a}',
                 labels={'value': 'Nombre de cod_nat_catnat unique', 'mois': 'Mois'},
                 color_discrete_sequence=px.colors.qualitative.Safe)  # Utilisation de la palette de couleurs adaptées

    fig.update_layout(barmode='stack', xaxis={'tickmode': 'array', 'tickvals': list(month_order.values()),
                    'ticktext': list(month_order.keys())})
    
    fig2 = px.line(durees_moyennes_par_annee, x='annee', y='duree', color='lib_risque_jo',
              title='Durées moyennes en jours des sinistres par année et par type de catnat',
              labels={'annee': 'Année', 'duree': 'Durée moyenne', 'lib_risque_jo': 'Type de cat nat'})
    
    data_year = df2
    count_communes_par_catnat = data_year.groupby('lib_risque_jo')['cod_commune'].nunique().reset_index()
    count_communes_par_catnat = count_communes_par_catnat.rename(columns={'cod_commune': 'Nombre de communes'})
    count_communes_par_catnat['Nombre de communes'] = count_communes_par_catnat['Nombre de communes'].round(decimals=1)
    # Utiliser une palette de couleurs adaptée aux daltoniens
    color_palette = px.colors.qualitative.Safe

    # Appliquer la palette de couleurs
    count_communes_par_catnat['color'] = count_communes_par_catnat['lib_risque_jo'].map(dict(zip(
        count_communes_par_catnat['lib_risque_jo'].unique(), color_palette)))
    
    fig3 = px.pie(count_communes_par_catnat, values='Nombre de communes', names='lib_risque_jo',
                 title=f'Nombre de communes touchées entre {a} par type de catnat',
                 hole=0.4,
                 color='color')  # Utilisation de la colonne de couleurs adaptées
    
    fig3.update_traces(marker=dict(colors=count_communes_par_catnat['color']))
    
    count_communes_par_cod_catnat = df2.groupby('cod_nat_catnat')['cod_commune'].nunique().reset_index()
    count_communes_par_cod_catnat = count_communes_par_cod_catnat.rename(columns={'cod_commune': 'Nombre de communes'})
    
    top_10_communes = count_communes_par_cod_catnat.nlargest(10, 'Nombre de communes')

    fig4 = go.Figure(go.Treemap(
        labels=top_10_communes['cod_nat_catnat'],
        parents=[''] * len(top_10_communes),
        values=top_10_communes['Nombre de communes'],
        text=[f"Label: {BaseGaspar.loc[BaseGaspar['cod_nat_catnat'] == row['cod_nat_catnat'], 'lib_risque_jo'].iloc[0]}<br>"
              f"Début: {BaseGaspar.loc[BaseGaspar['cod_nat_catnat'] == row['cod_nat_catnat'], 'dat_deb'].iloc[0]}<br>"
              f"Durée: {BaseGaspar.loc[BaseGaspar['cod_nat_catnat'] == row['cod_nat_catnat'], 'duree'].iloc[0]} jours <br>"
              f"Nombre de communes touchées: {row['Nombre de communes']} communes <br>"
              for _, row in top_10_communes.iterrows()],
    ))

    fig4.update_layout(
        title=f'Top 10 des catnat en fonction du nombre de communes touchées entre {a}',
        treemapcolorway=px.colors.qualitative.Safe,
        title_font=dict(size=15)
    )

    fig4

    #fig2.update_layout(title_font=dict(size=15))
    return fig,fig4,fig3


    
@app.callback(
    Output('graphe_sina3', 'figure'),
    [Input('Perimetre_temporel3', 'value'),Input('idcarte', 'value')])

def mja(a,r):
    
    df2=BaseGaspar.copy() 
    df2=df2[(df2.annee>=a[0]) & (df2.annee<=a[1])]
    df2['cod_dpt'] = df2['cod_commune'].str[:2]

    xc=pd.DataFrame(df2[df2['lib_risque_jo'] ==r].groupby('cod_dpt')['cod_nat_catnat'].count().reset_index())
    xc = xc.rename(columns={'cod_nat_catnat': r})
    
    fig1=px.choropleth_mapbox(data_frame=xc, geojson=carte,locations='cod_dpt',featureidkey='properties.code',
                                    mapbox_style="white-bg",zoom=4.3,center = {"lat": 47.0, "lon": 4.0},
                                    color = xc[r],
                                    hover_name='cod_dpt',
                                    color_continuous_scale= "Viridis",
                                    title=f"Nombre d'{r} par département entre {a}")
    return fig1

if __name__ == "__main__":
    app.run_server(debug=True, port=52)