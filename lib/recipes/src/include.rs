use handlebars::Handlebars;
use serde::Deserialize;
use std::collections::HashMap;
use std::io::Read;
use std::io::Write;
use std::path::PathBuf;
use tempfile::Builder;

use gobi_lib::{
    file::{GobiFile, GobiFileEntryTrait, GobiFileTrait},
    recipes::*,
    GobiError, GobiResult,
};

#[derive(Deserialize)]
struct IncludeConfig {
    path: String,
    #[serde(default)]
    env: HashMap<String, String>,
}

struct IncludeAction {
    name: String,
    subaction: Action,
}

impl IncludeAction {
    fn new(name: &str, action: Action) -> Self {
        Self {
            name: format!("{}.{}", name, action.get_name()),
            subaction: action,
        }
    }
}

impl IAction for IncludeAction {
    fn get_name(&self) -> &str {
        &self.name
    }

    fn get_subname(&self) -> &str {
        self.subaction.get_subname()
    }

    fn get_help(&self) -> &str {
        self.subaction.get_help()
    }

    fn has_priority(&self) -> bool {
        false
    }

    fn run(&self, actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()> {
        self.subaction.run(actions, args)
    }
}

struct IncludeRecipe {}

impl IncludeRecipe {
    fn new() -> IncludeRecipe {
        IncludeRecipe {}
    }
}

impl IRecipe for IncludeRecipe {
    fn get_name(&self) -> &str {
        "include"
    }

    fn get_help(&self) -> &str {
        r#"
This recipe is used to include a file and provide environments to override parts of it.

To use this just specify as many includes of the following format:

[include.<name>]
path = "/path/to/include.toml"
[include.<name>.env]]
key = "value"
key2 = 3

Name will be prepended to all included action to allow for disambiguating them.

Note! included actions will be considered lower priority than ones defined in the file, so the full name will be needed for an imported action if it's subname appears in the current file.
"#
    }

    fn create_actions(
        &self,
        recipe_manager: &SharedRecipeManager,
        gobi_file: &GobiFile,
    ) -> GobiResult<Vec<Action>> {
        let config = match gobi_file.get_data().get("include") {
            Some(config) if config.is_table() => config,
            _ => return Ok(vec![]),
        };

        let handlebars = Handlebars::new();

        let (err, actions) = config
            .get_table()
            .unwrap()
            .into_iter()
            .map(
                |(name, config)| match config.deserialize::<IncludeConfig>() {
                    Ok(config) => {
                        let path = if config.path.starts_with("/") {
                            PathBuf::from(config.path)
                        } else {
                            gobi_file.path().parent().unwrap().join(&config.path)
                        };
                        if !path.is_file() {
                            return Err(GobiError {
                                code: 1,
                                msg: format!(
                                    "Invalid path for include: '{}', '{}'",
                                    name,
                                    path.display()
                                ),
                            });
                        }

                        let mut file = std::fs::File::open(path).unwrap();
                        let mut contents = String::new();
                        file.read_to_string(&mut contents).unwrap();

                        let contents = handlebars.render_template(&contents, &config.env).unwrap();

                        let mut tmp_file = Builder::new()
                            .prefix("gobi")
                            .suffix(".toml")
                            .tempfile()
                            .unwrap();

                        tmp_file.write(contents.as_bytes()).unwrap();

                        let included_gobi_file = GobiFile::from_path(tmp_file.path())?;

                        Ok(recipe_manager
                            .create_actions(&recipe_manager, &included_gobi_file)?
                            .into_iter()
                            .map(move |action| {
                                ActionWrapper::new(IncludeAction::new(&name, action)) as Action
                            }))
                    }
                    _ => Err(GobiError {
                        code: 1,
                        msg: format!("Invalid include config for action '{}'", name),
                    }),
                },
            )
            .fold(
                (GobiError::default(), Vec::new()),
                |(err, mut actions), action| match action {
                    Ok(action) => {
                        actions.extend(action);
                        (err, actions)
                    }
                    Err(nerr) => (err.merge(nerr), actions),
                },
            );

        if err.code != 0 {
            return Err(err);
        }

        Ok(actions)
    }
}

pub fn register_recipes(recipe_manager: &mut RecipeManager) {
    recipe_manager.register_recipe(RecipeWrapper::new(IncludeRecipe::new()));
}
