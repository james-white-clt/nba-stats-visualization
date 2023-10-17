from flask import Flask, render_template, request, send_from_directory
import pandas as pd
import os
from plotly.subplots import make_subplots
import plotly.graph_objs as go

app = Flask(__name__)

# Determine the full path to the CSV files in the data folder
data_folder = os.path.join(os.path.dirname(__file__), 'data')
csv_file_path_totals = os.path.join(data_folder, '2022_nba_player_totals.csv')
csv_file_path_advanced = os.path.join(data_folder, '2022_nba_player_advanced.csv')

# Read the CSV file into a DataFrame
dataTotals = pd.read_csv(csv_file_path_totals)
dataAdvanced = pd.read_csv(csv_file_path_advanced)

# Route for home page
@app.route('/')
def index():
    return render_template('index.html')

# Route for plotly chart when loaded with data
@app.route('/plotly_chart')
def plotly_chart():
    # Process form data (selected stat and team) here
    if request.method == 'POST':
        selected_stat = request.form['selected_stat']
        selected_team = request.form['selected_team']
    else:
        selected_stat = request.args.get('selected_stat', 'PTS_PER')
        selected_team = request.args.get('selected_team', '')
        

    # Filter the data based on the selected team for both dataTotals and dataAdvanced
    if selected_team:
        filtered_data_totals = dataTotals[dataTotals['Tm'] == selected_team]
        filtered_data_advanced = dataAdvanced[dataAdvanced['Tm'] == selected_team]
    else:
        # No team selected, include all teams in both datasets
        filtered_data_totals = dataTotals
        filtered_data_advanced = dataAdvanced
    
    # Initialize variables for scatter plots
    x_label = ""
    y_label = ""
    
    if selected_stat == "PTS_PER":
        x_label = "Player Efficiency Rating (PER)"
        y_label = "Points per Game (PTS)"
        x_values = filtered_data_advanced['PER']  # Calculate PTS per game
        y_values = filtered_data_totals['PTS'] / filtered_data_totals['G']
        labels = filtered_data_totals['Player'] + ' (' + filtered_data_totals['Tm'] + ')'
    elif selected_stat == "AST_TOV":
        x_label = "Assists per Game (AST)"
        y_label = "Turnovers per Game (TOV)"
        x_values = filtered_data_totals['AST'] / filtered_data_totals['G']  # Calculate AST per game
        y_values = filtered_data_totals['TOV'] / filtered_data_totals['G']  # Calculate TOV per game
        labels = filtered_data_totals['Player'] + ' (' + filtered_data_totals['Tm'] + ')'
    elif selected_stat == "3PM_3PA":
        x_label = "3-Pointers Made per Game (3PM)"
        y_label = "3-Point Attempts per Game (3PA)"
        x_values = filtered_data_totals['3P'] / filtered_data_totals['G']  # Calculate 3PM per game
        y_values = filtered_data_totals['3PA'] / filtered_data_totals['G'] # Calculate 3PA per game
        labels = filtered_data_totals['Player'] + ' (' + filtered_data_totals['Tm'] + ')'
    else:
        return "Selected comparison not found."

    # Create a Plotly scatter plot
    fig = go.Figure(data=[go.Scatter(
        x=x_values,
        y=y_values,
        mode='markers',
        text=labels,
        marker=dict(
            size=8,
            opacity=0.7,
            color='skyblue'
        )
    )])

    fig.update_layout(
        xaxis_title=x_label,
        yaxis_title=y_label,
        title=f'NBA Players: {x_label} vs {y_label}',
        hovermode='closest'
    )

    

    # Convert Plotly figure to HTML
    chart_html = fig.to_html(full_html=False)

    return render_template('plotly_chart.html', chart_html=chart_html, selected_stat=selected_stat, selected_team=selected_team)

