# appetizer

Bored of eating the same meals week after week? Appetizer sparks your creativity by suggesting recipes as different as possible from what you've had recently. Appetizer draws from your personal recipes to recommend old favorites as well as inspire new combinations.

## Installation and Use
First, download and install conda. This can be done by installing [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

To download and set up appetizer, run in a terminal:
```
git clone https://github.com/aribrill/appetizer.git
cd appetizer
conda env create -f environment.yml
chmod +x appetizer.sh
```

To run appetizer, run in a terminal:
```
./appetizer.sh
```

Appetizer is built to use my personal spreadsheet of favorite recipes. If you're me, place that spreadsheet in the `appetizer` directory before running the app. Otherwise, create one named `Weekly Menu.xslx` containing a sheet `Recipes` that has the following structure:

| Recipe | Protein | Starch | Cuisine | Form | Meal | Min Servings | Max Servings | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Breakfast burritos | eggs, beans | tortillas | Mexican | | brunch, lunch, dinner | 2 | 6 | |
| Corn chickpea bowl | chickpeas | corn | | salad | lunch | 4 | 4 | Link: https://www.bonappetit.com/recipe/corn-and-chickpea-bowl-with-miso-jalapeno-tahini |
| Pasta e fagioli | beans | pasta | Italian | soup/stew | lunch, dinner | 4 | 4 | Link: https://www.seriouseats.com/30-minute-pasta-and-kidney-bean-soup-pasta-e-fagioli-recipe |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

![Screenshot](screenshot.png)
