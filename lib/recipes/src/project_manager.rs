use std::{collections::HashMap, path::PathBuf};

use gobi_lib::{
    file::{GobiFile, GobiFileEntryTrait, GobiFileTrait},
    recipes::*,
    GobiError, GobiResult,
};

struct WhereAction {
    gobi_file_path: PathBuf,
}

impl WhereAction {
    fn new<T>(gobi_file_path: T) -> WhereAction
    where
        T: Into<PathBuf>,
    {
        WhereAction {
            gobi_file_path: gobi_file_path.into(),
        }
    }
}

impl IAction for WhereAction {
    fn get_name(&self) -> &str {
        "project-manager.where"
    }

    fn get_subname(&self) -> &str {
        "where"
    }

    fn get_help(&self) -> &str {
        r"
Get the path of a projects gobi file

Usage: gobi <project list...>? where <project name>"
    }

    fn run(&self, _actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()> {
        if args.len() == 0 {
            return Err(GobiError {
                code: 1,
                msg: "No project name provided".into(),
            });
        }

        let gobi_file = GobiFile::from_path(&self.gobi_file_path)?;

        let project_data = match gobi_file.get_data().get_nested(&["gobi", "projects"]) {
            Some(project_data) if project_data.is_table() => project_data,
            _ => {
                return Err(GobiError {
                    code: 1,
                    msg: "Expected 'projects' to be a table".into(),
                });
            }
        };

        let (err, paths) = args
            .iter()
            .map(
                |project_name| match project_data.get(project_name.as_str()) {
                    Some(path) if path.is_string() => Ok(path),
                    _ => Err(GobiError {
                        code: 1,
                        msg: format!("Project {} not found", project_name),
                    }),
                },
            )
            .fold(
                (GobiError::default(), vec![]),
                |(err, mut paths), path| match path {
                    Ok(path) => {
                        paths.push(path);
                        (err, paths)
                    }
                    Err(nerr) => (err.merge(nerr), paths),
                },
            );

        if err.code != 0 {
            return Err(err);
        }

        paths
            .iter()
            .for_each(|path| println!("{}", path.get_string().unwrap()));

        Ok(())
    }
}

struct RegisterAction {
    gobi_file_path: PathBuf,
}

impl RegisterAction {
    fn new<T>(gobi_file_path: T) -> RegisterAction
    where
        T: Into<PathBuf>,
    {
        RegisterAction {
            gobi_file_path: gobi_file_path.into(),
        }
    }
}

impl IAction for RegisterAction {
    fn get_name(&self) -> &str {
        "project-manager.register"
    }

    fn get_subname(&self) -> &str {
        "register"
    }

    fn get_help(&self) -> &str {
        r"
Register a project to a gobi file

Usage: gobi <project list...>? register <project name> <gobi file path>

project name: name of the action that will load the project

gobi file path: path to the gobi file for the project"
    }

    fn run(&self, _actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()> {
        if args.len() != 2 {
            return Err(GobiError {
                code: 1,
                msg: "Expected 2 arguments: <gobi_name> <gobi_file_path>".into(),
            });
        }

        let gobi_name = &args[0];
        let gobi_file_path = &args[1];
        let gobi_file_path = PathBuf::from(gobi_file_path);

        if !gobi_file_path.is_file() {
            return Err(GobiError {
                code: 1,
                msg: format!(
                    "File '{}' does not exist",
                    gobi_file_path.to_str().unwrap_or(&args[1])
                ),
            });
        }

        let mut gobi_file = GobiFile::from_path_format(&self.gobi_file_path)?;
        let gobi_data = gobi_file.get_data();

        let gobi_info = match gobi_data.get("gobi") {
            None => HashMap::default(),
            Some(v) if v.is_table() => v.get_table().unwrap(),
            _ => {
                return Err(GobiError {
                    code: 1,
                    msg: "Expected [gobi] to be a table".into(),
                });
            }
        };

        let projects = match gobi_info.get("projects") {
            None => HashMap::default(),
            Some(v) if v.is_table() => v.get_table().unwrap(),
            _ => {
                return Err(GobiError {
                    code: 1,
                    msg: "Expected [gobi.projects] to be a table".into(),
                });
            }
        };

        if projects.get(gobi_name).is_some() {
            return Err(GobiError {
                code: 1,
                msg: format!("Project {} is already registered", gobi_name),
            });
        }

        if let None = gobi_data.get("gobi") {
            gobi_file.set(&gobi_data, "gobi", HashMap::default())?;
        }
        let gobi_config = gobi_data.get("gobi").unwrap();
        if let None = gobi_config.get("projects") {
            gobi_file.set(&gobi_config, "projects", HashMap::default())?;
        }
        let projects_config = gobi_config.get("projects").unwrap();

        gobi_file.set(
            &projects_config,
            gobi_name.as_str(),
            gobi_file_path.to_str().unwrap().to_string(),
        )?;

        gobi_file.save()
    }
}

struct DeRegisterAction {
    gobi_file_path: PathBuf,
}

impl DeRegisterAction {
    fn new<T>(gobi_file_path: T) -> Self
    where
        T: Into<PathBuf>,
    {
        Self {
            gobi_file_path: gobi_file_path.into(),
        }
    }
}

impl IAction for DeRegisterAction {
    fn get_name(&self) -> &str {
        "project-manager.deregister"
    }

    fn get_subname(&self) -> &str {
        "deregister"
    }

