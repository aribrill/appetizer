#!/usr/bin/env python
# coding: utf-8


"""
Appetizer: a web app to help choose recipes for the week
"""


from itertools import compress
import os
import random
import sys

from dash import Dash, html, dcc, Input, Output, State
import pandas as pd


def get_recipe_indices(df, recipes):
    """Gets a list of indices in df corresponding to the recipes"""
    inds = []
    for recipe in recipes:
        inds.append(int(df[df['Recipe'] == recipe].index.values))
    return inds


def filter_col(df, col, prev_inds):
    """Selects rows NOT matching any previous recipes
    in the relevant category of columns
    """
    col_filter = df.columns.str.startswith(f"{col}_")
    mask = df.loc[prev_inds, col_filter].sum(0).astype(bool)
    return ((df[df.columns[col_filter]] * mask) ^ 1).all(axis=1)


def select_meals(df, meals):
    """Selects recipes appropriate for the specified meals"""
    mask = pd.Series(False, df.index)
    for meal in meals:
        mask |= df[f"Meal_{meal}"]
    return mask


def select_servings(df, servings=None):
    """Selects recipes appropriate for the specified servings"""
    mask = pd.Series(True, df.index)
    if servings is not None:
        mask &= df['Min Servings'] <= servings
        mask &= df['Max Servings'] >= servings
    return mask


def get_recipe_recommendations(df, prev_recipes, meals, servings, seed):
    """
    Returns a dataframe of recommended recipes that are dissimilar to previous
    recipes, are appropriate for the chosen meals, and can provide the chosen
    number of servings.

    Dissimilarity is determined based on four categories: in decreasing
    importance, Protein, Cusine, Form, and Starch.
    Recommendations must be dissimilar in at least one category, and are ranked
    1-4 based on how many categories they are dissimilar in.

    The recommendations are shuffled within each ranking level. A random seed
    is provided to ensure that the order is consistent whenever the "Suggest
    Recipe" button is pressed. The seed is randomized on app initialization so
    that the ordering varies from session to session.
    """
    if prev_recipes is None:
        prev_recipes = []
    prev_inds = get_recipe_indices(df, prev_recipes)
    recommendation_categories = ['Protein', 'Cuisine', 'Form', 'Starch']

    recommendations = []
    ratings = []
    mask = pd.Series(True, df.index)
    mask &= ~df.index.isin(prev_inds)
    mask &= select_meals(df, meals)
    mask &= select_servings(df, servings)

    for rating in range(len(recommendation_categories), 0, -1):
        rating_mask = mask.copy()
        for col in recommendation_categories[:rating]:
            rating_mask &= filter_col(df, col, prev_inds)
        selected_recipes = df[rating_mask]['Recipe']
        shuffled_recipes = selected_recipes.sample(frac=1, random_state=seed)
        recommendations.append(shuffled_recipes)
        ratings.extend([rating]*len(shuffled_recipes))
        mask &= ~rating_mask

    recommendations = pd.concat(recommendations, axis=0)
    ratings = pd.Series(data=ratings, index=recommendations.index,
                        name='Rating')
    recommendations = pd.concat([recommendations, ratings], axis=1)
    return recommendations


def select_recommendation(df, recommendations, i):
    """Formats the recommendation for display"""
    if len(recommendations) == 0 or i >= len(recommendations):
        return "No more recipes to recommend!"
    recommendation = recommendations['Recipe'].iloc[i]
    rating = recommendations['Rating'].iloc[i]
    stars = '*' * rating
    notes = df['Notes'][recommendations.index[i]]
    if notes is None:
        notes = ""
    markdown = f"""
    ## {recommendation} | {stars}
    {notes}
    """
    return markdown




def merge_strings(*strings):
    """Merge strings unless any is null"""
    if None in strings:
        return ""
    return "".join(strings)


def get_recipe_inspiration(df, categories, prev_recipes):
    """Generates a random recipe idea using categories
    dissimilar to the previous recipes"""

    if prev_recipes is None:
        prev_recipes = []
    prev_inds = get_recipe_indices(df, prev_recipes)

    def get_new_category(col):
        """Get a category in col not used by any of the previous recipes"""
        col_filter = df.columns.str.startswith(f"{col}_")
        mask = df.loc[prev_inds, col_filter].sum(0).astype(bool)
        inspo_categories = list(compress(categories[col], ~mask))
        try:
            inspo_categories.remove('none')
            inspo_categories.remove('other')
        except ValueError:
            pass
        try:
            return random.choice(inspo_categories)
        except IndexError:
            return None

    inspiration = ""
    if random.random() < 0.5:
        inspiration += merge_strings(get_new_category("Cuisine"), " ")
    if random.random() < 0.7:
        inspiration += merge_strings(get_new_category("Form"), " ")
    prefix = "with " if inspiration else ""
    inspiration += merge_strings(prefix, get_new_category("Protein"), "")
    if random.random() < 0.5:
        prefix = " and " if inspiration else ""
        inspiration += merge_strings(prefix, get_new_category("Starch"))
    return inspiration


