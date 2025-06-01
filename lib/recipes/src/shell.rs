use serde::Deserialize;
use std::collections::HashMap;
use std::env;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::rc::Rc;
use tempfile::{Builder, NamedTempFile};

use gobi_lib::{
    file::{GobiFile, GobiFileEntryTrait, GobiFileTrait},
    recipes::*,
    GobiError, GobiResult,
    render_template,
};

#[derive(Deserialize, Default)]
struct ShellConfig {
    shell: Option<String>,
    extension: Option<String>,
    params: Option<Vec<String>>,
    env: Option<HashMap<String, String>>,
    #[serde(rename = "eval-env")]
    eval_env: Option<HashMap<String, String>>,
    cwd: Option<String>,
    help: Option<String>,
    priority: Option<bool>,
    command: Option<String>,
    completion: Option<String>,
}

#[derive(Debug)]
struct CompleteShellConfig {
    shell: String,
    extension: String,
    params: Vec<String>,
    env: HashMap<String, String>,
    eval_env: HashMap<String, String>,
    cwd: String,
    command: String,
    completion: Option<String>,
}

macro_rules! val_or_default {
    ($val: expr, $default: expr, $expr: expr) => {
        $val.clone().unwrap_or($default.clone().unwrap_or($expr))
    };
}

fn which(command: &str) -> Option<PathBuf> {
    // if path exists alone, just return it
    if Path::new(command).is_file() {
        Some(PathBuf::from(command))
    } else {
        env::var_os("PATH").and_then(|paths| {
            env::split_paths(&paths).find_map(|path| {
                let full_path = path.join(command);
                // todo, check file is executable
                if full_path.is_file() {
                    Some(full_path)
                } else {
                    None
                }
            })
        })
    }
}

impl CompleteShellConfig {
    fn new(config: &ShellConfig, default: &ShellConfig) -> Self {
        Self {
            shell: val_or_default!(config.shell, default.shell, "/bin/sh".to_string()),
            extension: val_or_default!(config.extension, default.extension, "".to_string()),
            params: val_or_default!(config.params, default.params, vec![]),
            env: val_or_default!(config.env, default.env, HashMap::new()),
            eval_env: val_or_default!(config.eval_env, default.eval_env, HashMap::new()),
            cwd: val_or_default!(
                config.cwd,
                default.cwd,
                env::current_dir().unwrap().display().to_string()
            ),
            command: config.command.clone().unwrap(),
            completion: config.completion.clone(),
        }
    }
}

pub struct ShellAction {
    name: String,
    subname: String,
    priority: bool,

    default: Rc<ShellConfig>,
    config: ShellConfig,
    config_file: PathBuf,
}

fn setup_command(
    config: &CompleteShellConfig,
    shell_path: &Path,
    command: &str,
    dir: &Path,
    env: &HashMap<String, String>,
) -> (NamedTempFile, Command) {
    // make a temp file
    let mut file = Builder::new()
        .prefix("gobi")
        .suffix(&config.extension)
        .tempfile()
        .unwrap();

    // write command to file
    file.write_all(command.as_bytes()).unwrap();
    file.flush().unwrap();

    // run command
    let mut command = Command::new(&shell_path);
    command
        .args(config.params.iter())
        .arg(file.path())
        .current_dir(dir)
        .env_clear()
        .envs(env.iter());
    (file, command)
}

impl ShellAction {
    fn new<P: Into<PathBuf>>(
        subname: &str,
        default: Rc<ShellConfig>,
        config: ShellConfig,
        config_file: P,
    ) -> Self {
        ShellAction {
            name: format!("shell.{}", subname),
            subname: subname.to_string(),
            priority: config.priority.unwrap_or(true),
            default,
            config,
            config_file: config_file.into(),
        }
    }

    fn setup_env(
        &self,
        config: &CompleteShellConfig,
    ) -> GobiResult<(PathBuf, PathBuf, HashMap<String, String>)> {
        // get shell executable
        let shell_path = match which(&config.shell) {
            Some(path) => path,
            None => {
                return Err(GobiError {
                    code: 1,
                    msg: format!("Shell '{}' not found", config.shell),
                })
            }
        };

        // create a copy of the env
        let mut env = env::vars().collect::<HashMap<_, _>>();

        // todo add eval-env / env
        // for each eval env we run the value as a command
        for (key, value) in &config.eval_env {
            let (_tmp_file, value) = {
                let (tmp_file, mut cmd) = setup_command(
                    config,
                    &shell_path,
                    value,
                    &self.config_file.parent().unwrap(),
                    &env,
                );
                match cmd.output() {
                    Ok(output) => {
                        if !output.status.success() {
                            return Err(GobiError {
                                code: output.status.code().unwrap_or(1),
                                msg: format!(
                                    "Eval-env command for '{}' failed with msg: '{}'",
                                    key,
                                    String::from_utf8_lossy(&output.stderr)
                                ),
                            });
                        }
                        (
                            tmp_file,
                            String::from_utf8_lossy(&output.stdout).trim().to_string(),
                        )
                    }
                    Err(err) => {
                        return Err(GobiError {
                            code: 1,
                            msg: format!(
                                "Error starting up command for eval-env var '{}': {}",
                                key, err
                            ),
                        });
                    }
                }
            };
            env.insert(key.to_string(), value);
        }

        // setup env
        for (key, value) in &config.env {
            // templates with env vars
            let value = render_template(value, &env, false)?;
            env.insert(key.to_string(), value.to_string());
        }

        // check cwd
        let cwd = render_template(&config.cwd, &env, false)?;
        let cwd = Path::new(cwd.as_str());
        if !cwd.is_dir() {
            return Err(GobiError {
                code: 1,
                msg: format!("Cwd '{}' does not exist", cwd.display()),
            });
        }

        Ok((shell_path, cwd.to_path_buf(), env))
    }
}

