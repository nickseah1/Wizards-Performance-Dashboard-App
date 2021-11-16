import dash
from dash import html
import dash_bootstrap_components as dbc
from dash import dcc
import pandas as pd
import numpy as np
import urllib.request
from urllib.request import urlopen
from bs4 import BeautifulSoup
import plotly.express as px
import plotly

# Web Scraping
url = 'https://www.foxsports.com/nba/washington-wizards-team-game-log'
page = urlopen(url)
soup = BeautifulSoup(page, 'html.parser')
table = soup.find('table')

output_rows = []
for table_row in table.findAll('tr'):
    columns = table_row.findAll('td')
    output_row = []
    for column in columns:
        output_row.append(column.text)
    output_rows.append(output_row)

output_rows = output_rows[1:]

column_values = ['Date', 'Opponent', 'Score', 'FGM', 'FGA', 'FG%', 'FTM', 'FTA', 'FT%', '3FGM', '3FGA', '3FG%', 'PTS']

# Create a dataframe
df = pd.DataFrame(data=output_rows, columns=column_values)

# Preprocessing
# Remove /n from Date, Opponent, and Score Columns
df['Date'] = df['Date'].str.replace("\n", "")
df['Opponent'] = df['Opponent'].str.replace("\n", " ")

# Remove the whitespace on the left of the Score Column
df['Score'] = df['Score'].str.replace("\n", "").str.lstrip()
# Create a Result Column and Update Score Column
df[['Result', 'Score']] = df['Score'].str.split(' ', expand=True)
# Create Opponents Score Column
df['OpScore'] = df['Score'].str.split('-').str[1]

# Home or Away Column
df['H/A'] = df['Opponent'].str.split(' ').apply(lambda x: 'Away' if (x[1] == '@') else 'Home')

# Drop Games that haven't been played yet from the data
df = df.dropna(axis=0, how='any')

# Covert the following columns to the int type
int_cols = ['FGM', 'FGA', 'FTM', 'FTA', '3FGM', '3FGA', 'PTS', 'OpScore']
df[int_cols] = df[int_cols].astype(int)
# Convert the following columns to the float type
float_cols = ['FG%', 'FT%', '3FG%']
df[float_cols] = df[float_cols].astype(float)

# Format Opponent Column
df['Opponent'] = df['Opponent'].str.replace('@', '')
df['Opponent'] = df['Opponent'].str.replace('vs', '')

# Win Percentage Function
wins = []
win_percentage = []


def rollingWinPercentage(series):
    result = series
    for element in range(0, len(result)):
        if result[element] == 'W':
            wins.append(1)
        else:
            wins.append(0)

        wp = (sum(wins) / len(wins)) * 100
        win_percentage.append(round(wp, 2))

    return win_percentage


Win_Percentage = pd.Series(rollingWinPercentage(df['Result']))

# Feature Engineering

# Create a point differential column
df['PointDiff'] = df['PTS'] - df['OpScore']

# Effective Field Goal Percentage
df['EFG%'] = (((df['FGM'] + 0.5 * df['3FGM']) / df['FGA']) * 100).round(2)

# Free Throw Rate
df['FTR'] = ((df['FTM'] / df['FGA']) * 100).round(2)

# Win Percentage Column
df['Win Percentage'] = Win_Percentage


# Line Plot function

def lineplot(dataframe, xcol, ycol, Graph_title):
    fig = px.line(dataframe,
                  x=xcol,
                  y=ycol,
                  title=Graph_title,
                  template='simple_white',
                  markers=True)

    # fig = px.line(df, x = 'Date', y = 'PointDiff', title = 'Point Differential',template = 'simple_white')
    fig.update_layout(title_x=0.5,
                      font=dict(size=18, color='#002B5C'),
                      plot_bgcolor='rgba(0, 0, 0, 0)',
                      paper_bgcolor='rgba(0, 0, 0, 0)',
                      xaxis_title='Season Start to End')
    fig.update_xaxes(showticklabels=False)
    fig.update_traces(line_color='#002B5C')

    return fig


line_p = lineplot(df, 'Date', 'Win Percentage', '<b>Rolling Win Percentage<b>')

EFGP = df['EFG%'].mean()
Perc_3 = df['3FG%'].mean()
FTP = df['FT%'].mean()

# home_win_loss
home_wins = len(df[(df['Result'] == 'W') & (df['H/A'] == 'Home')])
home_losses = len(df[(df['Result'] == 'L') & (df['H/A'] == 'Home')])
home_wl = str(home_wins) + '-' + str(home_losses)
# Home Win %
home_win_percentage = str(round((home_wins / (home_wins + home_losses) * 100), 2)) + '%'

