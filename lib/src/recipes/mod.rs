use sharedlib::{Func, Lib, Symbol};
use std::collections::HashMap;
use std::fmt::{Debug, Formatter};
use std::path::Path;
use std::rc::Rc;

use crate::{file::GobiFile, GobiError, GobiResult};

pub mod gobi;
pub mod utils;
pub use toml;
pub use toml_edit;

pub type ActionWrapper<T> = Rc<T>;
pub type Action = ActionWrapper<dyn IAction>;

pub trait IAction {
    fn get_name(&self) -> &str;
    fn get_subname(&self) -> &str;
    fn get_help(&self) -> &str {
        "No help available"
    }
    fn has_priority(&self) -> bool {
        true
    }
    fn run(&self, actions: &Vec<Action>, args: Vec<String>) -> GobiResult<()>;
    fn completion(&self, _actions: &Vec<Action>, _args: Vec<String>) -> GobiResult<Vec<String>> {
        Ok(vec![])
    }
}

pub fn find_action(query: &str, actions: &Vec<Action>) -> GobiResult<Action> {
    let (subname_match, subname_priority_match, name_match): (
        GobiResult<Option<Action>>,
        GobiResult<Option<Action>>,
        GobiResult<Option<Action>>,
    ) = actions
        .iter()
        .map(|action| {
            (
                action.get_subname() == query,
                action.get_subname() == query && action.has_priority(),
                action.get_name() == query,
                action,
            )
        })
        .fold(
            (Ok(None), Ok(None), Ok(None)),
            |(subname, subname_priority, name),
             (is_subname, is_subname_priority, is_name, action)| {
                let subname = match subname {
                    Ok(None) if is_subname => Ok(Some(action.clone())),
                    Ok(_) if is_subname => Err(GobiError {
                        code: 1,
                        msg: format!("Action {} is ambiguous", query),
                    }),
                    e => e,
                };
                let subname_priority = match subname_priority {
                    Ok(None) if is_subname_priority => Ok(Some(action.clone())),
                    Ok(_) if is_subname_priority => Err(GobiError {
                        code: 1,
                        msg: format!("Action {} is ambiguous", query),
                    }),
                    e => e,
                };
                let name = match name {
                    Ok(None) if is_name => Ok(Some(action.clone())),
                    Ok(_) if is_name => Err(GobiError {
                        code: 1,
                        msg: format!("Action {} is ambiguous", query),
                    }),
                    e => e,
                };
                (subname, subname_priority, name)
            },
        );

    match (subname_match, subname_priority_match, name_match) {
        (Ok(Some(action)), _, _) => Ok(action),
        (_, Ok(Some(action)), _) => Ok(action),
        (_, _, Ok(Some(action))) => Ok(action),
        (Err(e), _, _) => Err(e),
        (_, Err(e), _) => Err(e),
        (_, _, Err(e)) => Err(e),
        _ => Err(GobiError {
            code: 1,
            msg: format!("Action {} not found", query),
        }),
    }
}

pub fn get_minimal_names(actions: &Vec<Action>) -> Vec<(Action, String)> {
    let mut minimal_name: HashMap<String, Vec<Action>> = HashMap::new();
    for action in actions {
        if minimal_name.contains_key(action.get_subname()) {
            minimal_name
                .get_mut(action.get_subname())
                .unwrap()
                .push(action.clone());
        } else {
            minimal_name.insert(action.get_subname().to_string(), vec![action.clone()]);
        }
    }
    let mut minimal_name_keys: Vec<&String> = minimal_name.keys().collect();
    minimal_name_keys.sort_by(|a, b| a.cmp(&b));
    minimal_name_keys
        .iter_mut()
        .map(|subname| {
            let mut actions = minimal_name.get(*subname).unwrap().clone();
            let mut priority_actions: Vec<&Action> = actions
                .iter()
                .filter(|&action| action.has_priority())
                .collect();
            if priority_actions.len() == 1 {
                vec![(priority_actions[0].clone(), subname.to_string())]
            } else if priority_actions.len() > 1 {
                priority_actions.sort_by(|a, b| a.get_name().cmp(&b.get_name()));
                priority_actions
                    .iter()
                    .map(|&action| (action.clone(), action.get_name().into()))
                    .collect()
            } else if actions.len() == 1 {
                vec![(actions[0].clone(), subname.to_string())]
            } else {
                actions.sort_by(|a, b| a.get_name().cmp(&b.get_name()));
                actions
                    .iter()
                    .map(|action| (action.clone(), action.get_name().to_string()))
                    .collect()
            }
        })
        .flatten()
        .collect()
}

impl Debug for dyn IAction {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        write!(f, "<Action: {} [{}]>", self.get_name(), self.has_priority())
    }
}

// spub type ActionIterator = Iterator<Item = Action>;
pub trait IRecipe {
    fn get_name(&self) -> &str;
    fn get_help(&self) -> &str;
    fn create_actions(
        &self,
        recipe_manager: &SharedRecipeManager,
        gobi_file: &GobiFile,
    ) -> GobiResult<Vec<Action>>;
}
pub type RecipeWrapper<T> = Rc<T>;
pub type Recipe = RecipeWrapper<dyn IRecipe>;

// impl Debug for dyn IRecipe {
//     fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
//         write!(f, "<Recipe: {}>", self.get_name())
//     }
// }

pub struct RecipeManager {
    known_recipes: HashMap<String, Recipe>,
    libs: Vec<Lib>,
}
pub type SharedRecipeManager = Rc<RecipeManager>;

impl RecipeManager {
    pub fn new() -> RecipeManager {
        RecipeManager {
            known_recipes: HashMap::new(),
            libs: Vec::new(),
        }
    }

    pub fn register_recipe(&mut self, recipe: Recipe) {
        self.known_recipes
            .insert(recipe.get_name().to_string(), recipe);
    }

    pub fn register_recipes_from_so(&mut self, path: &Path) {
        // load recipes from shared object which will have
        // a function called register_recipes with no mangling
        unsafe {
            let lib = Lib::new(&path.to_str().unwrap()).unwrap();
            let register_fn: Func<extern "C" fn(&mut RecipeManager)> =
                lib.find_func("gobi_register_recipes").unwrap();
            register_fn.get()(self);
            self.libs.push(lib);
        }
    }

    pub fn get_recipe(&self, name: &str) -> Option<Recipe> {
        self.known_recipes.get(name).cloned()
    }

    pub fn recipes(&self) -> std::collections::hash_map::Values<String, Recipe> {
        self.known_recipes.values()
    }

    pub fn create_actions<'a>(
        &self,
        recipe_manager: &SharedRecipeManager,
        gobi_file: &GobiFile,
    ) -> GobiResult<Vec<Action>> {
        let (err, actions) = self
            .known_recipes
            .iter()
            .map(|(_name, recipe)| recipe.create_actions(recipe_manager, gobi_file))
            .fold(
                (GobiError::default(), Vec::new()),
                |(err, mut actions), result| match result {
                    Ok(new_actions) => {
                        actions.extend(new_actions);
                        (err, actions)
                    }
                    Err(e) => (err.merge(e), actions),
                },
            );

        if err.code != 0 {
            return Err(err);
        }

        Ok(actions)
    }
}
