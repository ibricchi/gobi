use gobi_lib::{file::GobiFile, recipes::*, GobiError, GobiResult};

pub struct HelpAction {
    recipe_manager: SharedRecipeManager,
}

impl HelpAction {
    fn new(recipe_manager: &SharedRecipeManager) -> Self {
        Self {
            recipe_manager: recipe_manager.clone(),
        }
    }
}

impl IAction for HelpAction {
    fn get_name(&self) -> &str {
        "help"
    }

    fn get_subname(&self) -> &str {
        "help"
    }

    fn get_help(&self) -> &str {
        "
Usage: gobi <project list...>? help [mode]? [<action_name>+]?

mode can be 'recipe' or 'action', if ommited will default to 'action'

With no arguments, will print the help menu for all actions/recipes, otherwise only prints the help for the specified action/recipe
"
    }

    fn run(&self, actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()> {
        enum Mode {
            Action,
            Recipe,
        }

        let mut args = args.iter().peekable();

        let mode = match args.peek() {
            None => Mode::Action,
            Some(mode) => match mode.as_str() {
                "recipe" => {
                    args.next();
                    Mode::Recipe
                }
                "action" => {
                    args.next();
                    Mode::Action
                }
                _ => Mode::Action,
            },
        };

        let names: &mut dyn Iterator<Item = String> = if args.len() == 0 {
            &mut actions.iter().map(|a| a.get_name().into())
        } else {
            &mut args.map(|a| a.clone())
        };
        let messages: &mut dyn Iterator<Item = GobiResult<String>> = match mode {
            Mode::Recipe => &mut names.map(|rname| -> GobiResult<String> {
                let recipe = match self.recipe_manager.get_recipe(&rname) {
                    None => {
                        return Err(GobiError {
                            code: 1,
                            msg: format!("Recipe '{}' not found", rname),
                        })
                    }
                    Some(r) => r,
                };
                Ok(format!(
                    "{}\n# {} #\n{}\n{}",
                    "#".repeat(recipe.get_name().len() + 4),
                    recipe.get_name(),
                    "#".repeat(recipe.get_name().len() + 4),
                    recipe.get_help().trim()
                ))
            }),
            Mode::Action => &mut names.map(|aname| -> GobiResult<String> {
                let action = find_action(&aname, actions)?;
                let name = action.get_name();
                Ok(format!(
                    "{}\n# {} #\n{}\n{}",
                    "#".repeat(name.len() + 4),
                    action.get_name(),
                    "#".repeat(name.len() + 4),
                    action.get_help().trim()
                ))
            }),
        };

        let (err, help) = messages.fold(
            (
                GobiError {
                    code: 0,
                    msg: String::new(),
                },
                String::new(),
            ),
            |(acce, acch), m| match m {
                Err(e) => (acce.merge(e), acch),
                Ok(h) => (acce, format!("{}\n\n{}", acch, h)),
            },
        );

        if err.code != 0 {
            return Err(err.clone());
        }

        println!("{}", help.trim());
        Ok(())
    }
}

struct HelpRecipe {}

impl HelpRecipe {
    fn new() -> HelpRecipe {
        HelpRecipe {}
    }
}

impl IRecipe for HelpRecipe {
    fn get_name(&self) -> &str {
        "help"
    }

    fn get_help(&self) -> &str {
        "Generates the help action for gobi."
    }

    fn create_actions(
        &self,
        recipe_manager: &SharedRecipeManager,
        _gobi_file: &GobiFile,
    ) -> GobiResult<Vec<Action>> {
        return Ok(vec![ActionWrapper::new(HelpAction::new(recipe_manager))]);
    }
}

pub fn register_recipes(recipe_manager: &mut RecipeManager) {
    recipe_manager.register_recipe(RecipeWrapper::new(HelpRecipe::new()));
}