# Route for the NBA Teams page
@app.route('/nba_teams')
def nba_teams():
    # Process form data (selected stat and teams) here
    if request.method == 'POST':
        selected_stat = request.form['stat']
        selected_teams = request.form.getlist('teams')
    else:
        selected_stat = request.args.get('stat', 'W/L')
        selected_teams = request.args.getlist('teams')

    # Preload all team data
    team_data = {}  # Use a dictionary to store team data
    team_names = ["atlanta_hawks", "boston_celtics", "brooklyn_nets", "charlotte_hornets", "chicago_bulls", "cleveland_cavaliers", "dallas_mavericks", "denver_nuggets", "detroit_pistons", "golden_state_warriors", "houston_rockets", "indiana_pacers", "los_angeles_clippers", "los_angeles_lakers", "memphis_grizzlies", "miami_heat", "milwaukee_bucks", "minnesota_timberwolves", "new_orleans_pelicans", "new_york_knicks", "oklahoma_city_thunder", "orlando_magic", "philadelphia_76ers", "phoenix_suns", "portland_trail_blazers", "sacramento_kings", "san_antonio_spurs", "toronto_raptors", "utah_jazz", "washington_wizards"]  # Player names from csv files (ADD PLAYERS TO THIS LIST IF MORE PLAYER CSVs GET ADDED)
    for team_name in team_names:
        csv_file_path = f"data/teams/{team_name}.csv"  # Replace with the correct file path
        team_data[team_name] = pd.read_csv(csv_file_path, skiprows=2)
        team_data[team_name].columns = ['Rk', 'G', 'Date', 'Location', 'Opponent', 'W/L', 'TmPts', 'OpPts', 'TmFG', 'TmFGA', 'TmFG%', 'Tm3P', 'Tm3PA', 'Tm3P%', 'TmFT', 'TmFTA', 'TmFT%', 'TmORB', 'TmTRB', 'TmAST', 'TmSTL', 'TmBLK', 'TmTOV', 'TmPF', 'Separator', 'OpFG', 'OpFGA', 'OpFG%', 'Op3P', 'Op3PA', 'Op3P%', 'OpFT', 'OpFTA', 'OpFT%', 'OpORB', 'OpTRB', 'OpAST', 'OpSTL', 'OpBLK', 'OpTOV', 'OpPF']

    # Fetch data for selected teams
    selected_team_data = [team_data[team_name] for team_name in selected_teams]

    # Array of selected team names used for tracing
    selected_team_names = [convert_name(team_name) for team_name in selected_teams]

    # Render the chart as an HTML string
    chart_html = generate_team_comparison_chart(selected_stat, selected_team_data, selected_team_names)
    
    # Render the NBA team comparison page with the chart
    return render_template('nba_teams.html', chart_html=chart_html, selected_stat=selected_stat, selected_teams=selected_teams)

def generate_team_comparison_chart(selected_stat, team_data, selected_team_names):
    # Create a Plotly figure
    fig = go.Figure()

    # Initialize the is_percentage_stat variable outside the loop
    is_percentage_stat = selected_stat.endswith('%')

    # Iterate through team data
    for team_df, team_name in zip(team_data, selected_team_names):
        # Convert number stats into numeric
        if selected_stat not in ['W/L', 'Date', 'Location', 'Opponent', 'Separator']:
            team_df[selected_stat] = pd.to_numeric(team_df[selected_stat], errors='coerce')

        # Add the trace only if there are data points
        if not team_df.empty:
            if is_percentage_stat:
                # Convert the percentage values to actual percentages (multiply by 100)
                team_df[selected_stat] = team_df[selected_stat] * 100

            if selected_stat == 'W/L':
                fig.add_trace(go.Scatter(
                    x=team_df['Date'],  # Assuming 'Date' is the column with dates
                    y=team_df['TmPts'] - team_df['OpPts'],  # Use the selected stat as the y-values
                    mode='lines+markers',  # Line chart with markers
                    name=team_name,  # Player's name as the trace name
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=team_df['Date'],  # Assuming 'Date' is the column with dates
                    y=team_df[selected_stat],  # Use the selected stat as the y-values
                    mode='lines+markers',  # Line chart with markers
                    name=team_name,  # Player's name as the trace name
                ))
            

    # Customize the layout
    fig.update_layout(
        title=f'{selected_stat} Comparison',  # Title based on selected stat
        xaxis_title='Date',
        yaxis_title=selected_stat,
        hovermode='closest',
        legend=dict(orientation='h', yanchor='top', xanchor='center', x=0.5, y=1.15),
    )

    if is_percentage_stat:
        # Format the y-axis as percentages if it's a percentage stat
        fig.update_yaxes(tickformat='.2f')

    # Convert the Plotly figure to HTML
    chart_html = fig.to_html(full_html=False)

    return chart_html