    fn get_help(&self) -> &str {
        r"
Deregister a project from a gobi file

Usage: gobi <project list...>? deregister <project name>

project name: name of the action that will load the project"
    }

    fn run(&self, _actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()> {
        if args.len() != 1 {
            return Err(GobiError {
                code: 1,
                msg: "Expected 1 argument: <gobi_name>".into(),
            });
        }

        let gobi_name = &args[0];

        let mut gobi_file = GobiFile::from_path_format(&self.gobi_file_path)?;
        let gobi_data = gobi_file.get_data();

        let gobi_info = match gobi_data.get("gobi") {
            None => HashMap::default(),
            Some(v) if v.is_table() => v.get_table().unwrap(),
            _ => {
                return Err(GobiError {
                    code: 1,
                    msg: "Expected [gobi] to be a table".into(),
                });
            }
        };

        let projects = match gobi_info.get("projects") {
            None => HashMap::default(),
            Some(v) if v.is_table() => v.get_table().unwrap(),
            _ => {
                return Err(GobiError {
                    code: 1,
                    msg: "Expected [gobi.projects] to be a table".into(),
                });
            }
        };

        if projects.get(gobi_name).is_none() {
            return Err(GobiError {
                code: 1,
                msg: format!("Project {} is not registered", gobi_name),
            });
        }

        gobi_file.drop(
            &gobi_data.get("gobi").unwrap().get("projects").unwrap(),
            gobi_name.as_str(),
        )?;

        gobi_file.save()
    }
}

struct PruneAction {
    gobi_file_path: PathBuf,
}

impl PruneAction {
    fn new<T>(gobi_file_path: T) -> Self
    where
        T: Into<PathBuf>,
    {
        Self {
            gobi_file_path: gobi_file_path.into(),
        }
    }
}

impl IAction for PruneAction {
    fn get_name(&self) -> &str {
        "project-manager.prune"
    }

    fn get_subname(&self) -> &str {
        "prune"
    }

    fn get_help(&self) -> &str {
        r"
Prune projects from the current gobi file that no longer exist

Usage: gobi <project list...>? prune [-y]

-y: skip confirmation prompt
"
    }

    fn run(&self, _actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()> {
        let mut gobi_file = GobiFile::from_path_format(&self.gobi_file_path)?;
        let gobi_data = gobi_file.get_data();

        let gobi_info = match gobi_data.get("gobi") {
            None => HashMap::default(),
            Some(v) if v.is_table() => v.get_table().unwrap(),
            _ => {
                return Err(GobiError {
                    code: 1,
                    msg: "Expected [gobi] to be a table".into(),
                });
            }
        };

        let projects = match gobi_info.get("projects") {
            None => HashMap::default(),
            Some(v) if v.is_table() => v.get_table().unwrap(),
            _ => {
                return Err(GobiError {
                    code: 1,
                    msg: "Expected [gobi.projects] to be a table".into(),
                });
            }
        };

        let prune_list: Vec<String> = projects
            .into_iter()
            .filter_map(|(gobi_file, gobi_file_path)| {
                match gobi_file_path {
                    gobi_file_path if gobi_file_path.is_string() => {
                        let gobi_file_path: PathBuf = gobi_file_path.get_string().unwrap().into();

                        if gobi_file_path.is_file() {
                            None
                        } else {
                            Some(gobi_file)
                        }
                    }
                    // Todo we should warn about this
                    _ => None,
                }
            })
            .collect();

        if prune_list.len() == 0 {
            return Ok(());
        }

        let skip_check = args.len() > 0 && args[0] == "-y";

        if !skip_check {
            println!("About to remove:")
        } else {
            println!("Removed:");
        }

        prune_list
            .iter()
            .for_each(|gobi_file| println!("{}", gobi_file));

        if !skip_check {
            println!("Continue [y/n]?");
            let mut buf: String = "".into();
            let _ = std::io::stdin().read_line(&mut buf);
            if buf.trim() != "y" {
                return Err(GobiError {
                    code: 1,
                    msg: "Aborting...".into(),
                });
            }
        }

        prune_list.into_iter().for_each(|gobi_name| {
            let _ = gobi_file.drop(
                &gobi_data.get("gobi").unwrap().get("projects").unwrap(),
                gobi_name.as_str(),
            );
        });

        if !skip_check {
            println!("Done!");
        }

        gobi_file.save()
    }
}

struct ProjectManagerRecipe {}

impl ProjectManagerRecipe {
    fn new() -> ProjectManagerRecipe {
        ProjectManagerRecipe {}
    }
}

impl IRecipe for ProjectManagerRecipe {
    fn get_name(&self) -> &str {
        "project-manager"
    }

    fn get_help(&self) -> &str {
        r#"
Creates the (de)register, where, and prune actions to manage projects
"#
    }

    fn create_actions(
        &self,
        _recipe_manager: &SharedRecipeManager,
        gobi_file: &GobiFile,
    ) -> GobiResult<Vec<Action>> {
        Ok(vec![
            ActionWrapper::new(WhereAction::new(gobi_file.path())) as Action,
            ActionWrapper::new(RegisterAction::new(gobi_file.path())) as Action,
            ActionWrapper::new(DeRegisterAction::new(gobi_file.path())) as Action,
            ActionWrapper::new(PruneAction::new(gobi_file.path())) as Action,
        ])
    }
}

pub fn register_recipes(recipe_manager: &mut RecipeManager) {
    recipe_manager.register_recipe(RecipeWrapper::new(ProjectManagerRecipe::new()));
}
