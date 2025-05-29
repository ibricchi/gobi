use gobi_lib::recipes::*;
use gobi_lib::utils::*;

struct TemplateAction {
    name: String,
    subname: String,
    priority: bool,
}

impl TemplateAction {
    fn new() -> Self {
        todo!()
    }
}

impl IAction for TemplateAction {
    fn get_name(&self) -> &str {
        &self.name
    }

    fn get_subname(&self) -> &str {
        &self.subname
    }

    fn get_help(&self) -> &str {
        todo!()
    }

    fn run(&self, _actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()> {
        todo!()
    }
}

struct TemplateRecipe {}

impl TemplateRecipe {
    fn new() -> TemplateRecipe {
        TemplateRecipe {}
    }
}

impl IRecipe for TemplateRecipe {
    fn get_name(&self) -> &str {
        todo!()
    }

    fn get_help(&self) -> &str {
        todo!()
    }

    fn create_actions(
        &self,
        _recipe_manager: &SharedRecipeManager,
        _gobi_file: &GobiFile,
    ) -> GobiResult<Vec<Action>> {
        todo!()
    }
}

pub fn register_recipes(recipe_manager: &mut RecipeManager) {
    recipe_manager.register_recipe(RecipeWrapper::new(TemplateRecipe::new()));
}
