use serde::Deserialize;
use std::cell::OnceCell;

use gobi_lib::{
    file::{GobiFile, GobiFileEntryTrait, GobiFileTrait},
    recipes::*,
    GobiError, GobiResult,
};

#[derive(Deserialize)]
struct SequenceConfig {
    subactions: Vec<String>,
    #[serde(default)]
    #[serde(rename = "allow-fail")]
    allow_fail: bool,
    #[serde(default)]
    decorate: bool,
}

struct SequenceAction {
    name: String,
    subname: String,

    config: SequenceConfig,
    help: OnceCell<String>,
}

impl SequenceAction {
    fn new(name: &str, config: SequenceConfig) -> Self {
        SequenceAction {
            name: format!("sequence.{}", name),
            subname: name.to_string(),
            config,
            help: OnceCell::new(),
        }
    }
}

impl IAction for SequenceAction {
    fn get_name(&self) -> &str {
        &self.name
    }

    fn get_subname(&self) -> &str {
        &self.subname
    }

    fn get_help(&self) -> &str {
        self.help.get_or_init(|| {
            format!(
                "Runs {:?} in a sequence {}",
                self.config.subactions,
                if self.config.allow_fail {
                    "allowing failures"
                } else {
                    "exiting on failures"
                }
            )
        })
    }

    fn run(&self, actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()> {
        let actions_to_run = self
            .config
            .subactions
            .iter()
            .map(|name| find_action(name, actions));

        let (err, actions_to_run) = actions_to_run.fold(
            (GobiError::default(), Vec::new()),
            |(err, mut actions), action| match action {
                Ok(action) => {
                    actions.push(action);
                    (err, actions)
                }
                Err(nerr) => (err.merge(nerr), actions),
            },
        );

        if err.code != 0 {
            return Err(err);
        }

        let err = actions_to_run
            .into_iter()
            .try_fold(GobiError::default(), |err, action| {
                if self.config.decorate {
                    let name = action.get_name();
                    println!("{0}\n# {1} #\n{0}", "#".repeat(name.len() + 4), name);
                }
                match action.run(actions, args.clone()) {
                    Ok(_) => Ok(err),
                    Err(nerr) if self.config.allow_fail => Ok(err.merge(nerr)),
                    Err(nerr) => Err(nerr),
                }
            });

        match err {
            Ok(err) if err.code == 0 => Ok(()),
            Ok(err) => Err(GobiError {
                code: err.code,
                msg: format!("Sequence finished with errors: "),
            }
            .merge(err)),
            Err(err) => Err(GobiError {
                code: err.code,
                msg: format!("Sequence failed: "),
            }
            .merge(err)),
        }
    }
}

struct SequenceRecipe {}

impl SequenceRecipe {
    fn new() -> SequenceRecipe {
        SequenceRecipe {}
    }
}

impl IRecipe for SequenceRecipe {
    fn get_name(&self) -> &str {
        "sequence"
    }

    fn get_help(&self) -> &str {
        "
Generates sequence actions.

This recipe uses the following configuration options:

[sequence.<action name>.subactions] (required) : list[str]
    list of actions to run in order

[sequence.<action name>.allow-fail] (optional) : bool (default: false)
    if true, continue running actions even if one fails

[sequence.<action name>.decorate] (optional) : bool (default: false)
    if true, prints the name of each subaction before running it
"
    }

    fn create_actions(
        &self,
        _recipe_manager: &SharedRecipeManager,
        gobi_file: &GobiFile,
    ) -> GobiResult<Vec<Action>> {
        let config = match gobi_file.get_data().get("sequence") {
            Some(config) if config.is_table() => config.get_table().unwrap(),
            _ => return Ok(vec![]),
        };

        let (err, actions) = config
            .into_iter()
            .map(
                |(name, config)| match config.deserialize::<SequenceConfig>() {
                    Ok(config) => {
                        Ok(ActionWrapper::new(SequenceAction::new(&name, config)) as Action)
                    }
                    _ => Err(GobiError {
                        code: 1,
                        msg: format!("Invalid sequence config for action '{}'", name),
                    }),
                },
            )
            .fold(
                (GobiError::default(), Vec::new()),
                |(err, mut actions), action| match action {
                    Ok(action) => {
                        actions.push(action);
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
    recipe_manager.register_recipe(RecipeWrapper::new(SequenceRecipe::new()));
}
