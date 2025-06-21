use serde::Deserialize;
use std::env;
use std::{cell::OnceCell, collections::HashMap};

use gobi_lib::{
    file::{GobiFile, GobiFileEntryTrait, GobiFileTrait},
    recipes::*,
    GobiError, GobiResult,
};

fn extract(
    item: (clap::error::ContextKind, &clap::error::ContextValue),
) -> Option<&clap::error::ContextValue> {
    let (k, v) = item;
    if k == clap::error::ContextKind::InvalidArg {
        return Some(v);
    }
    None
}

fn parse_known_args(
    cmd: &clap::Command,
    mut args: Vec<String>,
) -> Result<(clap::ArgMatches, Vec<String>), clap::Error> {
    let mut rem: Vec<String> = vec![];
    loop {
        match cmd.clone().try_get_matches_from(&args) {
            Ok(matches) => {
                return Ok((matches, rem));
            }
            Err(error) => match error.kind() {
                clap::error::ErrorKind::UnknownArgument => {
                    let items = error.context().find_map(extract);
                    match items {
                        Some(x) => match x {
                            clap::error::ContextValue::String(s) => {
                                rem.push(s.to_owned());
                                args.retain(|a| a != s);
                            }
                            _ => {
                                return Err(error);
                            }
                        },
                        None => {
                            return Err(error);
                        }
                    }
                }
                _ => {
                    return Err(error);
                }
            },
        }
    }
}

#[derive(Deserialize)]
struct ArgparseFlag {
    #[serde(default)]
    short: Option<char>,
    #[serde(default)]
    long: Option<String>,
    #[serde(default)]
    help: Option<String>,
    #[serde(default)]
    set_false: bool,
    #[serde(default)]
    var_name: Option<String>,
}

#[derive(Deserialize)]
struct ArgparseArg {
    #[serde(default)]
    short: Option<char>,
    #[serde(default)]
    long: Option<String>,
    #[serde(default)]
    help: Option<String>,
    #[serde(default)]
    default: Option<String>,
    #[serde(default)]
    required: bool,
    #[serde(default)]
    var_name: Option<String>,
    #[serde(default)]
    choices: Option<Vec<String>>,
}

#[derive(Deserialize)]
struct ArgparseConfig {
    action: String,
    #[serde(default)]
    flags: HashMap<String, ArgparseFlag>,
    #[serde(default)]
    args: HashMap<String, ArgparseArg>,
    #[serde(default)]
    passthrough: bool,
}

struct ArgparseAction {
    name: String,
    subname: String,

    config: ArgparseConfig,
    parser: OnceCell<(clap::Command, String)>,
    help: OnceCell<String>,
}

impl ArgparseAction {
    fn new(name: &str, config: ArgparseConfig) -> Self {
        ArgparseAction {
            name: format!("argparse.{}", name),
            subname: name.to_string(),
            config,
            parser: OnceCell::new(),
            help: OnceCell::new(),
        }
    }

    fn get_parser_and_help(&self) -> &(clap::Command, String) {
        self.parser.get_or_init(|| {
            let mut command = clap::Command::new(self.name.clone()).no_binary_name(true);
            for (name, flag) in &self.config.flags {
                let mut arg =
                    clap::Arg::new(name.clone()).long(flag.long.clone().unwrap_or(name.clone()));
                if let Some(short) = flag.short {
                    arg = arg.short(short);
                }
                if let Some(help) = &flag.help {
                    arg = arg.help(help);
                }
                if flag.set_false {
                    arg = arg.action(clap::ArgAction::SetFalse);
                } else {
                    arg = arg.action(clap::ArgAction::SetTrue);
                }
                command = command.arg(arg);
            }
            for (name, arg) in &self.config.args {
                let mut clap_arg =
                    clap::Arg::new(name.clone()).long(arg.long.clone().unwrap_or(name.clone()));
                if let Some(short) = arg.short {
                    clap_arg = clap_arg.short(short);
                }
                if let Some(help) = &arg.help {
                    clap_arg = clap_arg.help(help);
                }
                if let Some(default) = &arg.default {
                    clap_arg = clap_arg.default_value(default.clone());
                }
                if arg.required {
                    clap_arg = clap_arg.required(true);
                }
                if let Some(choices) = &arg.choices {
                    clap_arg = clap_arg
                        .value_parser(clap::builder::PossibleValuesParser::new(choices.iter()));
                }
                command = command.arg(clap_arg);
            }
            let help = command.render_help().to_string();
            (command, help)
        })
    }