# away_win_loss
road_wins = len(df[(df['Result'] == 'W') & (df['H/A'] == 'Away')])
road_losses = len(df[(df['Result'] == 'L') & (df['H/A'] == 'Away')])
road_wl = str(road_wins) + '-' + str(road_losses)
road_win_percentage = str(round((road_wins / (road_wins + road_losses) * 100), 2)) + '%'

# overall win_loss
wins = len(df[df['Result'] == 'W'])
losses = len(df[df['Result'] == 'L'])
wl = str(wins) + '-' + str(losses)
win_per = str(round((wins / (wins + losses) * 100), 2)) + '%'

# Pie Chart
# Proportion of Home Games Pie Chart

# Count of home games
count_home = len(df[df['H/A'] == 'Home'])
# Count List of away games
count_away = len(df[df['H/A'] == 'Away'])
# To a List
value = [count_home, count_away]
name = ['Home', 'Away']

# Pie Chart
fig = px.pie(df,
             values=value,
             names=name,
             title='<b>Proportion of Home Games<b>',
             color=name,
             color_discrete_map={'Home': '#002B5C', 'Away': '#E31837'})
fig.update_layout(title_x=0.5, font=dict(size=18, color='#002B5C'))
fig.update_traces(textposition='inside', textinfo='percent+label')
fig.update_layout(showlegend=False, plot_bgcolor='rgba(0, 0, 0, 0)', paper_bgcolor='rgba(0, 0, 0, 0)')

# App Configuration

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_stylesheets = [dbc.themes.SIMPLEX]

app = dash.Dash(__name__,
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1, maximum-scale=1.2, minimum-scale=0.5,'}],
                external_stylesheets=external_stylesheets)

app.config.suppress_callback_exceptions = True
server = app.server

# App Layout


overall_record = wl
overall_win_p = win_per
home_record = home_wl
home_win_p = home_win_percentage
away_record = road_wl
away_win_p = road_win_percentage
three_per = str(round(Perc_3, 2)) + ' %'
efg_per = str(round(EFGP, 2)) + ' %'
ft_per = str(round(FTP, 2)) + ' %'

app.layout = dbc.Container([
    dcc.Markdown(style={'margin-bottom': '10px'}),

    html.H1("Washington Wizards Performance", style={'color': '#002B5C', 'fontWeight': 'bold'}),

    html.Hr(style={'color': '#002B5C'}),

    dbc.Row([
        dbc.Col(html.H3('Overall', style={'color': '#002B5C', 'fontWeight': 'bold'})),
        dbc.Col(html.H3('Home', style={'color': '#002B5C', 'fontWeight': 'bold'})),
        dbc.Col(html.H3('Away', style={'color': '#002B5C', 'fontWeight': 'bold'}))

    ]),

    dbc.Row([
        dbc.Col(html.Div('Record'), style={'fontWeight': 'bold'}),
        dbc.Col(html.Div('Win Percentage'), style={'fontWeight': 'bold'}),
        dbc.Col(html.Div('Record'), style={'fontWeight': 'bold'}),
        dbc.Col(html.Div('Win Percentage'), style={'fontWeight': 'bold'}),
        dbc.Col(html.Div('Record'), style={'fontWeight': 'bold'}),
        dbc.Col(html.Div('Win Percentage'), style={'fontWeight': 'bold'}),
    ]),

    dbc.Row([
        dbc.Col(html.Div(overall_record)),
        dbc.Col(html.Div(overall_win_p)),
        dbc.Col(html.Div(home_record)),
        dbc.Col(html.Div(home_win_p)),
        dbc.Col(html.Div(away_record)),
        dbc.Col(html.Div(away_win_p)),
    ]),
    html.Hr(style={'color': '#002B5C', 'margin-bottom': '20px'}),

    dbc.Row(
        dbc.Col(html.H3('Key Performance Indicators',  style={'fontWeight': 'bold'})),
        style={'margin-bottom': '10px', 'color': '#002B5C'}),

    dbc.Container(
        [
            dbc.Row([
                dbc.Col(html.Div('3 Point Percentage'), style={'fontWeight': 'bold'}),
                dbc.Col(html.Div('Effective Field Goal Percentage'), style={'fontWeight': 'bold'}),
                dbc.Col(html.Div('Free Throw Percentage'), style={'fontWeight': 'bold'})
            ]),
            dbc.Row([
                dbc.Col(html.P(three_per)),
                dbc.Col(html.P(efg_per)),
                dbc.Col(html.P(ft_per))
            ]),
        ]),

    html.Hr(style={'color': '#002B5C'}),

    dbc.Row([
        dbc.Col(dcc.Graph(id='interactivegraph', figure=line_p)),
        dbc.Col(dcc.Graph(id='homegraph', figure=fig))
    ]),

], style={'text-align': 'center', 'color': '#002B5C'})
# 'backgroundColor': '#002B5C'

# Main Function
if __name__ == '__main__':
    app.run_server(debug=True)