# Route for the NBA Players page
@app.route('/nba_players', methods=['GET', 'Post'])
def nba_players():
    # Process form data (selected stat and players) here
    if request.method == 'POST':
        selected_stat = request.form['stat']
        selected_players = request.form.getlist('players')
    else:
        selected_stat = request.args.get('stat', 'MP')
        selected_players = request.args.getlist('players')

    # Preload all player data
    player_data = {}  # Use a dictionary to store player data
    player_names = ["andrew_wiggins", "anthony_davis", "anthony_edwards", "bam_adebayo", "ben_simmons", "bradley_beal", "brandon_ingram", "chris_paul", "damian_lillard", "darius_garland", "deaaron_fox", "dejounte_murray", "demar_derozan", "devin_booker", "domantas_sabonis", "donovan_mitchell", "draymond_green", "giannis_antetokounmpo", "ja_morant", "jalen_brunson", "jarrett_allen", "jaylen_brown", "jayson_tatum", "jimmy_butler", "joel_embiid", "jrue_holiday", "julius_randle", "karl-anthony_towns", "kawhi_leonard", "kevin_durant", "khris_middleton", "klay_thompson", "kyle_lowry", "kyrie_irving", "lamelo_ball", "lauri_markkanen", "lebron_james", "luka_doncic", "nikola_jokic", "pascal_siakam", "paul_george", "rudy_gobert", "russell_westbrook", "shai_gilgeous-alexander", "stephen_curry", "trae_young", "tyrese_haliburton", "zach_lavine", "zion_williamson"]  # Player names from csv files (ADD PLAYERS TO THIS LIST IF MORE PLAYER CSVs GET ADDED)
    for player_name in player_names:
        csv_file_path = f"data/players/{player_name}.csv"  # Replace with the correct file path
        player_data[player_name] = pd.read_csv(csv_file_path)

    # Fetch data for selected players
    selected_player_data = [player_data[player_name] for player_name in selected_players]

    # Array of selected player names used for tracing
    selected_player_names = [convert_name(player_name) for player_name in selected_players]

    # Render the chart as an HTML string
    chart_html = generate_player_comparison_chart(selected_stat, selected_player_data, selected_player_names)
    
    # Render the NBA player comparison page with the chart
    return render_template('nba_players.html', chart_html=chart_html, selected_stat=selected_stat, selected_players=selected_players)

def generate_player_comparison_chart(selected_stat, player_data, selected_player_names):
    # Create a Plotly figure
    fig = go.Figure()

    # Initialize the is_percentage_stat variable outside the loop
    is_percentage_stat = selected_stat.endswith('%')

    # Iterate through player data
    for player_df, player_name in zip(player_data, selected_player_names):
        # Filter out rows where player didn't play
        player_df_filtered = player_df[(player_df['G'] != "") & (~player_df['PTS'].str.contains('Did Not Play|Inactive|Did Not Dress'))]

        # Apply the time_to_minutes function to 'MP' column if 'selected_stat' is not 'MP'
        if selected_stat != 'MP':
            player_df_filtered[selected_stat] = pd.to_numeric(player_df_filtered[selected_stat], errors='coerce')
        else:
            player_df_filtered['MP'] = player_df_filtered['MP'].apply(time_to_minutes)

        # Add the trace only if there are data points left after filtering
        if not player_df_filtered.empty:
            if is_percentage_stat:
                # Convert the percentage values to actual percentages (multiply by 100)
                player_df_filtered[selected_stat] = player_df_filtered[selected_stat] * 100

            fig.add_trace(go.Scatter(
                x=player_df_filtered['Date'],  # Assuming 'Date' is the column with dates
                y=player_df_filtered[selected_stat],  # Use the selected stat as the y-values
                mode='lines+markers',  # Line chart with markers
                name=player_name,  # Player's name as the trace name
            ))

    # Customize the layout
    fig.update_layout(
        title=f'{selected_stat} Comparison',  # Title based on selected stat
        xaxis_title='Date',
        yaxis_title=selected_stat,
        hovermode='closest',
        legend=dict(orientation='h', yanchor='top', xanchor='center', x=0.5, y=1.15),
    )

    if is_percentage_stat:
        # Format the y-axis as percentages if it's a percentage stat
        fig.update_yaxes(tickformat='.2f')

    # Convert the Plotly figure to HTML
    chart_html = fig.to_html(full_html=False)

    return chart_html

# Function to convert player name from snake_case to a readable format
def convert_name(name):
    return name.replace('_', ' ').title()

# Function to convert the time format (MM:SS or M:SS) to a numeric value (in minutes)
def time_to_minutes(time_str):
    # Split the time string into minutes and seconds
    minutes, seconds = map(int, time_str.split(':'))
    # Calculate the total minutes
    total_minutes = minutes + (seconds / 60)
    return total_minutes

if __name__ == '__main__':
    app.run(debug=True)
