use gobi_lib::{file::GobiFile, recipes::*, GobiError, GobiResult};

pub struct ListAction {}

impl ListAction {
    pub fn print_list(actions: &Vec<Action>, full: bool) {
        let mut actions: Vec<Action> = actions.clone();
        if full {
            actions.sort_by(|a, b| a.get_name().cmp(b.get_name()));
            actions.iter().for_each(|action| {
                println!("{}", action.get_name());
            });
        } else {
            get_minimal_names(&actions).iter().for_each(|(_, name)| {
                println!("{}", name);
            });
        }
    }
}

impl IAction for ListAction {
    fn get_name(&self) -> &str {
        "list"
    }

    fn get_subname(&self) -> &str {
        "list"
    }

    fn get_help(&self) -> &str {
        "Get a list of all available actions for a project
Usage: gobi <project list...>? list [porcelain|full]

By default will try and display the subname of available actions unless a conflict exists, then will use the full name.
Porcelain will not print out the message at the start of the list command.
Full will print out the full name of all actions."
    }

    fn run(&self, actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()> {
        if args.len() == 0 {
            println!("Available actions:");
            ListAction::print_list(actions, false);
        } else if args.len() == 1 {
            match args[0].as_str() {
                "porcelain" => ListAction::print_list(actions, false),
                "full" => ListAction::print_list(actions, true),
                _ => {
                    return Err(GobiError {
                        code: 1,
                        msg: format!("Unknown argument: {}", args[0]),
                    });
                }
            }
        } else {
            return Err(GobiError {
                code: 1,
                msg: "Too many arguments passed to list action".to_string(),
            });
        }
        return Ok(());
    }
}

struct ListRecipe {}

impl ListRecipe {
    fn new() -> ListRecipe {
        ListRecipe {}
    }
}

impl IRecipe for ListRecipe {
    fn get_name(&self) -> &str {
        "list"
    }

    fn get_help(&self) -> &str {
        "Generates a list of all available actions"
    }

    fn create_actions(
        &self,
        _recipe_manager: &SharedRecipeManager,
        _gobi_file: &GobiFile,
    ) -> GobiResult<Vec<Action>> {
        return Ok(vec![ActionWrapper::new(ListAction {})]);
    }
}

pub fn register_recipes(recipe_manager: &mut RecipeManager) {
    recipe_manager.register_recipe(RecipeWrapper::new(ListRecipe::new()));
}