    fn get_parser(&self) -> &clap::Command {
        &self.get_parser_and_help().0
    }

    fn get_parser_help(&self) -> &str {
        &self.get_parser_and_help().1
    }
}

impl IAction for ArgparseAction {
    fn get_name(&self) -> &str {
        &self.name
    }

    fn get_subname(&self) -> &str {
        &self.subname
    }

    fn get_help(&self) -> &str {
        self.help.get_or_init(|| {
            format!(
                "Parses arguments for action {}\n{}",
                self.config.action,
                self.get_parser_help()
            )
        })
    }

    fn run(&self, actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()> {
        let parser = self.get_parser();

        let match_info = if self.config.passthrough {
            parse_known_args(parser, args)
        } else {
            parser
                .clone()
                .try_get_matches_from(args)
                .map(|matches| (matches, vec![]))
        };

        match match_info {
            Ok((matches, rem)) => {
                // first we set all of the flags
                for (id, config) in &self.config.flags {
                    env::set_var(
                        config.var_name.as_ref().unwrap_or(id),
                        match matches.get_flag(id) {
                            true => "1",
                            false => "0",
                        },
                    );
                }

                // then all the args
                for (id, config) in &self.config.args {
                    if let Some(val) = matches.get_one::<String>(id) {
                        env::set_var(config.var_name.as_ref().unwrap_or(id), &val);
                    }
                }

                // then we run the action
                let action = match find_action(&self.config.action, actions) {
                    Ok(action) => action,
                    Err(err) => {
                        return Err(GobiError {
                            code: err.code,
                            msg: format!(
                                "Argparse could not find subaction: {}",
                                self.config.action
                            ),
                        })
                    }
                };
                return action.run(actions, rem);
            }
            Err(err) => {
                return Err(GobiError {
                    code: err.kind() as i32,
                    msg: format!(
                        "Error parsing arguments for action {}:{}",
                        self.config.action,
                        err.to_string()
                    ),
                });
            }
        }
    }
}

struct ArgparseRecipe {}

impl ArgparseRecipe {
    fn new() -> ArgparseRecipe {
        ArgparseRecipe {}
    }
}

impl IRecipe for ArgparseRecipe {
    fn get_name(&self) -> &str {
        "argparse"
    }

    fn get_help(&self) -> &str {
        "
Generates an argparse wrapper around a given subacton.

This recipe uses the following configuration options:

[argparse.<action name>.subaction] (required) : str
    name of subaction to call

[argparse.<action name>.passthrough] (optional) : bool
    if true, allows unknown arguments to be passed to subaction

Each argument is defined with the following options:
[argparse.<action name>.[args,flags].<arg name>] (required) : str
    name of argument / flag

[argparse.<action name>.[args,flags].<arg name>.short] (optional) : str
    short name of argument / flag
    
[argparse.<action name>.args.<arg name>.default] (optional) : str
    Default value for argument

[argparse.<action name>.[args,flags].<arg name>.help] (optional) : str
    Help text for argument / flag

[argparse.<action name>.args.<arg name>.required] (optional) : bool
    If true, argument is required

[argparse.<action name>.args.<arg name>.choices] (optional) : list[str]
    List of allowed choices

[argparse.<action name>.args.<arg name>.var_name] (optional) : str
    Name of environment variable to set, defautls to arg name (optional)

[argparse.<action name>.flags.<flag name>.set_false] (optional) : bool
    Changes the default behavior of the flag to set the value to false (optional)
"
    }

    fn create_actions(
        &self,
        _recipe_manager: &SharedRecipeManager,
        gobi_file: &GobiFile,
    ) -> GobiResult<Vec<Action>> {
        let config = match gobi_file.get_data().get("argparse") {
            Some(config) if config.is_table() => config.get_table().unwrap(),
            _ => return Ok(vec![]),
        };

        let (err, actions) = config
            .into_iter()
            .map(
                |(name, config)| match config.deserialize::<ArgparseConfig>() {
                    Ok(config) => {
                        Ok(ActionWrapper::new(ArgparseAction::new(&name, config)) as Action)
                    }
                    Err(e) => {
                        Err(GobiError {
                            code: 1,
                            msg: format!("Invalid argparse config for action '{}'\n{}", name, e.msg),
                        })
                    }
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
    recipe_manager.register_recipe(RecipeWrapper::new(ArgparseRecipe::new()));
}