impl IAction for ShellAction {
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
        match (&self.config.help, &self.default.help) {
            (Some(help), _) => help,
            (_, Some(help)) => help,
            _ => "This shell action does not have a help message",
        }
    }

    fn run(&self, _actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()> {
        let config = CompleteShellConfig::new(&self.config, &self.default);

        let (shell_path, cwd, env) = self.setup_env(&config)?;

        let command = render_template(&config.command, &env, false)?;
        let (_tmp_file, mut command) = setup_command(&config, &shell_path, &command, &cwd, &env);
        for arg in args {
            command.arg(arg);
        }

        match command.status() {
            Ok(status) if status.success() => Ok(()),
            Ok(status) => Err(GobiError {
                code: status.code().unwrap_or(1),
                msg: "Command failed".to_string(),
            }),
            Err(err) => Err(GobiError {
                code: 1,
                msg: format!("Error starting up command: {}", err),
            }),
        }
    }

    fn completion(&self, _actions: &Vec<Action>, args: Vec<String>) -> GobiResult<Vec<String>> {
        let config = CompleteShellConfig::new(&self.config, &self.default);

        let (shell_path, cwd, env) = self.setup_env(&config)?;

        match &config.completion {
            Some(completion) => {
                let command = render_template(completion, &env, false)?;
                let (_tmp_file, mut command) =
                    setup_command(&config, &shell_path, &command, &cwd, &env);
                for arg in args {
                    command.arg(arg);
                }
                match command.output() {
                    Ok(output) if output.status.success() => {
                        let output_str = String::from_utf8_lossy(&output.stdout);
                        let completions: Vec<String> = output_str
                            .lines()
                            .map(|line| line.trim().to_string())
                            .filter(|line| !line.is_empty())
                            .collect();
                        Ok(completions)
                    }
                    Ok(output) => Err(GobiError {
                        code: output.status.code().unwrap_or(1),
                        msg: format!(
                            "Completion command failed with msg: '{}'",
                            String::from_utf8_lossy(&output.stderr)
                        ),
                    }),
                    Err(err) => Err(GobiError {
                        code: 1,
                        msg: format!("Error starting up completion command: {}", err),
                    }),
                }
            }
            None => Ok(cwd
                .read_dir()
                .map_err(|e| GobiError {
                    code: 1,
                    msg: format!("Error reading directory '{}': {}", cwd.display(), e),
                })?
                .filter_map(Result::ok)
                .map(|entry| entry.file_name().into_string().unwrap_or_default())
                .collect()),
        }
    }
}

struct ShellRecipe {}

impl ShellRecipe {
    fn new() -> ShellRecipe {
        ShellRecipe {}
    }
}

impl IRecipe for ShellRecipe {
    fn get_name(&self) -> &str {
        "shell"
    }

    fn get_help(&self) -> &str {
        "Generate shell actions:

Shell actions run a shell command by creating a temporary with the 'command' parameter, and running '[shell] [params] [command file] [args]'. Where shell, params, and command are specified per action, and args, are any arguments passed through the command line.

This recipe uses the following configuration options:

[shell.<action name>.command] (required) : str
    command to run

[shell.<action name>.shell] (optional) : str
    shell to use, defaults to /bin/sh

[shell.<action name>.extension] (optional) : str
    extension to set for the command file, defaults to empty string (mostly useful for windows)

[shell.<action name>.params] (optional) : list[str]
    list of params to pass to shell, defaults to []

[shell.<action name>.env] (optional) : dict[str, str]
    dict of env variables to set, defaults to {}, values are processed as if they are string.Template objects

[shell.<action name>.eval-env] (optional) : dict[str, str]
    dict of env variables to set, defaults to {}, values are run as shell commands from the directory of the gobi file. These are set before the normal env variables.

[shell.<action name>.cwd] (optional) : str
    directory to run the command in, defaults to the current working directory

[shell.<action name>.help] (optional) : str
    help menu entry for the action created for a file

The action name 'gobi' is reserved to override default shell config for all actions in the project. 'command' cannot provide defaults."
    }

    fn create_actions(
        &self,
        _recipe_manager: &SharedRecipeManager,
        gobi_file: &GobiFile,
    ) -> GobiResult<Vec<Action>> {
        let mut config = match gobi_file.get_data().get("shell") {
            Some(config) if config.is_table() => config.get_table().unwrap(),
            _ => return Ok(vec![]),
        };

        let default_config = Rc::new(match config.remove("gobi") {
            Some(config) if config.is_table() => match config.deserialize::<ShellConfig>() {
                Ok(config) => config,
                _ => ShellConfig::default(),
            },
            _ => ShellConfig::default(),
        });

        let (err, actions) = config
            .into_iter()
            .filter_map(|(name, config)| {
                if name == "gobi" {
                    return None;
                }
                Some(match config.deserialize::<ShellConfig>() {
                    Ok(config) if config.command.is_some() => Ok(ActionWrapper::new(
                        ShellAction::new(&name, default_config.clone(), config, gobi_file.path()),
                    ) as Action),
                    _ => Err(GobiError {
                        code: 1,
                        msg: format!("Invalid shell config for action '{}'", name),
                    }),
                })
            })
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
    recipe_manager.register_recipe(RecipeWrapper::new(ShellRecipe::new()));
}
