use gobi_lib::recipes::RecipeManager;

mod argparse;
mod help;
mod include;
mod list;
mod project_manager;
mod sequence;
mod shell;

#[no_mangle]
pub extern "C" fn gobi_register_recipes(recipe_manager: &mut RecipeManager) {
    argparse::register_recipes(recipe_manager);
    help::register_recipes(recipe_manager);
    include::register_recipes(recipe_manager);
    list::register_recipes(recipe_manager);
    project_manager::register_recipes(recipe_manager);
    sequence::register_recipes(recipe_manager);
    shell::register_recipes(recipe_manager);
}
