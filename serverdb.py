from jinja2 import StrictUndefined

from flask import Flask, render_template, request, redirect, session, jsonify, flash

from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, Diet, Ingredient, Recipe, RecipeIngredient

import re

import os

import json

from send_sms import send_sms

# import querydb  # Need to comment this line out if running querydb.py in interactive python.

# import spoonacular

app = Flask(__name__)

app.secret_key = os.environ["APP_SECRET_KEY"]

app.jinja_env.undefined = StrictUndefined  # Raises an error if error made in Jinja2.


@app.route("/")
def index():
    """Return Homepage."""

    return render_template("homepagedb.html")


@app.route("/search-results")
def results():
    """Return search results for user's input ingredients."""

    # Get the ingredient(s) inputted by the user and pass as one
    # of the arguments in the query_recipes_by_diet.
    ingredients = request.args.get("ingredient")

    # Split the ingredient(s) into a list.
    ingredients = ingredients.split(' ')

    # Get the user indicated diet to pass as an argument into query_recipes_by_diet.
    diet = request.args.get("diet")

    # Query for recipes in the database that meet user indicated diet and any of the input ingredients.
    recipes = Recipe.query.filter(Recipe.diets.any(
                                Diet.name == diet)).filter(
                                Recipe.ingredients.any(
                                Ingredient.name.in_(ingredients))).all()

    return render_template("search_resultsdb.html", recipes=recipes, ingredients=ingredients)


@app.route("/recipe/<int:recipe_id>")
def show_recipe(recipe_id):
    """Return recipe that user clicks on from /search_results."""

    recipe = Recipe.query.filter_by(recipe_id=recipe_id).one()

    instructions = recipe.instructions

    # Remove HTML tags from instructions with regex. Expression means to match strings 
    # that start with < that don't match characters in the following set [^>]. 
    # * means to match 0 or more of the preceding token. The last character of the string being >.
    # Source: http://stackoverflow.com/questions/3662142/how-to-remove-tags-from-a-string-in-python-using-regular-expressions-not-in-ht
    instructions = re.sub('<[^>]*>', '', instructions)

    # Perform this query to get the measurements, ingredients, and ingredient ids.
    # Display measurements and ingredients to user.
    measurements_ingredients = db.session.query(RecipeIngredient.measurement,
                                                Ingredient.ingredient_id,
                                                Ingredient.name).join(Recipe).join(Ingredient).filter(
                                                Recipe.recipe_id == recipe_id).all()

    shopping_list = session.keys()

    return render_template("recipe.html", recipe=recipe, instructions=instructions,
                            measurements_ingredients=measurements_ingredients, 
                            shopping_list=json.dumps(shopping_list))  # Use shopping_list as an object in html and js.


@app.route("/shopping-list")
def show_shopping_list():
    """Show user's shopping list."""

    # List of ingredient ids in shopping list.
    ingredient_ids = session["shopping_list"]

    ingredients = []

    # Get the ingredient names for the ingredients in the shopping_list.
    for ingredient_id in ingredient_ids:
        ingredient = db.session.query(Ingredient.ingredient_id,
                                        Ingredient.name).filter_by(
                                        ingredient_id=ingredient_id).one()
        ingredients.append(ingredient)

    return render_template("shopping_list.html", shopping_list=ingredients)


@app.route("/shopping-list", methods=["POST"])
def add_to_shopping_list():
    """Add ingredients to shopping_list session."""

    # Get the ingredient_id clicked by the user sent by AJAX.
    ingredient_id = request.form.get("ingredient_id")

    # Convert unicode to int.
    ingredient_id = int(ingredient_id)

    if "shopping_list" in session:
        shopping_list = session["shopping_list"]
    else:
        shopping_list = session["shopping_list"] = []

    # Only append ingredients not currently in the shopping_list.
    if ingredient_id not in shopping_list:
        shopping_list.append(ingredient_id)
    else:
        flash("Ingredient already in list!")  # Need to debug flash. 
    
    # print "DEBUG:", session["shopping_list"]  # For debugging.

    # import pdb; pdb.set_trace()

    # session.clear() 

    return "Success"  # What can I return here?
    

@app.route("/remove-from-shopping-list", methods=["POST"])
def remove_ingredient():
    """Remove ingredients from shopping list session.

    User will never visit this route.
    """

    ingredient = request.form.get("ingredient_id")
    
    # Convert unicode to int.
    ingredient = int(ingredient)

    # Remove the ingredient deleted from the shopping list view from the session.
    session["shopping_list"].remove(ingredient)

    return "Success"  # What can I return here?


### This route needs to be fixed. 
@app.route("/send-sms")
def send_sms_shopping_list():

    shopping_list = session["shopping_list"]

    ingredients = []

    # Get the ingredient names for the ingredients in the shopping_list.
    for ingredient_id in shopping_list:
        ingredient = db.session.query(Ingredient.name ).filter_by(ingredient_id=ingredient_id).one()
        ingredients.append(str(ingredient[0]))  # ingredient is a tuple so get the first index and convert unicode to string.

    # import pdb; pdb.set_trace()
    if len(ingredients) > 1:
        ingredients = ", ".join(ingredients)
        # print "MORE THAN ONE: ", ingredients
    else:
        ingredients = "".join(ingredients)
        # print "LESS THAN ONE: ", ingredients

    # print ingredients

    sender = request.args.get("sender_number")
    print "SENDER:", sender
    recipient = request.args.get("recipient_number")
    print "RECIPIENT:", recipient

    #### If user hits submit, then call send_sms.
    # send_sms(ingredients)  # Will send a text message with the shopping list.


    return render_template("send_sms.html")


# # @app.route("/favorites")  # Route needs to be revised.
# # def show_saved_recipes():
# #     """Show user's bookmarked recipes."""

# #     saved_recipes = session["save_recipe"]
# #     print "DEBUG:", saved_recipes

# #     return render_template("savedrecipes.html", saved_recipe=saved_recipe)



# @app.route("/favorites", methods=["POST"])  # Route needs to be revised.
# def add_recipes():
#     """Save recipe to favorites."""

#     recipe_title = request.form.get("save_recipe")

#     print session

#     # print "DEBUG", recipe_title



#     session.setdefault("save_recipe", []).append(recipe_title)
#     # import pdb; pdb.set_trace()


#     saved = session["save_recipe"]

#     print "FAVORITES: ", saved  # For debugging.

#     session.clear()

#     print session
#     return "Sucess"


@app.route("/login")  # Route needs to be revised.
def show_profile():
    """Show user's profile that displays user's info, shopping lists, and bookmarks."""

    pass

@app.route("/logout")  # Route needs to be revised.
def show_logout():
    """Show user's profile that displays user's info, shopping lists, and bookmarks."""

    pass


@app.route("/profile")  # Route needs to be revised.
def show_user_profile():
    """Show user's profile that displays user's info, shopping lists, and bookmarks."""

    pass











if __name__ == "__main__":  # Makes sure the server only runs if the script is executed directly from the Python interpreter and not used as an imported module.
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()
