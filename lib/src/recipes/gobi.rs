use std::cell::OnceCell;
use std::env;
use std::path::PathBuf;

use crate::{
    file::{GobiFileEntryTrait, GobiFileTrait},
    recipes::*,
};

pub struct GobiAction {
    name: String,
    subname: String,
    priority: bool,
    recipe_manager: SharedRecipeManager,

    path: PathBuf,
    help_msg: OnceCell<String>,
}

impl GobiAction {
    pub fn new<P: Into<PathBuf>>(
        name: &str,
        file_path: P,
        recipe_manager: &SharedRecipeManager,
    ) -> Action {
        let name = if name == "" { "gobi" } else { name };
        let subname = if name == "" { "gobi" } else { name };
        // run_once(help_msg_fn);
        ActionWrapper::new(GobiAction {
            name: name.to_string(),
            subname: subname.to_string(),
            recipe_manager: recipe_manager.clone(),
            priority: false,
            path: file_path.into(),
            help_msg: OnceCell::new(),
        })
    }

    fn set_env(&self, action: &Action) {
        env::set_var("GOBI_FILE", self.path.to_string_lossy().to_string());
        env::set_var(
            "GOBI_DIR",
            self.path.parent().unwrap().to_string_lossy().to_string(),
        );
        env::set_var("GOBI_ACTION", action.get_subname().to_string());
        env::set_var("GOBI_ACTION_FULL", action.get_name().to_string());
        env::set_var("GOBI_PROJECT", &self.subname);
        if self.name == "gobi" {
            env::remove_var("GOBI_PROJECT_LIST");
        } else {
            match env::var("GOBI_PROJECT_LIST") {
                Ok(project_list) => {
                    env::set_var(
                        "GOBI_PROJECT_LIST",
                        format!("{};{}", project_list, self.subname),
                    );
                }
                Err(_) => {
                    env::set_var("GOBI_PROJECT_LIST", self.subname.clone());
                }
            }
        }
    }
}

impl IAction for GobiAction {
    fn get_name(&self) -> &str {
        &self.name
    }

    fn get_subname(&self) -> &str {
        &self.subname
    }

    fn has_priority(&self) -> bool {
        self.priority
    }

    fn get_help(&self) -> &str {
        self.help_msg
            .get_or_init(|| match GobiFile::from_path(&self.path) {
                Ok(gobi_file) => match gobi_file.get_data().get_nested(&["gobi", "help"]) {
                    Some(help) if help.is_string() => format!("{}", help.get_string().unwrap()),
                    _ => format!("Project '{}' has no help", self.subname.to_string()),
                },
                Err(e) => format!("Error loading gobi file: {}", e.msg),
            })
    }

    fn run(&self, _actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()> {
        let gobi_file = match GobiFile::from_path(&self.path) {
            Ok(gobi_file) => gobi_file,
            Err(e) => {
                return Err(GobiError {
                    code: 1,
                    msg: format!("Error loading gobi file: {}", e.msg),
                });
            }
        };

        let actions = self
            .recipe_manager
            .create_actions(&self.recipe_manager, &gobi_file)?;

        if args.len() == 0 {
            return Err(GobiError {
                code: 1,
                msg: format!("No action specified"),
            });
        }

        let action = find_action(&args[0], &actions)?;
        self.set_env(&action);
        let args: Vec<String> = args.iter().skip(1).map(|arg| arg.to_string()).collect();

        return action.run(&actions, args);
    }

    fn completion(&self, _actions: &Vec<Action>, args: Vec<String>) -> GobiResult<Vec<String>> {
        let gobi_file = match GobiFile::from_path(&self.path) {
            Ok(gobi_file) => gobi_file,
            Err(e) => {
                return Err(GobiError {
                    code: 1,
                    msg: format!("Error loading gobi file: {}", e.msg),
                });
            }
        };

        let actions = self
            .recipe_manager
            .create_actions(&self.recipe_manager, &gobi_file)?;

        if args.len() == 0 {
            get_minimal_names(&actions)
                .into_iter()
                .map(|(_, name)| Ok(name.to_string()))
                .collect()
        } else {
            let action = find_action(&args[0], &actions)?;
            self.set_env(&action);
            action.completion(&actions, args.iter().skip(1).cloned().collect())
        }
    }
}

struct GobiRecipe {}

impl GobiRecipe {
    fn new() -> GobiRecipe {
        GobiRecipe {}
    }
}

impl IRecipe for GobiRecipe {
    fn get_name(&self) -> &str {
        "gobi"
    }

    fn get_help(&self) -> &str {
        "
This recipe is automatically loaded by gobi, and is used to load and process gobi files. It is responsible for loading and calling all other recipes, and for triggering actions.

This recipe uses the following configuration options:

[gobi.recipes] : list[str]
    list of child recipes to load

[gobi.child-recipes] : list[str]
    list of child recipes to load, that are not loaded by default

[gobi.help] : str
    help menu entry for the action created for a file

[gobi.projects] : dict[str, str]:
    dictionary of project names to paths, used to create actions for gobi files
"
    }

    fn create_actions(
        &self,
        recipe_manager: &SharedRecipeManager,
        gobi_file: &GobiFile,
    ) -> GobiResult<Vec<Action>> {
        let config = match gobi_file.get_data().get("gobi") {
            Some(config) => config,
            None => return Ok(vec![]),
        };

        Ok(config.get("projects").map_or(vec![], |projects| {
            projects.get_table().map_or(vec![], |projects| {
                projects
                    .iter()
                    .filter_map(|(name, path)| {
                        path.get_string()
                            .map(|path| GobiAction::new(name, path, recipe_manager))
                    })
                    .collect()
            })
        }))
    }
}

pub fn register_recipes(recipe_manager: &mut RecipeManager) {
    recipe_manager.register_recipe(RecipeWrapper::new(GobiRecipe::new()));
}