def get_dummies(df, col):
    """Gets dummy variables, allowing for multiple values with
    extra/missing whitespaces in the separators"""
    dummies_df = df[col].str.split(',').apply(
        lambda lst: [x.strip() for x in lst]
                    if isinstance(lst, list) else lst)\
                                       .str.join(',')\
                                       .str.get_dummies(',')
    col_categories = dummies_df.columns.values.tolist()
    dummies_df = dummies_df.add_prefix(f"{col}_")
    return dummies_df, col_categories


def run_app():
    """Load and process the recipes dataframe and run the appetizer app"""

    try:
        df = pd.read_excel("Weekly menu.xlsx", sheet_name="Recipes",
                           engine="openpyxl")
    except FileNotFoundError:
        dir_path = os.path.abspath('')
        print('Error: "Weekly menu.xlsx" not found. '
              f'Please download and copy it to: {dir_path}')
        sys.exit()
    df = df.dropna(axis=1, how='all')
    df['Notes'] = df['Notes'].where(pd.notnull, None)
    recipes = df['Recipe'].sort_values().values
    categories = {}

    for col in ["Meal", "Protein", "Cuisine", "Form", "Starch"]:
        dummies_df, col_categories = get_dummies(df, col)
        df = pd.concat([df, dummies_df], axis=1)
        categories[col] = col_categories


    # Define the app
    seed = random.randint(0, 2**32 - 1)

    app = Dash(__name__)
    app.title = 'Appetizer'

    @app.callback(
        Output('suggest-recipe', 'n_clicks'),
        Output('inspire-recipe', 'n_clicks'),
        Input('recipe-selection', 'value'),
        Input('meal-selection', 'value'),
        Input('servings-selection', 'value'),
        Input('restart', 'n_clicks')
    )
    def reset_clicks(*args):
        del args
        return None, None


    @app.callback(
        Output('recipe-suggestion', 'children'),
        Output('restart', 'disabled'),
        Input('suggest-recipe', 'n_clicks'),
        State('recipe-selection', 'value'),
        State('meal-selection', 'value'),
        State('servings-selection', 'value'),
    )
    def suggest_recipe(n_clicks, prev_recipes, meals, servings):
        if n_clicks is not None:
            recommendations = get_recipe_recommendations(df, prev_recipes,
                                                         meals, servings, seed)
            return (select_recommendation(df, recommendations, n_clicks - 1),
                    False)
        return "", True


    @app.callback(
        Output('recipe-inspiration', 'children'),
        Input('inspire-recipe', 'n_clicks'),
        State('recipe-selection', 'value'),
    )
    def inspire_recipe(n_clicks, prev_recipes):
        if n_clicks is not None:
            return get_recipe_inspiration(df, categories, prev_recipes)
        return ""


    app.layout = html.Div(children=[
        html.H1("Appetizer", style={'textAlign': 'center'}),
        html.Br(),
        dcc.Dropdown(recipes, multi=True,
                     placeholder='What have we eaten lately?',
                     id='recipe-selection'),
        html.Br(),
        html.Label("Meals"),
        dcc.Checklist(['breakfast', 'brunch', 'lunch', 'dinner', 'shabbat'],
                      ['lunch', 'dinner'],
                      inline=True, id='meal-selection'),
        html.Br(),
        html.Label("Servings"),
        dcc.Slider(1, 12, 1, value=4, marks=None,
                   tooltip={'placement': 'bottom', 'always_visible': False},
                   id='servings-selection'),
        html.Br(),
        html.Div([
            html.Button("Restart", id='restart', disabled=True,
                        style={'display': 'inline-block'}),
            html.Button("Suggest Recipe", id='suggest-recipe',
                        style={'display': 'inline-block',
                               'margin-left': '15px'}),
            html.Button("Inspire Recipe", id='inspire-recipe',
                        style={'display': 'inline-block',
                               'margin-left': '15px'}),
            html.Div(id='recipe-inspiration',
                     style={'display': 'inline-block', 'margin-left': '15px'}),
        ]),
        dcc.Markdown(id='recipe-suggestion', link_target="_blank"),
    ])

    app.run_server()


if __name__ == '__main__':
    run_app()
