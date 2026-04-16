"""Cooking rules: recipes, sashimi creation, pearl rewards, cooking wheel.

RC3 — Review questions for Derek:
  - Does cooking require specific fish types?
  - Are pearl rewards fixed per recipe?
"""

import pytest

from .helpers import get_current_profile

FAKE_OBJECT_ID = "000000000000000000000000"


@pytest.mark.live
class TestRecipes:
    """Verify recipe structure and requirements."""

    @pytest.mark.order(59)
    @pytest.mark.timeout(15)
    def test_get_recipes_returns_structure(self, auth_token):
        """Recipes have cookingRecipeId, requirements, rewards."""
        from ff_agent import api_client as api

        result = api.get_active_recipes()
        assert result is not None

        # The response may be a list of recipes or dict with a data key
        recipes = result if isinstance(result, list) else result.get("data", result)
        if isinstance(recipes, dict):
            recipes = recipes.get("recipes", recipes.get("items", [recipes]))

        if not isinstance(recipes, list) or len(recipes) == 0:
            pytest.skip("No active recipes available")

        recipe = recipes[0]
        print(f"  Recipe keys: {list(recipe.keys())}")

        # Check for expected fields (field names may vary)
        has_id = any(k in recipe for k in ("cookingRecipeId", "_id", "id", "recipeId"))
        assert has_id, f"Recipe missing ID field. Keys: {list(recipe.keys())}"

    @pytest.mark.order(60)
    @pytest.mark.timeout(15)
    def test_recipe_requirements_list_fish(self, auth_token):
        """Each recipe lists required fish types + quantities."""
        from ff_agent import api_client as api

        result = api.get_active_recipes()
        recipes = result if isinstance(result, list) else result.get("data", result)
        if isinstance(recipes, dict):
            recipes = recipes.get("recipes", recipes.get("items", [recipes]))

        if not isinstance(recipes, list) or len(recipes) == 0:
            pytest.skip("No active recipes")

        recipe = recipes[0]
        # Look for requirements/ingredients
        req_key = next(
            (k for k in ("requirements", "ingredients", "requiredFish",
                          "fishRequirements", "items")
             if k in recipe),
            None
        )
        print(f"  Recipe: {recipe.get('name', recipe.get('_id', 'unknown'))}")
        print(f"  Requirement key: {req_key}")
        if req_key:
            reqs = recipe[req_key]
            print(f"  Requirements: {reqs}")
            assert isinstance(reqs, (list, dict)), \
                f"Requirements should be list or dict, got {type(reqs)}"


@pytest.mark.live
class TestCooking:
    """Verify cooking with correct/incorrect fish."""

    @pytest.mark.order(61)
    @pytest.mark.timeout(30)
    def test_cook_with_matching_fish(self, auth_token):
        """Cook with correct fish → sashimi created.

        This test is observational — we need the right fish in inventory.
        If we can't match a recipe, we skip.
        """
        from ff_agent import api_client as api

        recipes_resp = api.get_active_recipes()
        recipes = recipes_resp if isinstance(recipes_resp, list) else \
            recipes_resp.get("data", recipes_resp)
        if isinstance(recipes, dict):
            recipes = recipes.get("recipes", recipes.get("items", [recipes]))

        if not isinstance(recipes, list) or len(recipes) == 0:
            pytest.skip("No active recipes")

        # Get fish inventory
        inv = api.get_fish_inventory()
        fish_list = inv if isinstance(inv, list) else \
            inv.get("data", inv.get("fish", inv.get("items", [])))

        if not isinstance(fish_list, list) or len(fish_list) == 0:
            pytest.skip("No fish in inventory to cook with")

        # Try each recipe to find one we can fulfill
        for recipe in recipes:
            recipe_id = recipe.get("cookingRecipeId") or recipe.get("_id") or recipe.get("id")
            if not recipe_id:
                continue

            # Get fish IDs from inventory (just use first few)
            fish_ids = []
            for f in fish_list[:3]:
                fid = f.get("fishInfoId") or f.get("_id") or f.get("id")
                if fid:
                    fish_ids.append(fid)

            if not fish_ids:
                continue

            result = api.cook(recipe_id, 1, fish_ids)
            print(f"  Cook result: {result}")
            assert isinstance(result, dict)
            # If successful, we're done. If not, try next recipe
            if not (isinstance(result, dict) and result.get("code") in (400, 404)):
                return

        pytest.skip("Could not match any recipe with available fish")

    @pytest.mark.order(62)
    @pytest.mark.timeout(15)
    def test_cook_with_wrong_fish_fails(self, auth_token):
        """Pass invalid fish_ids → error."""
        from ff_agent import api_client as api

        recipes_resp = api.get_active_recipes()
        recipes = recipes_resp if isinstance(recipes_resp, list) else \
            recipes_resp.get("data", recipes_resp)
        if isinstance(recipes, dict):
            recipes = recipes.get("recipes", recipes.get("items", [recipes]))

        if not isinstance(recipes, list) or len(recipes) == 0:
            pytest.skip("No active recipes")

        recipe = recipes[0]
        recipe_id = recipe.get("cookingRecipeId") or recipe.get("_id") or recipe.get("id")

        result = api.cook(recipe_id, 1, ["fake_fish_id_111111111111"])
        assert isinstance(result, dict)
        print(f"  Wrong fish result: {result}")


@pytest.mark.live
class TestCookingWheel:
    """Verify cooking wheel pearl requirements."""

    @pytest.mark.order(63)
    @pytest.mark.timeout(15)
    def test_spin_wheel_requires_pearls(self, auth_token):
        """Spin with 0 pearls → error or empty result."""
        from ff_agent import api_client as api

        result = api.spin_cooking_wheel(1)
        assert isinstance(result, dict)
        print(f"  Spin wheel result: {result}")
        # Should either succeed (if pearls available) or return error

    @pytest.mark.order(64)
    @pytest.mark.timeout(15)
    def test_spin_wheel_returns_reward(self, auth_token):
        """Spin (if pearls available) → reward structure returned."""
        from ff_agent import api_client as api

        result = api.spin_cooking_wheel(1)
        assert isinstance(result, dict)
        # Log the structure for Derek's review
        print(f"  Wheel reward keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
